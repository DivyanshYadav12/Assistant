"""Code generation skill - writes actual code to Notepad or files.

Distinguishes from type_text:
- "write a program" → generates code
- "write text" → writes literal text
"""

from __future__ import annotations

import re
import time

import pyautogui
import pyperclip

from assistant.core import llm
from assistant.skills.base import SkillContext, SkillResult


class CodeGenerationSkill:
    """Generate code and write it to Notepad or a file."""

    name = "code_generation"
    description = "Generate code in any programming language and write it to Notepad or a file"
    risk_default = "medium"

    _TRIGGER = ("write a program", "write code", "generate code", "create a program",
                "write a function", "write a class", "code for", "program to")
    
    _LANGUAGES = {
        "python": "python",
        "c++": "cpp",
        "c plus plus": "cpp",
        "javascript": "js",
        "java": "java",
        "html": "html",
        "css": "css",
        "sql": "sql",
        "rust": "rs",
        "go": "go",
        "typescript": "ts",
    }

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower().strip()
        
        # Check for code-specific triggers
        if any(t in text for t in self._TRIGGER):
            return 0.92
        
        # Check for language keywords + programming context
        has_language = any(lang in text for lang in self._LANGUAGES.keys())
        has_programming = any(word in text for word in ("function", "class", "loop", "variable", 
                                                        "algorithm", "logic", "syntax"))
        if has_language and has_programming:
            return 0.85
        
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        text = context.user_intent.lower()
        
        # Extract the programming language
        language = self._extract_language(text)
        
        # Extract what the code should do
        task = self._extract_task(text)
        
        if not task:
            return SkillResult(
                status="clarify",
                clarification_question="What should the code do?",
            )
        
        # Check if user wants it in Notepad or a file
        to_notepad = "notepad" in text or "note pad" in text
        
        if not context.session.get("approved"):
            preview = f"Generate {language or 'code'} for: {task}"
            if to_notepad:
                preview += "\nWrite to Notepad"
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview=preview,
            )
        
        # Generate the code using LLM
        code = self._generate_code(task, language)
        
        if not code:
            return SkillResult(
                status="failed",
                speak="I couldn't generate the code.",
            )
        
        # Write to Notepad or file
        if to_notepad:
            return self._write_to_notepad(code, task)
        else:
            return self._write_to_file(code, language, task)

    def _extract_language(self, text: str) -> str:
        """Extract programming language from text."""
        text = text.lower()
        for lang_name, ext in self._LANGUAGES.items():
            if lang_name in text:
                return ext
        return "python"  # Default to Python

    def _extract_task(self, text: str) -> str:
        """Extract what the code should do."""
        # Remove trigger phrases
        for phrase in self._TRIGGER:
            text = text.replace(phrase, "")
        
        # Remove language keywords
        for lang in self._LANGUAGES.keys():
            text = text.replace(lang, "")
        
        # Remove "in notepad" or similar
        text = re.sub(r"\b(in|on|to|for)\s+(notepad|note pad)\b", "", text, flags=re.IGNORECASE)
        
        # Clean up
        task = text.strip()
        task = " ".join(task.split())  # Normalize spaces
        
        return task

    def _generate_code(self, task: str, language: str) -> str | None:
        """Generate code using the LLM."""
        if not llm.is_available():
            return None
        
        prompt = f"""Write {language} code to: {task}

Provide only the code, no explanation. Include comments for clarity."""
        
        try:
            response = llm.chat(prompt)
            if response:
                # Clean up any markdown code blocks
                response = re.sub(r"```[\w]*\n?", "", response)
                response = re.sub(r"```", "", response)
                return response.strip()
        except Exception:
            pass
        
        return None

    def _write_to_notepad(self, code: str, task: str) -> SkillResult:
        """Write code to Notepad."""
        try:
            # Copy code to clipboard
            pyperclip.copy(code)
            time.sleep(0.2)
            
            # Paste into Notepad
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)
            
            return SkillResult(
                status="ok",
                speak=f"I've written the code in Notepad.",
                output={"code": code, "task": task},
            )
        except Exception as e:
            return SkillResult(
                status="failed",
                error=str(e),
                speak="I generated the code but couldn't write it to Notepad.",
            )

    def _write_to_file(self, code: str, language: str, task: str) -> SkillResult:
        """Write code to a file."""
        from pathlib import Path
        import os
        
        # Generate a filename based on the task
        filename = self._generate_filename(task, language)
        folder = Path.home() / "Documents"
        target = folder / filename
        
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code, encoding="utf-8")
            
            return SkillResult(
                status="ok",
                speak=f"I've created {filename} in Documents.",
                output={"file": str(target), "code": code, "task": task},
            )
        except Exception as e:
            return SkillResult(
                status="failed",
                error=str(e),
                speak="I generated the code but couldn't save it to a file.",
            )

    def _generate_filename(self, task: str, language: str) -> str:
        """Generate a filename based on the task."""
        # Take first few words of task, sanitize
        words = re.findall(r"\w+", task)[:3]
        if not words:
            words = ["code"]
        
        name = "_".join(words)
        ext = {
            "python": ".py",
            "cpp": ".cpp",
            "js": ".js",
            "java": ".java",
            "html": ".html",
            "css": ".css",
            "sql": ".sql",
            "rs": ".rs",
            "go": ".go",
            "ts": ".ts",
        }.get(language, ".txt")
        
        return f"{name}{ext}"
