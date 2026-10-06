"""System control skill — shell commands, window management, system actions.

Risk levels:
  - Window focus/minimize/maximize: medium (visible, reversible)
  - Close window: high (may lose unsaved work)
  - Shell commands: high (arbitrary execution)
  - Volume/brightness: low (easily reversible)
  - Screenshot: safe (read-only)
  - Clipboard: low
"""

from __future__ import annotations

import os
import re
import subprocess
import time

from assistant.skills.base import Skill, SkillContext, SkillResult


class SystemControlSkill:
    name = "system_control"
    description = (
        "Run shell commands, manage windows (minimize, maximize, close, focus), "
        "control volume, take screenshots, manage clipboard, lock or sleep the system"
    )
    risk_default = "medium"

    # ---- Routing ----------------------------------------------------------

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        if any(k in text for k in (
            "minimize", "maximise", "maximize", "close window", "close", "focus window",
            "switch to", "bring to front",
        )):
            return 0.9
        if any(k in text for k in ("volume", "mute", "unmute")):
            return 0.88
        if any(k in text for k in ("screenshot", "screen shot", "capture screen")):
            return 0.9
        if any(k in text for k in ("clipboard", "copy to clipboard", "paste from clipboard")):
            return 0.85
        if any(k in text for k in ("lock screen", "lock the screen", "sleep", "hibernate")):
            return 0.88
        if any(k in text for k in ("brightness",)):
            return 0.85
        if any(k in text for k in ("run command", "run shell", "execute", "cmd ", "powershell", "terminal command")):
            return 0.82
        if any(k in text for k in ("kill process", "end process", "stop process", "taskkill")):
            return 0.85
        if any(k in text for k in ("minimise all", "minimize all", "show desktop")):
            return 0.88
        return 0.0

    # ---- Execution --------------------------------------------------------

    def execute(self, context: SkillContext) -> SkillResult:
        text = context.user_intent.lower()

        # Window management
        if any(k in text for k in ("minimize", "minimise")) and "all" in text:
            return self._minimize_all()
        if any(k in text for k in ("minimize", "minimise")):
            return self._window_action(text, "minimize", context)
        if any(k in text for k in ("maximize", "maximise")):
            return self._window_action(text, "maximize", context)
        if "close window" in text or ("close" in text and "window" in text):
            return self._window_action(text, "close", context, high_risk=True)
        # Handle "close [appname]" pattern
        if "close" in text and not any(k in text for k in ("close window", "close all")):
            # Extract potential app name after "close"
            window_name = self._extract_window_name(text)
            if window_name:  # Only if we can extract an app name
                return self._window_action(text, "close", context, high_risk=True)
        if any(k in text for k in ("focus", "switch to", "bring to front")):
            return self._focus_window(text)
        if "show desktop" in text or "minimize all" in text or "minimise all" in text:
            return self._minimize_all()

        # Volume
        if "mute" in text and "un" not in text:
            return self._volume_mute()
        if "unmute" in text:
            return self._volume_unmute()
        if "volume" in text:
            return self._volume_set(text)

        # Brightness
        if "brightness" in text:
            return self._brightness_set(text)

        # Screenshot
        if any(k in text for k in ("screenshot", "screen shot", "capture screen")):
            return self._screenshot()

        # Clipboard
        if "clipboard" in text:
            return self._clipboard(text)

        # System power
        if "lock" in text and "screen" in text:
            return self._lock_screen()
        if "sleep" in text:
            return self._sleep(context)
        if "hibernate" in text:
            return self._hibernate(context)

        # Shell commands
        if any(k in text for k in ("run command", "run shell", "execute", "powershell", "cmd ")):
            return self._shell_command(context)

        # Kill process
        if any(k in text for k in ("kill process", "end process", "stop process", "taskkill")):
            return self._kill_process(text, context)

        return SkillResult(status="clarify", clarification_question="What system action should I take?")

    # ---- Window management ------------------------------------------------

    @staticmethod
    def _get_window(title_fragment: str):
        """Find a window by title fragment (case-insensitive)."""
        import pygetwindow as gw

        all_windows = gw.getAllWindows()
        for win in all_windows:
            if win.title and title_fragment in win.title.lower():
                return win
        return None

    def _window_action(self, text: str, action: str, context: SkillContext, high_risk: bool = False) -> SkillResult:
        # Extract window name from intent
        window_name = self._extract_window_name(text)
        if not window_name:
            return SkillResult(
                status="clarify",
                clarification_question=f"Which window should I {action}?",
            )

        win = self._get_window(window_name)
        if not win:
            return SkillResult(
                status="failed",
                error=f"Window '{window_name}' not found",
                speak=f"I couldn't find a window called {window_name}.",
            )

        if not context.session.get("approved"):
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview=f"{action.capitalize()} window: {win.title}",
                rollback_plan={"kind": "window_action", "action": action, "window": win.title},
            )

        try:
            if action == "minimize":
                win.minimize()
                return SkillResult(status="ok", speak=f"Minimized {win.title}.")
            elif action == "maximize":
                win.maximize()
                return SkillResult(status="ok", speak=f"Maximized {win.title}.")
            elif action == "close":
                win.close()
                return SkillResult(status="ok", speak=f"Closed {win.title}.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak=f"I couldn't {action} that window.")
        return SkillResult(status="failed", error="Unknown action")

    def _focus_window(self, text: str) -> SkillResult:
        window_name = self._extract_window_name(text)
        if not window_name:
            return SkillResult(
                status="clarify",
                clarification_question="Which window should I focus?",
            )
        win = self._get_window(window_name)
        if not win:
            return SkillResult(
                status="failed",
                error=f"Window '{window_name}' not found",
                speak=f"I couldn't find a window called {window_name}.",
            )
        try:
            win.activate()
            time.sleep(0.2)
            return SkillResult(status="ok", speak=f"Switched to {win.title}.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't focus that window.")

    @staticmethod
    def _minimize_all() -> SkillResult:
        try:
            # Win+D shortcut via ctypes — minimize all windows / show desktop
            import ctypes

            ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win down
            ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)  # D down
            ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)  # D up
            ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win up
            return SkillResult(status="ok", speak="Minimized all windows.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't minimize all windows.")

    @staticmethod
    def _extract_window_name(text: str) -> str | None:
        """Extract the window/app name from intent text."""
        text = text.lower()
        # Remove action verbs
        for verb in ("minimize", "minimise", "maximize", "maximise", "close",
                      "focus", "switch to", "bring to front", "window", "the", "app", "application"):
            text = text.replace(verb, "")
        text = text.strip(" .,")
        # Handle common speech recognition errors
        text = text.replace("note pad", "notepad")
        text = text.replace("note bad", "notepad")
        text = text.replace("note-pad", "notepad")
        return text if text else None

    # ---- Volume control ---------------------------------------------------

    def _volume_mute(self) -> SkillResult:
        try:
            import ctypes

            # Send Mute key (Volume Mute)
            ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAD, 0, 2, 0)
            return SkillResult(status="ok", speak="Muted the volume.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't mute the volume.")

    def _volume_unmute(self) -> SkillResult:
        try:
            import ctypes

            ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAD, 0, 2, 0)
            return SkillResult(status="ok", speak="Unmuted the volume.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't unmute the volume.")

    def _volume_set(self, text: str) -> SkillResult:
        level = self._extract_number(text)
        if level is None:
            return SkillResult(
                status="clarify",
                clarification_question="What volume level? Say a number from 0 to 100.",
            )
        level = max(0, min(100, level))
        try:
            # Use PowerShell to set volume via nircmd or fallback to keyboard
            script = (
                f"$obj = New-Object -ComObject WScript.Shell; "
                f"$obj.SendKeys([char]177)"  # Volume up/down approximation
            )
            # Use nircmd if available, otherwise use keyboard approximation
            nircmd = shutil_which("nircmd.exe")
            if nircmd:
                subprocess.run([nircmd, "setsysvolume", str(int(level * 65535 / 100))],
                               capture_output=True, timeout=5)
            else:
                # Approximate: press volume up/down keys
                import ctypes
                steps = abs(level - 50) // 2
                key = 0xAF if level > 50 else 0xAE  # UP or DOWN
                for _ in range(steps):
                    ctypes.windll.user32.keybd_event(key, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(key, 0, 2, 0)
            return SkillResult(status="ok", speak=f"Set volume to {level} percent.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't set the volume.")

    # ---- Brightness -------------------------------------------------------

    def _brightness_set(self, text: str) -> SkillResult:
        level = self._extract_number(text)
        if level is None:
            return SkillResult(
                status="clarify",
                clarification_question="What brightness level? Say a number from 0 to 100.",
            )
        level = max(0, min(100, level))
        try:
            script = (
                f"(Get-WmiObject -Namespace root/WMI "
                f"-Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"
            )
            subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True, timeout=10,
            )
            return SkillResult(status="ok", speak=f"Set brightness to {level} percent.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't set the brightness.")

    # ---- Screenshot -------------------------------------------------------

    def _screenshot(self) -> SkillResult:
        try:
            import pyautogui

            screenshots_dir = os.path.join(
                os.environ.get("USERPROFILE", os.path.expanduser("~")),
                "Pictures", "Screenshots",
            )
            os.makedirs(screenshots_dir, exist_ok=True)
            filename = f"screenshot_{int(time.time())}.png"
            path = os.path.join(screenshots_dir, filename)
            pyautogui.screenshot(path)
            return SkillResult(
                status="ok",
                output=path,
                speak=f"Screenshot saved to {filename}.",
            )
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't take a screenshot.")

    # ---- Clipboard --------------------------------------------------------

    def _clipboard(self, text: str) -> SkillResult:
        if "copy" in text or "set" in text:
            # Extract what to copy
            content = re.sub(r".*(?:copy|set).*?(?:to )?clipboard", "", text, flags=re.IGNORECASE).strip()
            if not content:
                content = re.sub(r".*(?:copy|set)\s+(.*?)\s*(?:to )?clipboard.*", r"\1", text, flags=re.IGNORECASE).strip()
            if not content:
                return SkillResult(
                    status="clarify",
                    clarification_question="What should I copy to the clipboard?",
                )
            try:
                import subprocess

                subprocess.run(
                    ["powershell", "-Command", f"Set-Clipboard -Value '{content}'"],
                    capture_output=True, timeout=5,
                )
                return SkillResult(status="ok", speak=f"Copied to clipboard.")
            except Exception as e:
                return SkillResult(status="failed", error=str(e), speak="I couldn't copy to the clipboard.")
        elif "paste" in text:
            try:
                import pyautogui

                pyautogui.hotkey("ctrl", "v")
                return SkillResult(status="ok", speak="Pasted from clipboard.")
            except Exception as e:
                return SkillResult(status="failed", error=str(e), speak="I couldn't paste from the clipboard.")
        return SkillResult(status="clarify", clarification_question="Should I copy or paste?")

    # ---- System power -----------------------------------------------------

    @staticmethod
    def _lock_screen() -> SkillResult:
        try:
            import ctypes

            ctypes.windll.user32.LockWorkStation()
            return SkillResult(status="ok", speak="Locking the screen.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't lock the screen.")

    @staticmethod
    def _sleep(context: SkillContext) -> SkillResult:
        if not context.session.get("approved"):
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview="Put the system to sleep",
            )
        try:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                           capture_output=True, timeout=5)
            return SkillResult(status="ok", speak="Going to sleep.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't put the system to sleep.")

    @staticmethod
    def _hibernate(context: SkillContext) -> SkillResult:
        if not context.session.get("approved"):
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview="Hibernate the system",
            )
        try:
            subprocess.run(["shutdown", "/h"], capture_output=True, timeout=5)
            return SkillResult(status="ok", speak="Hibernating.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="I couldn't hibernate the system.")

    # ---- Shell commands ---------------------------------------------------

    def _shell_command(self, context: SkillContext) -> SkillResult:
        text = context.user_intent
        # Extract the command after "run" / "execute" / "cmd" etc.
        cmd = self._extract_command(text)
        if not cmd:
            return SkillResult(
                status="clarify",
                clarification_question="What command should I run?",
            )
        if not context.session.get("approved"):
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview=f"Run shell command: {cmd}",
                rollback_plan={"kind": "shell_command", "reversible": False},
            )
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30,
            )
            output = result.stdout.strip() or result.stderr.strip()
            speak = output[:500] if output else "Command completed."
            return SkillResult(
                status="ok",
                output=output,
                speak=speak,
            )
        except subprocess.TimeoutExpired:
            return SkillResult(status="failed", error="Command timed out", speak="The command timed out.")
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak="The command failed.")

    @staticmethod
    def _extract_command(text: str) -> str | None:
        """Extract the shell command from the user intent."""
        text = text.strip()
        # Try to extract after common trigger phrases
        for trigger in ("run command", "run shell", "execute command", "execute",
                        "powershell", "cmd ", "terminal command"):
            idx = text.lower().find(trigger)
            if idx != -1:
                remainder = text[idx + len(trigger):].strip()
                # Remove leading "that", "the", etc.
                remainder = re.sub(r"^(that|the|this)\s+", "", remainder, flags=re.IGNORECASE)
                if remainder:
                    return remainder
        return None

    # ---- Kill process -----------------------------------------------------

    def _kill_process(self, text: str, context: SkillContext) -> SkillResult:
        proc_name = self._extract_process_name(text)
        if not proc_name:
            return SkillResult(
                status="clarify",
                clarification_question="Which process should I kill?",
            )
        if not context.session.get("approved"):
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview=f"Kill process: {proc_name}",
                rollback_plan={"kind": "kill_process", "reversible": False},
            )
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", proc_name],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return SkillResult(status="ok", speak=f"Killed {proc_name}.")
            else:
                return SkillResult(
                    status="failed",
                    error=result.stderr.strip(),
                    speak=f"I couldn't kill {proc_name}. {result.stderr.strip()}",
                )
        except Exception as e:
            return SkillResult(status="failed", error=str(e), speak=f"I couldn't kill {proc_name}.")

    @staticmethod
    def _extract_process_name(text: str) -> str | None:
        text = text.lower()
        for trigger in ("kill process", "end process", "stop process", "taskkill", "kill"):
            idx = text.find(trigger)
            if idx != -1:
                remainder = text[idx + len(trigger):].strip()
                remainder = re.sub(r"^(that|the|this|called|named)\s+", "", remainder, flags=re.IGNORECASE)
                remainder = remainder.strip(" .,")
                if remainder:
                    if not remainder.endswith(".exe"):
                        remainder += ".exe"
                    return remainder
        return None

    # ---- Helpers ----------------------------------------------------------

    @staticmethod
    def _extract_number(text: str) -> int | None:
        match = re.search(r"\b(\d{1,3})\b", text)
        if match:
            return int(match.group(1))
        # Word numbers
        word_map = {"zero": 0, "ten": 10, "twenty": 20, "thirty": 30, "forty": 40,
                    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
                    "hundred": 100}
        for word, num in word_map.items():
            if word in text:
                return num
        return None


def shutil_which(cmd: str) -> str | None:
    """Cross-platform which."""
    import shutil

    return shutil.which(cmd)
