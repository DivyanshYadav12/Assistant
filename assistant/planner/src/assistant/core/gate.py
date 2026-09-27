"""Safety Gate v1 (see docs/SAFETY.md).

Deterministic risk rules + voice approval channel. When approval is needed,
the gate speaks the preview, listens for a voice response ("yes"/"approve"
or "no"/"reject"), and falls back to a Windows dialog if voice fails.
`high` risk can never be auto-approved.
"""

from __future__ import annotations

import time

import structlog

from assistant.skills.base import RISK_ORDER, RiskLevel, Skill, SkillContext

log = structlog.get_logger()

_HIGH_PATTERNS = ("delete", "remove", "uninstall", "format", "send ", "email ",
                  "shutdown", "restart", "kill", "disable", "firewall", "registry")

# Words that count as approval / rejection
_APPROVE_WORDS = ("yes", "approve", "ok", "okay", "confirm", "go ahead", "do it", "sure", "yeah", "yep", "continue", "proceed")
_REJECT_WORDS = ("no", "reject", "cancel", "deny", "stop", "don't", "do not", "nope", "never", "abort")


def classify_risk(intent: str, skill: Skill) -> RiskLevel:
    """Deterministic rules; the skill's default is the floor, never lowered."""
    floor: RiskLevel = skill.risk_default
    text = intent.lower()
    if any(p in text for p in _HIGH_PATTERNS):
        return "high"
    return floor


def request_approval(preview: str, risk: RiskLevel) -> bool:
    """Voice-first approval flow with dialog fallback.

    1. Speaks the preview and asks "Do you approve?"
    2. Listens for a voice response (yes/no/approve/reject)
    3. Falls back to Windows Yes/No dialog if voice fails or is unclear
    """
    print(f"\n[APPROVAL REQUIRED — risk: {risk}]\n  {preview}")

    # Try voice approval first
    approved = _voice_approval(preview, risk)
    if approved is not None:
        log.info("approval_decision", preview=preview, risk=risk, approved=approved, channel="voice")
        return approved

    # Fall back to dialog
    approved = _dialog_approval(preview, risk)
    log.info("approval_decision", preview=preview, risk=risk, approved=approved, channel="dialog")
    return approved


def _voice_approval(preview: str, risk: RiskLevel) -> bool | None:
    """Try voice approval. Returns True/False if understood, None if failed."""
    try:
        from assistant.core.tts import speak
        from assistant.core.voice_input import capture_utterance

        # Speak the preview and prompt
        speak(f"Approval required. {preview}. Do you approve?")
        time.sleep(0.3)  # brief pause after TTS to avoid echo

        # Listen for response
        response = capture_utterance(timeout_s=6.0)
        log.info("voice_approval_response", text=response)

        if not response:
            speak("I didn't hear a response. Let me show a dialog instead.")
            return None

        # Check for approval words
        if any(w in response for w in _APPROVE_WORDS):
            speak("Approved.")
            return True
        if any(w in response for w in _REJECT_WORDS):
            speak("Cancelled.")
            return False

        # Unclear response
        speak(f"I heard '{response}', but I'm not sure if that's a yes or no. Let me show a dialog.")
        return None
    except Exception as e:
        log.warning("voice_approval_failed", error=str(e)[:100])
        return None


def _dialog_approval(preview: str, risk: RiskLevel) -> bool:
    """Windows Yes/No dialog fallback."""
    try:
        import ctypes

        MB_YESNO = 0x4
        MB_ICONWARNING = 0x30
        MB_TOPMOST = 0x40000
        IDYES = 6
        result = ctypes.windll.user32.MessageBoxW(
            0,
            f"{preview}\n\nRisk level: {risk}",
            "Aether — Approval required",
            MB_YESNO | MB_ICONWARNING | MB_TOPMOST,
        )
        return result == IDYES
    except Exception:  # noqa: BLE001 — non-Windows or headless fallback
        answer = input("  Approve? [y/N]: ").strip().lower()
        return answer in ("y", "yes")


def auto_approvable(risk: RiskLevel, session: dict) -> bool:
    """safe/low auto-execute; medium once per session; high never."""
    if RISK_ORDER[risk] <= RISK_ORDER["low"]:
        return True
    if risk == "medium" and session.get("medium_approved_this_session"):
        return True
    return False
