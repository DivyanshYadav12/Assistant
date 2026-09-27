"""File cleanup skill — finds duplicates, stale caches, build artifacts, and large files.

Scans user directories for:
  - Duplicate files (by content hash)
  - Stale cache directories (node_modules, __pycache__, .venv, target, etc.)
  - Large files (> configurable threshold)
  - Orphaned packages / build artifacts

Deletion is always `high` risk — requires approval + trash-based rollback.
Scan-only is `safe` — no approval needed.

See docs/FEATURES.md §6 and docs/SKILLS.md §5.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import time
import uuid
from collections import defaultdict
from pathlib import Path

from assistant.skills.base import SkillContext, SkillResult

TRASH_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Aether" / "trash"

# Directories that are safe to clean up (cache/build artifacts)
_CACHE_DIRS = {
    "node_modules": "Node.js dependencies",
    "__pycache__": "Python bytecode cache",
    ".venv": "Python virtual environment",
    "venv": "Python virtual environment",
    "target": "Rust/Cargo build output",
    "build": "Build output",
    "dist": "Distribution output",
    ".next": "Next.js build cache",
    ".nuxt": "Nuxt.js build cache",
    ".cache": "Generic cache",
    ".pytest_cache": "Pytest cache",
    ".mypy_cache": "MyPy cache",
    ".ruff_cache": "Ruff cache",
    ".gradle": "Gradle cache",
    ".terraform": "Terraform cache",
}

# Default scan locations
_SCAN_DIRS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
]

_LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100 MB
_MAX_SCAN_FILES = 50_000
_MAX_DUPLICATE_GROUPS = 20


class FileCleanupSkill:
    name = "file_cleanup"
    description = (
        "Find and clean up duplicate files, stale caches (node_modules, __pycache__), "
        "build artifacts, and large files. Deletion goes to recoverable trash."
    )
    risk_default = "high"

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        if any(k in text for k in ("duplicate", "duplicates")):
            return 0.92
        if any(k in text for k in ("clean up", "cleanup", "clean disk", "free up space", "free space")):
            return 0.9
        if any(k in text for k in ("cache", "node_modules", "pycache", "build artifacts", "temp files")):
            return 0.88
        if any(k in text for k in ("large files", "big files", "what's taking up space", "disk usage")):
            return 0.85
        if "junk files" in text or "unnecessary files" in text:
            return 0.85
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        text = context.user_intent.lower()

        # Determine scan mode
        if "duplicate" in text:
            return self._scan_duplicates(context)
        if any(k in text for k in ("cache", "node_modules", "pycache", "build artifacts")):
            return self._scan_caches(context)
        if any(k in text for k in ("large files", "big files", "what's taking up space", "disk usage")):
            return self._scan_large_files(context)
        if any(k in text for k in ("clean up", "cleanup", "clean disk", "free up space", "free space", "junk", "unnecessary")):
            return self._scan_all(context)
        return SkillResult(
            status="clarify",
            clarification_question="What should I scan for? Duplicates, caches, large files, or everything?",
        )

    # ---- Duplicate scanner ------------------------------------------------

    def _scan_duplicates(self, context: SkillContext) -> SkillResult:
        """Find duplicate files by content hash."""
        scan_dirs = self._get_scan_dirs(context)
        hashes: dict[str, list[Path]] = defaultdict(list)
        file_count = 0

        for root in scan_dirs:
            if not root.exists():
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                # Skip cache dirs during duplicate scan
                dirnames[:] = [d for d in dirnames if d not in _CACHE_DIRS and not d.startswith(".")]
                for fn in filenames:
                    if file_count >= _MAX_SCAN_FILES:
                        break
                    fp = Path(dirpath) / fn
                    if fp.stat().st_size < 1024:  # skip files < 1KB
                        continue
                    h = self._hash_file(fp)
                    if h:
                        hashes[h].append(fp)
                        file_count += 1

        duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
        total_waste = sum(
            (len(paths) - 1) * paths[0].stat().st_size
            for paths in duplicates.values()
        )

        if not duplicates:
            return SkillResult(status="ok", speak="No duplicate files found.")

        # Format results
        groups = []
        for h, paths in list(duplicates.items())[:_MAX_DUPLICATE_GROUPS]:
            size = paths[0].stat().st_size
            groups.append({
                "hash": h[:8],
                "size": size,
                "size_mb": round(size / 1024 / 1024, 1),
                "files": [str(p) for p in paths],
            })

        speak = (
            f"Found {len(duplicates)} group{'s' if len(duplicates) != 1 else ''} of duplicates. "
            f"About {round(total_waste / 1024 / 1024, 1)} MB can be freed."
        )

        # If approved, move duplicates to trash (keep first copy)
        if context.session.get("approved"):
            return self._delete_duplicates(groups, context)

        return SkillResult(
            status="needs_approval",
            requires_approval=True,
            approval_preview=f"Delete {len(duplicates)} groups of duplicates ({round(total_waste / 1024 / 1024, 1)} MB)? "
            f"First copy kept, rest moved to trash.",
            output=groups,
            speak=speak,
        )

    @staticmethod
    def _delete_duplicates(groups: list[dict], context: SkillContext) -> SkillResult:
        """Move duplicate files to trash (keep first copy of each group)."""
        TRASH_DIR.mkdir(parents=True, exist_ok=True)
        deleted = 0
        freed = 0
        rollback_items: list[dict] = []

        for group in groups:
            files = group["files"]
            for fp_str in files[1:]:  # keep first, trash the rest
                fp = Path(fp_str)
                try:
                    trashed = TRASH_DIR / f"{uuid.uuid4()}_{fp.name}"
                    shutil.move(str(fp), trashed)
                    deleted += 1
                    freed += group["size"]
                    rollback_items.append({
                        "original": str(fp),
                        "trashed": str(trashed),
                    })
                except OSError:
                    pass

        return SkillResult(
            status="ok",
            speak=f"Deleted {deleted} duplicate files, freed {round(freed / 1024 / 1024, 1)} MB. Say undo to restore.",
            rollback_plan={
                "kind": "duplicate_cleanup",
                "items": rollback_items,
                "reversible": True,
            },
        )

    # ---- Cache scanner ----------------------------------------------------

    def _scan_caches(self, context: SkillContext) -> SkillResult:
        """Find cache/build directories and their sizes."""
        scan_dirs = self._get_scan_dirs(context)
        caches: list[dict] = []
        total_size = 0

        for root in scan_dirs:
            if not root.exists():
                continue
            for dirpath, dirnames, _ in os.walk(root):
                for d in dirnames:
                    if d in _CACHE_DIRS:
                        cache_path = Path(dirpath) / d
                        size = self._dir_size(cache_path)
                        if size > 1024 * 1024:  # only report > 1MB
                            caches.append({
                                "path": str(cache_path),
                                "type": d,
                                "description": _CACHE_DIRS[d],
                                "size_mb": round(size / 1024 / 1024, 1),
                            })
                            total_size += size

        if not caches:
            return SkillResult(status="ok", speak="No cache directories found.")

        caches.sort(key=lambda c: c["size_mb"], reverse=True)
        speak = (
            f"Found {len(caches)} cache director{'ies' if len(caches) != 1 else 'y'}, "
            f"totaling {round(total_size / 1024 / 1024, 1)} MB."
        )

        if context.session.get("approved"):
            return self._delete_caches(caches)

        return SkillResult(
            status="needs_approval",
            requires_approval=True,
            approval_preview=f"Delete {len(caches)} cache directories ({round(total_size / 1024 / 1024, 1)} MB)? "
            f"These can be regenerated when needed.",
            output=caches,
            speak=speak,
        )

    @staticmethod
    def _delete_caches(caches: list[dict]) -> SkillResult:
        """Move cache directories to trash."""
        TRASH_DIR.mkdir(parents=True, exist_ok=True)
        deleted = 0
        freed = 0
        rollback_items: list[dict] = []

        for cache in caches:
            src = Path(cache["path"])
            try:
                trashed = TRASH_DIR / f"{uuid.uuid4()}_{src.name}"
                shutil.move(str(src), trashed)
                deleted += 1
                freed += int(cache["size_mb"] * 1024 * 1024)
                rollback_items.append({
                    "original": str(src),
                    "trashed": str(trashed),
                })
            except OSError:
                pass

        return SkillResult(
            status="ok",
            speak=f"Cleaned {deleted} cache directories, freed {round(freed / 1024 / 1024, 1)} MB. Say undo to restore.",
            rollback_plan={
                "kind": "cache_cleanup",
                "items": rollback_items,
                "reversible": True,
            },
        )

    # ---- Large file scanner -----------------------------------------------

    def _scan_large_files(self, context: SkillContext) -> SkillResult:
        """Find files larger than the threshold."""
        scan_dirs = self._get_scan_dirs(context)
        large_files: list[dict] = []
        file_count = 0

        for root in scan_dirs:
            if not root.exists():
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in _CACHE_DIRS and not d.startswith(".")]
                for fn in filenames:
                    if file_count >= _MAX_SCAN_FILES:
                        break
                    fp = Path(dirpath) / fn
                    try:
                        size = fp.stat().st_size
                        if size >= _LARGE_FILE_THRESHOLD:
                            large_files.append({
                                "path": str(fp),
                                "size_mb": round(size / 1024 / 1024, 1),
                                "modified": time.strftime(
                                    "%Y-%m-%d", time.localtime(fp.stat().st_mtime)
                                ),
                            })
                            file_count += 1
                    except OSError:
                        pass

        if not large_files:
            return SkillResult(status="ok", speak="No large files found.")

        large_files.sort(key=lambda f: f["size_mb"], reverse=True)
        total = sum(f["size_mb"] for f in large_files)
        speak = (
            f"Found {len(large_files)} large file{'s' if len(large_files) != 1 else ''} "
            f"(over 100 MB), totaling {round(total, 1)} MB."
        )

        return SkillResult(
            status="ok",
            output=large_files[:20],
            speak=speak,
        )

    # ---- Full scan --------------------------------------------------------

    def _scan_all(self, context: SkillContext) -> SkillResult:
        """Scan for duplicates + caches + large files, give a summary."""
        dup_result = self._scan_duplicates(context)
        cache_result = self._scan_caches(context)
        large_result = self._scan_large_files(context)

        parts = []
        if dup_result.speak:
            parts.append(dup_result.speak)
        if cache_result.speak:
            parts.append(cache_result.speak)
        if large_result.speak:
            parts.append(large_result.speak)

        combined_output = {
            "duplicates": dup_result.output if isinstance(dup_result.output, list) else [],
            "caches": cache_result.output if isinstance(cache_result.output, list) else [],
            "large_files": large_result.output if isinstance(large_result.output, list) else [],
        }

        return SkillResult(
            status="ok",
            output=combined_output,
            speak=" ".join(parts),
        )

    # ---- Helpers ----------------------------------------------------------

    @staticmethod
    def _hash_file(path: Path, chunk_size: int = 65536) -> str | None:
        """Return SHA-256 hash of file content, or None on error."""
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            return None

    @staticmethod
    def _dir_size(path: Path) -> int:
        """Get total size of a directory in bytes."""
        total = 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for fn in filenames:
                    fp = Path(dirpath) / fn
                    try:
                        total += fp.stat().st_size
                    except OSError:
                        pass
        except OSError:
            pass
        return total

    @staticmethod
    def _get_scan_dirs(context: SkillContext) -> list[Path]:
        """Determine which directories to scan from the user intent."""
        text = context.user_intent.lower()
        dirs = []
        if "desktop" in text:
            dirs.append(Path.home() / "Desktop")
        if "documents" in text or "document" in text:
            dirs.append(Path.home() / "Documents")
        if "downloads" in text or "download" in text:
            dirs.append(Path.home() / "Downloads")
        if "projects" in text or "project" in text:
            dirs.append(Path.home() / "Projects")
        if not dirs:
            dirs = _SCAN_DIRS[:]
        return dirs
