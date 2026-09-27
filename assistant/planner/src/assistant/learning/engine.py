"""Learning system — Tier 0 (rules) + Tier 1 (preference mining) + Tier 2 (macros).

Tier 0: User states a rule ("never touch D:/photos", "always approve notepad").
        Stored as preferences with source="user", hard=True.
        Enforced before every skill execution.

Tier 1: Nightly batch mining of approval/rejection patterns.
        Aggregates by (skill, context_signature) and detects:
        - approval_rate >= 0.9, n >= 5 -> auto-relax medium friction
        - rejection_rate >= 0.7, n >= 3 -> raise risk / always-ask
        - undo_rate >= 0.3 -> always-ask + never auto-relax

Tier 2: Weekly macro detection via frequent-sequence mining.
        Finds repeated action sequences (gap <= 60s, length 2-6, support >= 3
        in 14 days) and proposes them as named macros.

See docs/LEARNING.md for full spec.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import structlog

from assistant.memory.store import get_store

log = structlog.get_logger()

_DATA_DIR = Path(os.environ.get(
    "AETHER_DATA_DIR",
    str(Path(__file__).resolve().parents[2] / "data"),
)) / "learning"


class PreferenceStore:
    """SQLite store for user rules (Tier 0) and learned preferences (Tier 1)."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or _DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "preferences.sqlite"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id              TEXT PRIMARY KEY,
                    scope           TEXT NOT NULL,
                    rule            TEXT NOT NULL,
                    confidence      REAL NOT NULL DEFAULT 1.0,
                    source          TEXT NOT NULL DEFAULT 'user',
                    evidence_count  INTEGER NOT NULL DEFAULT 0,
                    hard            INTEGER NOT NULL DEFAULT 0,
                    created_at      INTEGER NOT NULL,
                    last_updated    INTEGER NOT NULL,
                    last_used       INTEGER
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scope ON preferences(scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON preferences(source)")

    def add_rule(
        self,
        scope: str,
        rule: str,
        hard: bool = True,
    ) -> str:
        """Add an explicit user rule (Tier 0). Returns preference ID."""
        import uuid

        pid = str(uuid.uuid4())
        now = int(time.time() * 1000)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO preferences (id, scope, rule, confidence, source, "
                "evidence_count, hard, created_at, last_updated) "
                "VALUES (?, ?, ?, 1.0, 'user', 0, ?, ?, ?)",
                (pid, scope, rule, 1 if hard else 0, now, now),
            )
        log.info("rule_added", scope=scope, rule=rule, hard=hard)

        # Also store in memory store for semantic retrieval
        get_store().write(
            type="preference",
            content=f"{scope}: {rule}",
            metadata={
                "scope": scope,
                "rule": rule,
                "source": "user",
                "hard": hard,
                "preference_id": pid,
            },
        )
        return pid

    def add_learned(
        self,
        scope: str,
        rule: str,
        confidence: float,
        evidence_count: int,
    ) -> str:
        """Add a learned preference (Tier 1). Returns preference ID."""
        import uuid

        pid = str(uuid.uuid4())
        now = int(time.time() * 1000)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO preferences (id, scope, rule, confidence, source, "
                "evidence_count, hard, created_at, last_updated) "
                "VALUES (?, ?, ?, ?, 'learned', ?, 0, ?, ?)",
                (pid, scope, rule, confidence, evidence_count, now, now),
            )
        log.info("learned_preference_added", scope=scope, rule=rule, conf=confidence)

        get_store().write(
            type="preference",
            content=f"{scope}: {rule}",
            metadata={
                "scope": scope,
                "rule": rule,
                "source": "learned",
                "confidence": confidence,
                "evidence_count": evidence_count,
                "preference_id": pid,
            },
        )
        return pid

    def get_rules_for_skill(self, skill_name: str) -> list[dict[str, Any]]:
        """Get all preferences that apply to a skill."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM preferences WHERE scope LIKE ? OR scope = 'global' "
                "ORDER BY hard DESC, confidence DESC",
                (f"%{skill_name}%",),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all(self) -> list[dict[str, Any]]:
        """Get all preferences."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM preferences ORDER BY hard DESC, last_updated DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def forget(self, pid: str) -> bool:
        """Delete a preference."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute("DELETE FROM preferences WHERE id = ?", (pid,))
            return cur.rowcount > 0

    def forget_all_learned(self) -> int:
        """Delete all learned preferences (Tier 1 wipe). Keeps user rules."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute("DELETE FROM preferences WHERE source = 'learned'")
            return cur.rowcount

    def update_confidence(self, pid: str, confidence: float, evidence_count: int) -> None:
        """Update a learned preference's confidence (with decay)."""
        now = int(time.time() * 1000)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE preferences SET confidence = ?, evidence_count = ?, "
                "last_updated = ? WHERE id = ?",
                (confidence, evidence_count, now, pid),
            )

    def mark_used(self, pid: str) -> None:
        """Mark a preference as used (for decay tracking)."""
        now = int(time.time() * 1000)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE preferences SET last_used = ? WHERE id = ?", (now, pid)
            )


