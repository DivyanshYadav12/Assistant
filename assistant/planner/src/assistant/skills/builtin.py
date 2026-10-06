"""Built-in skills for Phase 2: time/date, open app, file search.

Rule-based `can_handle` (LLM routing comes later). Each skill honors the
approval contract: mutating skills check context.session["approved"].
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
from pathlib import Path

from assistant.skills.base import Skill, SkillContext, SkillResult


class TimeSkill:
    name = "time_date"
    description = "Tell the current time and date"
    risk_default = "safe"

    _KEYWORDS = ("time", "date", "day", "today", "clock")

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        if any(k in text for k in ("what time", "the time", "time is it", "current time")):
            return 0.95
        if any(k in text for k in ("what day", "today's date", "the date", "date today")):
            return 0.95
        return 0.4 if any(k in text for k in self._KEYWORDS) else 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        now = dt.datetime.now()
        text = context.user_intent.lower()
        if "date" in text or "day" in text:
            speak = f"Today is {now.strftime('%A, %B %d, %Y')}."
        else:
            speak = f"It is {now.strftime('%I:%M %p').lstrip('0')}."
        return SkillResult(status="ok", output=now.isoformat(), speak=speak)


class OpenAppSkill:
    name = "open_app"
    description = "Open an application by name"
    risk_default = "low"  # reversible, harmless — auto-execute + audit log

    # App name -> command. Extend freely.
    _APPS: dict[str, str] = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "task manager": "taskmgr.exe",
        "cmd": "cmd.exe",
        "terminal": "wt.exe",
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "vs code": "code",
        "vscode": "code",
        "code": "code",
    }

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        if not any(v in text for v in ("open", "launch", "start", "run")):
            return 0.0
        return 0.9 if self._match_app(text) else 0.5

    def _match_app(self, text: str) -> str | None:
        for app in sorted(self._APPS, key=len, reverse=True):
            if app in text:
                return app
        return None

    def execute(self, context: SkillContext) -> SkillResult:
        app = self._match_app(context.user_intent.lower())
        if app is None and context.entities.get("app"):
            app = self._match_app(context.entities["app"].lower())
        if app is None:
            return SkillResult(
                status="clarify",
                clarification_question="Which application should I open?",
            )
        try:
            subprocess.Popen(self._APPS[app], shell=True)
            return SkillResult(status="ok", speak=f"Opening {app}.")
        except OSError as e:
            return SkillResult(status="failed", error=str(e), speak=f"I couldn't open {app}.")


class TypeTextSkill:
    """Write/type text into Notepad (opens it if needed) or the focused window."""

    name = "type_text"
    description = "Write or type text into Notepad or the active window (not code)"
    risk_default = "medium"  # writes into a visible app the user is watching

    _VERBS = ("write", "type", "note down", "take a note", "jot down")
    
    # Code-related triggers that should go to CodeGenerationSkill instead
    _CODE_TRIGGERS = ("program", "code", "function", "class", "algorithm", "logic",
                     "script", "syntax", "loop", "variable")

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        
        # If it has code triggers, let CodeGenerationSkill handle it
        if any(trigger in text for trigger in self._CODE_TRIGGERS):
            return 0.0
        
        if any(v in text for v in self._VERBS):
            return 0.92
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        payload = self._extract_payload(context.user_intent)
        if not payload and context.entities.get("content"):
            payload = context.entities["content"]
        if not payload:
            return SkillResult(
                status="clarify",
                clarification_question="What should I write?",
            )
        if not context.session.get("approved"):
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview=f'Type into Notepad: "{payload}"',
            )
        try:
            self._type_into_notepad(payload)
            return SkillResult(status="ok", speak=f"I've written that in Notepad.")
        except Exception as e:  # noqa: BLE001 — UI automation has many failure modes
            return SkillResult(status="failed", error=str(e), speak="I couldn't type that.")

    @staticmethod
    def _extract_payload(intent: str) -> str | None:
        """Take everything after the verb, minus target phrases like 'in notepad'."""
        import re

        text = intent.strip()
        m = re.search(r"(?:write|type|note down|jot down)\s+(.*)", text, re.IGNORECASE)
        if not m:
            return None
        payload = m.group(1)
        payload = re.sub(r"\b(in|into|on|to)\s+(the\s+)?notepad\b", "", payload, flags=re.IGNORECASE)
        payload = payload.strip(" .,")
        return payload or None

    @staticmethod
    def _type_into_notepad(payload: str) -> None:
        import time

        import pygetwindow as gw
        import pyautogui

        windows = gw.getWindowsWithTitle("Notepad")
        if windows:
            win = windows[0]
            win.activate()
        else:
            subprocess.Popen("notepad.exe", shell=True)
            time.sleep(1.2)  # give the window time to appear
            windows = gw.getWindowsWithTitle("Notepad")
            if windows:
                windows[0].activate()
        time.sleep(0.4)
        pyautogui.typewrite(payload, interval=0.02)


class FileSearchSkill:
    name = "file_search"
    description = "Find files by name under the user profile"
    risk_default = "safe"

    _KEYWORDS = ("find", "search", "locate", "where is")

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        if any(k in text for k in self._KEYWORDS) and "file" in text:
            return 0.9
        return 0.35 if any(k in text for k in self._KEYWORDS) else 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        term = self._extract_term(context.user_intent)
        if not term:
            return SkillResult(
                status="clarify",
                clarification_question="What file name should I search for?",
            )
        root = Path(os.environ.get("USERPROFILE", Path.home()))
        hits: list[str] = []
        skip = {".git", "node_modules", "__pycache__", ".venv", "AppData"}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip]
            for fn in filenames:
                if term.lower() in fn.lower():
                    hits.append(str(Path(dirpath) / fn))
                    if len(hits) >= 10:
                        break
            if len(hits) >= 10:
                break
        speak = (
            f"I found {len(hits)} file{'s' if len(hits) != 1 else ''} matching {term}."
            if hits
            else f"I couldn't find any files matching {term}."
        )
        return SkillResult(status="ok", output=hits, speak=speak)

    @staticmethod
    def _extract_term(intent: str) -> str | None:
        words = intent.lower().replace("?", "").split()
        stop = {"find", "search", "locate", "for", "a", "the", "file", "files",
                "named", "called", "me", "my", "where", "is", "please", "can", "you"}
        candidates = [w for w in words if w not in stop]
        return candidates[-1] if candidates else None
