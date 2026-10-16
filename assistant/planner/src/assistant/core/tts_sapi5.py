"""Text-to-speech via Windows SAPI5 with better voice selection.

Uses pyttsx3 with SAPI5 engine for better quality voices than default.
Supports voice selection, speed control, and volume adjustment.

Environment variables:
    AETHER_TTS_VOICE: Voice ID or name (default: system default)
    AETHER_TTS_RATE: Speech rate (default: 180, range: 50-400)
    AETHER_TTS_VOLUME: Volume (default: 1.0, range: 0.0-1.0)
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import pyttsx3
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

_lock = threading.Lock()
_voices_listed = False


def _list_voices() -> None:
    """List available voices for user reference."""
    global _voices_listed
    if _voices_listed:
        return
    
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print("\n" + "=" * 60)
        print("  Available TTS Voices (SAPI5)")
        print("=" * 60)
        for i, voice in enumerate(voices):
            print(f"\n  [{i}] {voice.name}")
            print(f"      ID: {voice.id}")
            print(f"      Languages: {voice.languages}")
            print(f"      Gender: {voice.gender}")
        print("\n" + "=" * 60)
        print("To select a voice, set AETHER_TTS_VOICE=<voice_id>")
        print("Example: AETHER_TTS_VOICE=HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")
        print("=" * 60 + "\n")
        _voices_listed = True
        engine.stop()
    except Exception as e:
        print(f"[WARN] Could not list voices: {e}")


def _create_engine() -> pyttsx3.Engine:
    """Create a new TTS engine with configured settings."""
    engine = pyttsx3.init()
    
    # Set voice if specified
    voice_id = os.environ.get("AETHER_TTS_VOICE")
    if voice_id:
        try:
            voices = engine.getProperty('voices')
            for voice in voices:
                if voice_id in voice.id or voice_id in voice.name:
                    engine.setProperty('voice', voice.id)
                    print(f"[OK] Using voice: {voice.name}")
                    break
        except Exception as e:
            print(f"[WARN] Could not set voice: {e}")
    
    # Set rate (speed)
    rate = int(os.environ.get("AETHER_TTS_RATE", "180"))
    try:
        engine.setProperty('rate', rate)
    except Exception as e:
        print(f"[WARN] Could not set rate: {e}")
    
    # Set volume
    volume = float(os.environ.get("AETHER_TTS_VOLUME", "1.0"))
    try:
        engine.setProperty('volume', volume)
    except Exception as e:
        print(f"[WARN] Could not set volume: {e}")
    
    return engine


def speak(text: str) -> None:
    """Speak text aloud, blocking. Thread-safe."""
    if not text:
        return
    
    with _lock:
        engine = None
        try:
            # Create fresh engine each time (pyttsx3 engines can't be reused after runAndWait)
            engine = _create_engine()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[WARN] TTS error: {e}")
        finally:
            # Always stop the engine to release resources
            if engine:
                try:
                    engine.stop()
                except:
                    pass


def list_voices() -> None:
    """List all available TTS voices."""
    _list_voices()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_voices()
    else:
        # Test TTS
        print("Testing SAPI5 TTS...")
        print("Listing available voices:")
        list_voices()
        print("\nTesting default voice...")
        speak("Hello, this is Aether testing text to speech.")
        print("Done.")
