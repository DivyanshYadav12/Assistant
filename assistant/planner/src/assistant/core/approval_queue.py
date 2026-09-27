"""Persistent approval queue — SQLite-backed, survives crashes/restarts.

When a skill returns needs_approval, the pending action is stored in SQLite.
If the process crashes or restarts before the user responds, the pending
approval is still there and can be resumed.

See docs/SAFETY.md §3 and docs/PRODUCTION.md §4.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

_DATA_DIR = Path(os.environ.get(
    "AETHER_DATA_DIR",
    str(Path(__file__).resolve().parents[2] / "data"),
)) / "approvals"

# Default timeout: 10 minutes (see SAFETY.md §3)
DEFAULT_TIMEOUT_S = 600


class ApprovalQueue:
    """SQLite-backed persistent approval queue.

    Stores pending approvals with their preview, risk level, and rollback plan.
    Supports timeout-based auto-expiry.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or _DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "approvals.sqlite"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_approvals (
                    id              TEXT PRIMARY KEY,
                    skill           TEXT NOT NULL,
                    intent          TEXT NOT NULL,
                    risk            TEXT NOT NULL,
                    preview         TEXT NOT NULL,
                    rollback_plan   TEXT,
                    context_json    TEXT,
                    created_at      INTEGER NOT NULL,
                    expires_at      INTEGER NOT NULL,
                    status          TEXT NOT NULL DEFAULT 'pending'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON pending_approvals(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON pending_approvals(expires_at)")

    def enqueue(
        self,
        skill: str,
        intent: str,
        risk: str,
        preview: str,
        rollback_plan: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> str:
        """Add a pending approval to the queue. Returns the approval ID."""
        aid = str(uuid.uuid4())
        now = int(time.time() * 1000)
        expires = now + timeout_s * 1000

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO pending_approvals "
                "(id, skill, intent, risk, preview, rollback_plan, context_json, "
                "created_at, expires_at, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
                (aid, skill, intent, risk, preview,
                 json.dumps(rollback_plan) if rollback_plan else None,
                 json.dumps(context) if context else None,
                 now, expires),
            )
        log.info("approval_enqueued", id=aid, skill=skill, risk=risk)
        return aid

    def resolve(self, aid: str, approved: bool) -> dict[str, Any] | None:
        """Resolve a pending approval. Returns the stored context if found.

        Args:
            aid: approval ID
            approved: True if approved, False if rejected

        Returns:
            The stored approval data (skill, intent, context, rollback_plan)
            if found and was pending, None otherwise.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM pending_approvals WHERE id = ? AND status = 'pending'",
                (aid,),
            ).fetchone()

            if row is None:
                return None

            # Check if expired
            now = int(time.time() * 1000)
            if now > row["expires_at"]:
                conn.execute(
                    "UPDATE pending_approvals SET status = 'expired' WHERE id = ?",
                    (aid,),
                )
                log.info("approval_expired", id=aid)
                return None

            status = "approved" if approved else "rejected"
            conn.execute(
                "UPDATE pending_approvals SET status = ? WHERE id = ?",
                (status, aid),
            )

        log.info("approval_resolved", id=aid, status=status)
        return {
            "id": row["id"],
            "skill": row["skill"],
            "intent": row["intent"],
            "risk": row["risk"],
            "preview": row["preview"],
            "rollback_plan": json.loads(row["rollback_plan"]) if row["rollback_plan"] else None,
            "context": json.loads(row["context_json"]) if row["context_json"] else None,
        }

    def get_pending(self) -> list[dict[str, Any]]:
        """Get all pending approvals (not yet resolved or expired)."""
        now = int(time.time() * 1000)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM pending_approvals WHERE status = 'pending' "
                "AND expires_at > ? ORDER BY created_at DESC",
                (now,),
            ).fetchall()
        return [dict(r) for r in rows]

    def expire_stale(self) -> int:
        """Mark expired approvals as expired. Returns count expired."""
        now = int(time.time() * 1000)
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute(
                "UPDATE pending_approvals SET status = 'expired' "
                "WHERE status = 'pending' AND expires_at <= ?",
                (now,),
            )
            count = cur.rowcount
        if count:
            log.info("approvals_expired", count=count)
        return count

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent resolved approvals for audit/debugging."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM pending_approvals WHERE status != 'pending' "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def count_pending(self) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM pending_approvals WHERE status = 'pending'"
            ).fetchone()
            return row[0]


# Singleton
_queue: ApprovalQueue | None = None


def get_queue() -> ApprovalQueue:
    global _queue
    if _queue is None:
        _queue = ApprovalQueue()
    return _queue
