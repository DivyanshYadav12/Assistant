"""Text-to-speech via Windows SAPI (pyttsx3) — offline, zero setup.

Swapped for piper (more natural voices) in a later phase.
"""

from __future__ import annotations

import threading

import pyttsx3

_lock = threading.Lock()


def speak(text: str) -> None:
    """Speak text aloud, blocking. Thread-safe (SAPI engine is not)."""
    if not text:
        return
    with _lock:
        engine = pyttsx3.init()
        engine.setProperty("rate", 180)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