class FeedbackCollector:
    """Collects signals from each turn for preference mining (Tier 1).

    Signals: intent -> skill + confidence, risk -> decision,
    clarification -> choice, undo events, corrections.
    """

    def __init__(self) -> None:
        self._signals: list[dict[str, Any]] = []

    def record(
        self,
        intent: str,
        skill: str,
        confidence: float,
        risk: str,
        decision: str,
        outcome: str = "",
        undo: bool = False,
    ) -> None:
        """Record a feedback signal."""
        signal = {
            "timestamp": int(time.time() * 1000),
            "intent": intent,
            "skill": skill,
            "confidence": confidence,
            "risk": risk,
            "decision": decision,
            "outcome": outcome,
            "undo": undo,
        }
        self._signals.append(signal)

        # Persist to memory store as action
        get_store().write(
            type="action",
            content=f"{skill}: {intent} -> {decision} ({risk})",
            metadata=signal,
        )

    def get_signals(self) -> list[dict[str, Any]]:
        return self._signals


class PreferenceMiner:
    """Tier 1 nightly preference mining (see docs/LEARNING.md §3)."""

    # Thresholds from the spec
    APPROVE_RATE_THRESHOLD = 0.9
    APPROVE_MIN_N = 5
    REJECT_RATE_THRESHOLD = 0.7
    REJECT_MIN_N = 3
    UNDO_RATE_THRESHOLD = 0.3

    def __init__(self, store: PreferenceStore) -> None:
        self.store = store

    def mine(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run preference mining on collected signals.

        Returns list of detected preferences to add.
        """
        # Group by (skill, risk)
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for s in signals:
            key = (s["skill"], s["risk"])
            groups[key].append(s)

        detected: list[dict[str, Any]] = []

        for (skill, risk), entries in groups.items():
            n = len(entries)
            approvals = sum(1 for e in entries if e["decision"] == "approve")
            rejections = sum(1 for e in entries if e["decision"] == "reject")
            undos = sum(1 for e in entries if e["undo"])

            approval_rate = approvals / n if n else 0
            rejection_rate = rejections / n if n else 0
            undo_rate = undos / n if n else 0

            scope = f"skill:{skill}"

            # Detect: high approval rate on medium risk -> auto-relax
            if (
                risk == "medium"
                and approval_rate >= self.APPROVE_RATE_THRESHOLD
                and n >= self.APPROVE_MIN_N
            ):
                detected.append({
                    "scope": scope,
                    "rule": f"Auto-approve {skill} actions (user approves {approval_rate:.0%} of the time)",
                    "confidence": approval_rate,
                    "evidence_count": n,
                    "type": "auto_approve",
                })

            # Detect: high rejection rate -> always ask
            if rejection_rate >= self.REJECT_RATE_THRESHOLD and n >= self.REJECT_MIN_N:
                detected.append({
                    "scope": scope,
                    "rule": f"Always ask before {skill} actions (user rejects {rejection_rate:.0%} of the time)",
                    "confidence": rejection_rate,
                    "evidence_count": n,
                    "type": "always_ask",
                })

            # Detect: high undo rate -> always ask + never auto-relax
            if undo_rate >= self.UNDO_RATE_THRESHOLD:
                detected.append({
                    "scope": scope,
                    "rule": f"Always ask before {skill} (high undo rate {undo_rate:.0%})",
                    "confidence": 1.0 - undo_rate,
                    "evidence_count": n,
                    "type": "always_ask",
                })

        # Store detected preferences
        for pref in detected:
            self.store.add_learned(
                scope=pref["scope"],
                rule=pref["rule"],
                confidence=pref["confidence"],
                evidence_count=pref["evidence_count"],
            )

        log.info("preference_mining_complete", detected=len(detected), signals=len(signals))
        return detected


class MacroStore:
    """SQLite store for detected and accepted macros (Tier 2)."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or _DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "macros.sqlite"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS macros (
                    id              TEXT PRIMARY KEY,
                    name            TEXT NOT NULL,
                    steps_json      TEXT NOT NULL,
                    trigger_phrases TEXT NOT NULL DEFAULT '',
                    uses            INTEGER NOT NULL DEFAULT 0,
                    created_at      INTEGER NOT NULL,
                    last_used       INTEGER,
                    accepted        INTEGER NOT NULL DEFAULT 0
                )
            """)

    def add_macro(
        self,
        name: str,
        steps: list[dict[str, Any]],
        trigger_phrases: list[str] | None = None,
        accepted: bool = False,
    ) -> str:
        import uuid

        mid = str(uuid.uuid4())
        now = int(time.time() * 1000)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO macros (id, name, steps_json, trigger_phrases, uses, "
                "created_at, accepted) VALUES (?, ?, ?, ?, 0, ?, ?)",
                (mid, name, json.dumps(steps),
                 json.dumps(trigger_phrases or []), now, 1 if accepted else 0),
            )
        log.info("macro_added", name=name, steps=len(steps))

        # Also store in memory for semantic retrieval
        get_store().write(
            type="macro",
            content=f"Macro '{name}': {' -> '.join(s.get('skill', '?') for s in steps)}",
            metadata={
                "name": name,
                "steps": steps,
                "trigger_phrases": trigger_phrases or [],
                "macro_id": mid,
                "accepted": accepted,
            },
        )
        return mid

    def accept_macro(self, mid: str) -> bool:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute(
                "UPDATE macros SET accepted = 1 WHERE id = ?", (mid,)
            )
            return cur.rowcount > 0

    def get_accepted_macros(self) -> list[dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM macros WHERE accepted = 1 ORDER BY last_used DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_proposed_macros(self) -> list[dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM macros WHERE accepted = 0 ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_used(self, mid: str) -> None:
        now = int(time.time() * 1000)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE macros SET uses = uses + 1, last_used = ? WHERE id = ?",
                (now, mid),
            )

    def forget(self, mid: str) -> bool:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute("DELETE FROM macros WHERE id = ?", (mid,))
            return cur.rowcount > 0

    def forget_all(self) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute("DELETE FROM macros")
            return cur.rowcount


class MacroDetector:
    """Tier 2 macro detection — frequent-sequence mining (see docs/LEARNING.md §4).

    Input:  session action logs (skill_id sequences with timestamps)
    Method: frequent-sequence mining with constraints:
            gap <= 60s between steps, length 2-6, support >= 3 occurrences / 14 days
    Output: candidate macro {steps, args_template, suggested trigger phrase}
    """

    MAX_GAP_S = 60.0
    MIN_LENGTH = 2
    MAX_LENGTH = 6
    MIN_SUPPORT = 3
    WINDOW_DAYS = 14

    def __init__(self, macro_store: MacroStore) -> None:
        self.store = macro_store

    def detect(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run macro detection on collected action signals.

        Returns list of proposed macros (not yet accepted by user).
        """
        if len(signals) < self.MIN_SUPPORT * self.MIN_LENGTH:
            return []

        # Sort signals by timestamp
        sorted_signals = sorted(signals, key=lambda s: s["timestamp"])

        # Build sessions: group signals into sessions where gap > MAX_GAP_S
        sessions: list[list[dict]] = []
        current: list[dict] = []
        prev_ts = 0

        for sig in sorted_signals:
            if current and (sig["timestamp"] - prev_ts) / 1000 > self.MAX_GAP_S:
                sessions.append(current)
                current = []
            current.append(sig)
            prev_ts = sig["timestamp"]
        if current:
            sessions.append(current)

        # Extract skill sequences from each session
        sequences: list[list[str]] = []
        for session in sessions:
            skills = [s["skill"] for s in session if s["decision"] in ("approve", "executed")]
            if len(skills) >= self.MIN_LENGTH:
                sequences.append(skills)

        # Mine frequent sequences using a simple approach:
        # enumerate all subsequences of length 2-6 and count occurrences
        candidate_counts: dict[tuple[str, ...], int] = defaultdict(int)

        for seq in sequences:
            seen_in_seq: set[tuple[str, ...]] = set()
            for length in range(self.MIN_LENGTH, min(self.MAX_LENGTH, len(seq)) + 1):
                for start in range(len(seq) - length + 1):
                    subseq = tuple(seq[start:start + length])
                    if subseq not in seen_in_seq:
                        seen_in_seq.add(subseq)
                        candidate_counts[subseq] += 1

        # Filter by minimum support
        frequent = [
            (seq, count) for seq, count in candidate_counts.items()
            if count >= self.MIN_SUPPORT
        ]
        frequent.sort(key=lambda x: (x[1], len(x[0])), reverse=True)

        # Remove sequences that are substrings of longer frequent sequences
        # (prefer longer macros)
        filtered: list[tuple[tuple[str, ...], int]] = []
        for seq, count in frequent:
            is_subseq = False
            for longer_seq, _ in filtered:
                if len(longer_seq) > len(seq):
                    # Check if seq is a contiguous substring of longer_seq
                    for i in range(len(longer_seq) - len(seq) + 1):
                        if longer_seq[i:i + len(seq)] == seq:
                            is_subseq = True
                            break
                    if is_subseq:
                        break
            if not is_subseq:
                filtered.append((seq, count))

        # Create macro proposals
        proposals: list[dict[str, Any]] = []
        for seq, count in filtered[:10]:  # top 10 proposals
            name = self._suggest_name(seq)
            steps = [{"skill": skill, "args_template": {}} for skill in seq]
            trigger = self._suggest_trigger(seq)

            mid = self.store.add_macro(
                name=name,
                steps=steps,
                trigger_phrases=[trigger],
                accepted=False,
            )
            proposals.append({
                "id": mid,
                "name": name,
                "steps": steps,
                "trigger_phrase": trigger,
                "support": count,
            })

        log.info("macro_detection_complete", proposals=len(proposals), sequences=len(sequences))
        return proposals

    @staticmethod
    def _suggest_name(seq: tuple[str, ...]) -> str:
        """Generate a human-friendly macro name from the skill sequence."""
        # Use first letters or skill keywords
        keywords: dict[str, str] = {
            "open_app": "Open",
            "type_text": "Type",
            "hive": "Email",
            "file_ops": "File",
            "math": "Math",
            "system_control": "System",
            "file_cleanup": "Cleanup",
            "web_search": "Search",
            "time_date": "Time",
            "notepad_solve": "Solve",
        }
        parts = [keywords.get(s, s.replace("_", " ").title()) for s in seq]
        return " -> ".join(parts)

    @staticmethod
    def _suggest_trigger(seq: tuple[str, ...]) -> str:
        """Generate a suggested trigger phrase for the macro."""
        if len(seq) == 2:
            return f"do {seq[0]} then {seq[1]}"
        return f"run {len(seq)}-step workflow"


# Singletons
_pref_store: PreferenceStore | None = None
_collector: FeedbackCollector | None = None
_miner: PreferenceMiner | None = None
_macro_store: MacroStore | None = None
_macro_detector: MacroDetector | None = None


def get_preferences() -> PreferenceStore:
    global _pref_store
    if _pref_store is None:
        _pref_store = PreferenceStore()
    return _pref_store


def get_collector() -> FeedbackCollector:
    global _collector
    if _collector is None:
        _collector = FeedbackCollector()
    return _collector


def get_miner() -> PreferenceMiner:
    global _miner
    if _miner is None:
        _miner = PreferenceMiner(get_preferences())
    return _miner


def get_macro_store() -> MacroStore:
    global _macro_store
    if _macro_store is None:
        _macro_store = MacroStore()
    return _macro_store


def get_macro_detector() -> MacroDetector:
    global _macro_detector
    if _macro_detector is None:
        _macro_detector = MacroDetector(get_macro_store())
    return _macro_detector
