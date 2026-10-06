"""Phase 1 planner listener.

Receives JSON-lines messages from the Rust daemon on 127.0.0.1:48100.
On `audio_captured`, transcribes the WAV with faster-whisper and prints
the transcript. Later phases plug the transcript into intent -> skills.
"""

from __future__ import annotations

import json
import os
import socketserver
from pathlib import Path

import structlog
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from assistant.core.planner import Planner
from assistant.core.transcribe import transcribe_wav
from assistant.core.tts import speak
from assistant.core.crash_handler import setup_global_crash_handler

# Set up crash handler
crash_handler = setup_global_crash_handler("Aether Planner")

log = structlog.get_logger()

HOST, PORT = "127.0.0.1", 48100

planner = Planner()


class PlannerHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        for raw in self.rfile:
            line = raw.decode("utf-8").strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                log.warning("bad_message", raw=line[:200])
                continue
            self.dispatch(msg)

    def dispatch(self, msg: dict) -> None:
        if msg.get("type") == "text_command":
            text = msg.get("text", "").strip()
            log.info("text_command", text=text)
            print(f"\n>>> You said: {text}")
            if text:
                reply = planner.handle(text)
                print(f"<<< Aether: {reply}\n")
                speak(reply)
            return
        if msg.get("type") == "audio_captured":
            wav = Path(msg["wav_path"])
            if not wav.exists():
                log.error("wav_missing", path=str(wav))
                return
            log.info("transcribing", path=str(wav))
            text = transcribe_wav(wav)
            log.info("transcript", text=text)
            print(f"\n>>> You said: {text}")
            if text:
                reply = planner.handle(text)
                print(f"<<< Aether: {reply}\n")
                speak(reply)  # speak the full reply
        else:
            log.warning("unknown_message_type", type=msg.get("type"))


def main() -> None:
    print_header("Aether Planner Listener")
    print("Checking dependencies...")
    
    # Check if Ollama is running
    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2) as resp:
            print("✓ Ollama is running")
    except (urllib.error.URLError, urllib.error.HTTPError, ConnectionRefusedError, TimeoutError):
        print("\n❌ ERROR: Ollama is not running!")
        print("\nAether requires Ollama to function.")
        print("Start Ollama by running: ollama serve")
        print("\nOr download Ollama from: https://ollama.com/download")
        input("\nPress Enter to exit...")
        return
    
    # Check if Vosk model exists
    vosk_model_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Aether" / "vosk-model-small-en-us-0.15"
    if not vosk_model_dir.exists():
        print("\n⚠️  WARNING: Vosk speech recognition model not found")
        print("The model will be downloaded automatically on first use.")
        print("This may take a few minutes.")
    
    print("✓ Dependencies checked")
    print(f"✓ Listening on {HOST}:{PORT}")
    print("\n" + "=" * 60)
    print("  Aether Planner is running!")
    print("=" * 60)
    print("\nStart the wake listener in another terminal:")
    print("  python -m assistant.core.wake")
    print("\nOr use hotkey mode:")
    print("  set AETHER_ENABLE_HOTKEY=1")
    print("  python -m assistant.core.wake")
    print("  Then press Win+Alt+A to activate")
    print("\nPress Ctrl+C to stop the planner.\n")
    
    log.info("planner_listening", host=HOST, port=PORT)
    
    try:
        with socketserver.ThreadingTCPServer((HOST, PORT), PlannerHandler) as server:
            server.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ ERROR: Port {PORT} is already in use!")
            print("\nAnother instance of Aether is likely already running.")
            print("\nTo fix this:")
            print("1. Find the process using this port:")
            print(f"   netstat -ano | findstr :{PORT}")
            print("2. Kill the process:")
            print("   taskkill /PID <PID> /F")
            print("\nOr simply close the other terminal running Aether.")
        else:
            print(f"\n❌ ERROR: {e}")
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\n👋 Planner stopped by user.\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please report this issue for debugging.")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


if __name__ == "__main__":
    main()
