"""Hive skill — email & calendar automation via Hive's FastAPI.

Calls Hive's endpoints (/run, /runs/{id}/approve, /runs/{id}/reject)
and maps Hive's HITL approval onto Aether's high-risk approval channel.

Usage:
- "check my inbox" / "summarize my emails"
- "draft a reply to John about the project"
- "schedule a meeting with Sarah tomorrow at 3pm"
- "what's on my calendar today"
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import structlog

from assistant.skills.base import SkillContext, SkillResult

log = structlog.get_logger()

HIVE_URL = os.environ.get("AETHER_HIVE_URL", "http://127.0.0.1:8000")
HIVE_DIR = os.environ.get("AETHER_HIVE_DIR", str(Path(__file__).resolve().parents[5] / "hivechild"))

# Keywords that trigger this skill
_EMAIL_KEYWORDS = (
    "email", "inbox", "mail", "reply", "draft", "send email",
    "summarize email", "check email", "unread",
)
_CALENDAR_KEYWORDS = (
    "calendar", "schedule", "meeting", "event", "appointment",
    "what's on my", "what is on my", "today's schedule",
    "book a meeting", "set up a meeting",
)


def _hive_available() -> bool:
    """Quick health check — is Hive's API running?"""
    try:
        req = urllib.request.Request(f"{HIVE_URL}/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


_hive_proc: subprocess.Popen | None = None


def _ensure_hive_running() -> bool:
    """Start Hive's API server if not already running. Returns True when ready."""
    global _hive_proc
    if _hive_available():
        return True

    venv_python = str(Path(HIVE_DIR) / ".venv" / "Scripts" / "python.exe")
    if not Path(venv_python).exists():
        venv_python = sys.executable  # fallback to current python

    log.info("hive_auto_starting", hive_dir=HIVE_DIR, python=venv_python)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(HIVE_DIR) / "src") + os.pathsep + env.get("PYTHONPATH", "")
    try:
        _hive_proc = subprocess.Popen(
            [venv_python, "-m", "uvicorn", "hive.api.app:app",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=HIVE_DIR,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except OSError as e:
        log.error("hive_auto_start_failed", error=str(e))
        return False

    # Wait for Hive to be ready (up to 30 seconds)
    for _ in range(60):
        time.sleep(0.5)
        if _hive_available():
            log.info("hive_auto_started")
            return True
        if _hive_proc.poll() is not None:
            log.error("hive_auto_start_died", returncode=_hive_proc.returncode)
            return False

    log.error("hive_auto_start_timeout")
    return False


def _hive_run(intent: str, thread_id: str | None = None) -> dict | None:
    """POST /run — start a Hive workflow. Returns snapshot dict or None."""
    payload = {"intent": intent}
    if thread_id:
        payload["thread_id"] = thread_id
    try:
        req = urllib.request.Request(
            f"{HIVE_URL}/run",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        log.warning("hive_run_failed", error=str(e))
        return None


def _hive_approve(thread_id: str) -> dict | None:
    """POST /runs/{thread_id}/approve — approve pending Hive action."""
    try:
        req = urllib.request.Request(
            f"{HIVE_URL}/runs/{thread_id}/approve",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        log.warning("hive_approve_failed", error=str(e))
        return None


def _hive_reject(thread_id: str) -> dict | None:
    """POST /runs/{thread_id}/reject — reject pending Hive action."""
    try:
        req = urllib.request.Request(
            f"{HIVE_URL}/runs/{thread_id}/reject",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        log.warning("hive_reject_failed", error=str(e))
        return None


def _format_snapshot(snap: dict) -> str:
    """Convert Hive's state dict into a human-readable summary."""
    state = snap.get("state", {})
    parts = []

    # Q&A answer (for inbox summaries, calendar queries)
    qa = state.get("qa_answer")
    if qa:
        parts.append(qa)

    # Email drafts
    drafts = state.get("email_drafts", [])
    for i, d in enumerate(drafts, 1):
        to = ", ".join(d.get("to", []))
        subject = d.get("subject", "(no subject)")
        body = d.get("body", "")
        tone = d.get("tone", "")
        rationale = d.get("rationale", "")
        preview = body[:200] + "..." if len(body) > 200 else body
        parts.append(
            f"Draft {i}: To: {to} | Subject: {subject}\n"
            f"  Tone: {tone}\n"
            f"  Body: {preview}"
        )
        if rationale:
            parts.append(f"  Rationale: {rationale}")

    # Event proposals
    events = state.get("event_proposals", [])
    for i, e in enumerate(events, 1):
        title = e.get("title", "(untitled)")
        start = e.get("start", "")
        end = e.get("end", "")
        attendees = ", ".join(e.get("attendees", []))
        rationale = e.get("rationale", "")
        parts.append(
            f"Event {i}: {title}\n"
            f"  When: {start} → {end}\n"
            f"  Attendees: {attendees}"
        )
        if rationale:
            parts.append(f"  Rationale: {rationale}")

    # Critic feedback
    critic = state.get("critic_feedback")
    if critic and not state.get("critic_passed", False):
        parts.append(f"Critic feedback: {critic}")

    # Errors
    errors = state.get("errors", [])
    if errors:
        parts.append(f"Errors: {'; '.join(errors)}")

    if not parts:
        # Fallback: show status
        status = state.get("status", "unknown")
        parts.append(f"Hive status: {status}")

    return "\n".join(parts)


class HiveSkill:
    """Email & calendar automation via Hive's FastAPI."""

    name = "hive"
    description = (
        "Email and calendar automation: check inbox, summarize emails, "
        "draft replies, schedule meetings, check calendar"
    )
    risk_default = "high"  # emails and calendar are high-risk (external actions)

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower().strip()
        if any(k in text for k in _EMAIL_KEYWORDS):
            return 0.9
        if any(k in text for k in _CALENDAR_KEYWORDS):
            return 0.9
        # Check entities from LLM
        if context.entities.get("skill_hint") == "hive":
            return 0.7
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        # Auto-start Hive if not running
        if not _ensure_hive_running():
            return SkillResult(
                status="failed",
                speak="I couldn't start the email service. Please check that Hive is installed correctly.",
                error="Hive API auto-start failed",
            )

        intent = context.user_intent

        # Start the Hive workflow
        thread_id = context.session.get("hive_thread_id")
        snap = _hive_run(intent, thread_id=thread_id)
        if snap is None:
            return SkillResult(
                status="failed",
                speak="I couldn't reach Hive to process that request.",
                error="Hive /run failed",
            )

        # Save thread_id for follow-up commands
        new_thread_id = snap.get("thread_id")
        if new_thread_id:
            context.session["hive_thread_id"] = new_thread_id

        awaiting = snap.get("awaiting_approval", False)
        summary = _format_snapshot(snap)

        if awaiting:
            # Hive wants approval — map to Aether's approval flow
            # Build a preview for the approval dialog
            preview = self._build_preview(snap)
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview=preview,
                speak=f"Hive has prepared a draft. Here's what it wants to do: {preview}",
                output={"hive_snapshot": snap, "thread_id": new_thread_id},
            )

        # No approval needed — return the result directly
        return SkillResult(
            status="ok",
            speak=summary,
            output=summary,
        )

    def _build_preview(self, snap: dict) -> str:
        """Build a short preview for the approval dialog."""
        state = snap.get("state", {})
        drafts = state.get("email_drafts", [])
        events = state.get("event_proposals", [])

        if drafts:
            d = drafts[0]
            to = ", ".join(d.get("to", []))
            subject = d.get("subject", "(no subject)")
            body = d.get("body", "")
            preview = body[:150] + "..." if len(body) > 150 else body
            return f"Send email to {to}\nSubject: {subject}\nBody: {preview}"

        if events:
            e = events[0]
            title = e.get("title", "(untitled)")
            start = e.get("start", "")
            attendees = ", ".join(e.get("attendees", []))
            return f"Create calendar event: {title}\nWhen: {start}\nAttendees: {attendees}"

        return "Hive wants to perform an action that needs your approval."
