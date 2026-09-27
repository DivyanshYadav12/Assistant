"""File operations skill: create, write, delete — with trash-based rollback.

Risk mapping (docs/SAFETY.md):
- create/save: medium (modifies user files) -> approval once per session
- delete:      high   (destructive)         -> always approval + rollback plan

Deleted files are MOVED to the app trash (%LOCALAPPDATA%/Aether/trash/<uuid>),
never removed permanently, so "undo" can restore them.
"""

from __future__ import annotations

import os
import re
import shutil
import uuid
from pathlib import Path

from assistant.skills.base import SkillContext, SkillResult

TRASH_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Aether" / "trash"

# Spoken location names -> real paths
_LOCATIONS: dict[str, Path] = {
    "desktop": Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
}


class FileOpsSkill:
    name = "file_ops"
    description = "Create, write to, or delete files (delete goes to recoverable trash)"
    risk_default = "medium"

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        has_file_word = "file" in text or self._extract_filename(text) is not None
        if any(v in text for v in ("create", "make", "new")) and has_file_word:
            return 0.9
        if any(v in text for v in ("delete", "remove", "trash")) and has_file_word:
            return 0.9
        if "save" in text and has_file_word:
            return 0.7
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        text = context.user_intent.lower()
        entities = context.entities
        if any(v in text for v in ("delete", "remove", "trash")) or entities.get("action") == "delete":
            return self._delete(context)
        return self._create(context)

    # ----- create / write -------------------------------------------------

    def _create(self, context: SkillContext) -> SkillResult:
        text = context.user_intent
        filename = self._extract_filename(text.lower())
        if not filename and context.entities.get("filename"):
            filename = context.entities["filename"]
        if not filename:
            return SkillResult(
                status="clarify",
                clarification_question="What should the file be called (with extension)?",
            )
        folder = self._extract_location(text.lower())
        if not folder and context.entities.get("location"):
            folder = _LOCATIONS.get(context.entities["location"].lower())
        folder = folder or _LOCATIONS["documents"]
        target = folder / filename
        content = self._extract_content(text) or context.entities.get("content", "") or ""

        if not context.session.get("approved"):
            preview = f"Create file: {target}"
            if content:
                preview += f'\nWith content: "{content}"'
            return SkillResult(
                status="needs_approval", requires_approval=True, approval_preview=preview
            )

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            existed = target.exists()
            backup: Path | None = None
            if existed:  # save pre-image so overwrite is reversible
                backup = TRASH_DIR / f"{uuid.uuid4()}_{target.name}"
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            target.write_text(content, encoding="utf-8")
            return SkillResult(
                status="ok",
                output=str(target),
                speak=f"Created {filename} in {folder.name}.",
                rollback_plan={
                    "kind": "file_create",
                    "target": str(target),
                    "overwrote": existed,
                    "backup": str(backup) if backup else None,
                    "reversible": True,
                },
            )
        except OSError as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't create the file.")

    # ----- delete (always high risk, trash-based) -------------------------

    def _delete(self, context: SkillContext) -> SkillResult:
        text = context.user_intent
        filename = self._extract_filename(text.lower())
        if not filename and context.entities.get("filename"):
            filename = context.entities["filename"]
        if not filename:
            return SkillResult(
                status="clarify",
                clarification_question="Which file should I delete?",
            )
        target = self._resolve_existing(filename, text.lower())
        if target is None and context.entities.get("location"):
            loc = _LOCATIONS.get(context.entities["location"].lower())
            if loc:
                candidate = loc / filename
                if candidate.exists():
                    target = candidate
        if target is None:
            return SkillResult(
                status="ok",
                speak=f"I couldn't find {filename} in Desktop, Documents or Downloads.",
            )

        if not context.session.get("approved"):
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview=f"Delete file: {target}\n(It will be moved to Aether's trash — recoverable)",
            )

        try:
            TRASH_DIR.mkdir(parents=True, exist_ok=True)
            trashed = TRASH_DIR / f"{uuid.uuid4()}_{target.name}"
            shutil.move(str(target), trashed)
            return SkillResult(
                status="ok",
                output=str(trashed),
                speak=f"Deleted {target.name}. Say undo to restore it.",
                rollback_plan={
                    "kind": "file_delete",
                    "original": str(target),
                    "trashed": str(trashed),
                    "reversible": True,
                },
            )
        except OSError as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't delete the file.")

    # ----- parsing helpers -------------------------------------------------

    @staticmethod
    def _extract_filename(text: str) -> str | None:
        m = re.search(r"\b([\w\-.]+\.(txt|md|py|json|csv|log|docx?|xlsx?))\b", text)
        if m:
            return m.group(1).strip()
        m = re.search(r"(?:file\s+(?:named|called)\s+)([\w\-]+)", text)
        if m:
            return m.group(1) + ".txt"
        return None

    @staticmethod
    def _extract_location(text: str) -> Path | None:
        for name, path in _LOCATIONS.items():
            if name in text:
                return path
        return None

    @staticmethod
    def _extract_content(text: str) -> str | None:
        m = re.search(r"(?:with content|containing|that says|saying)\s+(.*)", text, re.IGNORECASE)
        return m.group(1).strip(" .") if m else None

    @staticmethod
    def _resolve_existing(filename: str, text: str) -> Path | None:
        loc = FileOpsSkill._extract_location(text)
        folders = [loc] if loc else list(_LOCATIONS.values())
        for folder in folders:
            candidate = folder / filename
            if candidate.exists():
                return candidate
        return None


class UndoSkill:
    """Restore the most recent rollback-able action (Phase 2: file ops only)."""

    name = "undo"
    description = "Undo the last reversible action"
    risk_default = "low"

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        return 0.95 if "undo" in text or "restore" in text else 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        history: list[dict] = context.session.get("rollback_stack", [])
        if not history:
            return SkillResult(status="ok", speak="There's nothing to undo.")
        plan = history.pop()
        try:
            if plan["kind"] == "file_delete":
                shutil.move(plan["trashed"], plan["original"])
                name = Path(plan["original"]).name
                return SkillResult(status="ok", speak=f"Restored {name}.")
            if plan["kind"] == "file_create":
                target = Path(plan["target"])
                if plan.get("overwrote") and plan.get("backup"):
                    shutil.move(plan["backup"], target)
                    return SkillResult(status="ok", speak=f"Restored previous {target.name}.")
                target.unlink(missing_ok=True)
                return SkillResult(status="ok", speak=f"Removed {target.name}.")
            return SkillResult(status="failed", speak="I don't know how to undo that.")
        except OSError as e:
            return SkillResult(status="failed", error=str(e), speak="Undo failed.")
