"""Text-to-speech engine selector.

Supports multiple TTS engines:
- SAPI5 (Windows default, fast, simple)
- VoxCPM (advanced, multilingual, voice cloning)

Environment variables:
    AETHER_TTS_ENGINE: tts_sapi5 (default) or tts_voxcpm
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

# Get configured TTS engine
_tts_engine = os.environ.get("AETHER_TTS_ENGINE", "tts_sapi5")


def speak(text: str) -> None:
    """Speak text aloud using configured TTS engine."""
    if not text:
        return
    
    if _tts_engine == "tts_voxcpm":
        from assistant.core.tts_voxcpm import speak as speak_voxcpm
        speak_voxcpm(text)
    else:
        from assistant.core.tts_sapi5 import speak as speak_sapi5
        speak_sapi5(text)


def list_voices() -> None:
    """List available voices for configured TTS engine."""
    if _tts_engine == "tts_voxcpm":
        from assistant.core.tts_voxcpm import list_voices
        list_voices()
    else:
        from assistant.core.tts_sapi5 import list_voices
        list_voices()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_voices()
    else:
        # Test TTS
        print(f"Testing TTS with engine: {_tts_engine}")
        list_voices()
        print("\nTesting speech...")
        speak("Hello, this is a test of the text to speech system.")
        print("Done.")
