"""Phase 1 planner listener.

Receives JSON-lines messages from the Rust daemon on 127.0.0.1:48100.
On `audio_captured`, transcribes the WAV with faster-whisper and prints
the transcript. Later phases plug the transcript into intent -> skills.
"""

from __future__ import annotations

import json
import socketserver
from pathlib import Path

import structlog

from assistant.core.planner import Planner
from assistant.core.transcribe import transcribe_wav
from assistant.core.tts import speak

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
    log.info("planner_listening", host=HOST, port=PORT)
    with socketserver.ThreadingTCPServer((HOST, PORT), PlannerHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
