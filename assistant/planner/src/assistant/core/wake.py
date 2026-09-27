"""Wake-word listener — say "Computer" to talk.

Uses Vosk for continuous on-device speech recognition. On wake word
detection: plays a chime, then uses Vosk to transcribe the command
directly and sends the text to the planner — no Whisper needed.

Usage: python -m assistant.core.wake
Can also run hotkey listener in parallel for reliable activation.

Environment variables:
    AETHER_ENABLE_HOTKEY: Set to "1" to enable hotkey listener (default: off)
    AETHER_HOTKEY: Hotkey combination (default: win+alt+a)
"""

from __future__ import annotations

import json
import os
import socket
import tempfile
import time
import wave
from pathlib import Path
from threading import Thread

import numpy as np
import sounddevice as sd
import structlog

log = structlog.get_logger()

RATE = 16_000  # Vosk expects 16 kHz
FRAME = 1600  # 100 ms at 16k
SILENCE_RMS = 300  # int16 RMS below this counts as silence
SILENCE_STOP_S = 1.5  # stop after this much trailing silence
GRACE_PERIOD_S = 2.0  # wait this long before silence detection kicks in
MAX_UTTERANCE_S = 12.0
PLANNER_ADDR = ("127.0.0.1", 48100)
WAKE_WORDS = ("computer", "hey computer")
STOP_WORDS = ("stop listening", "stop", "shut down", "go to sleep", "goodbye")

_VOSK_MODEL_DIR = str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Aether" / "vosk-model-small-en-us-0.15")


def _find_mic() -> int:
    """Find best mic device. Prefers MME (better gain on some systems)."""
    import sounddevice as sd

    # Try MME default input first (device 1 on this system has 10x better signal)
    for api in sd.query_hostapis():
        if api["name"] == "MME":
            dev = api.get("default_input_device")
            if dev is not None and dev >= 0:
                return dev
    return sd.default.device[0]


def _load_model():
    from vosk import Model

    return Model(_VOSK_MODEL_DIR)


def _record_utterance(mic_dev: int) -> np.ndarray:
    """Record until trailing silence or max length; returns int16 mono at 16kHz."""
    chunks: list[np.ndarray] = []
    silent_for = 0.0
    started = time.monotonic()
    with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", device=mic_dev) as stream:
        while True:
            frame, _ = stream.read(FRAME)
            mono = frame[:, 0]
            chunks.append(mono.copy())
            rms = float(np.sqrt(np.mean(mono.astype(np.float64) ** 2)))
            elapsed = time.monotonic() - started
            # Only count silence after grace period (gives user time to start speaking)
            if elapsed > GRACE_PERIOD_S:
                silent_for = silent_for + FRAME / RATE if rms < SILENCE_RMS else 0.0
            if (silent_for >= SILENCE_STOP_S and elapsed > GRACE_PERIOD_S) or elapsed >= MAX_UTTERANCE_S:
                break
    return np.concatenate(chunks)


def _save_wav(samples: np.ndarray) -> Path:
    path = Path(tempfile.gettempdir()) / "aether_wake_capture.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(samples.tobytes())
    return path


def _notify_planner_text(text: str) -> None:
    """Send transcribed text directly to the planner (skips Whisper)."""
    msg = json.dumps({"type": "text_command", "text": text})
    with socket.create_connection(PLANNER_ADDR, timeout=5) as s:
        s.sendall(msg.encode() + b"\n")


def _notify_planner_audio(wav_path: Path) -> None:
    """Send WAV to planner for Whisper transcription (hotkey path)."""
    msg = json.dumps({"type": "audio_captured", "wav_path": str(wav_path)})
    with socket.create_connection(PLANNER_ADDR, timeout=5) as s:
        s.sendall(msg.encode() + b"\n")


def _chime() -> None:
    try:
        import winsound

        winsound.Beep(880, 120)
        winsound.Beep(1320, 120)
    except Exception:  # noqa: BLE001
        pass


def _start_hotkey_listener() -> Thread | None:
    """Start hotkey listener in a separate thread if enabled."""
    if os.environ.get("AETHER_ENABLE_HOTKEY", "0") != "1":
        return None

    try:
        from assistant.core.hotkey import main as hotkey_main

        hotkey = os.environ.get("AETHER_HOTKEY", "win+alt+a")
        log.info("starting_hotkey_listener", hotkey=hotkey)

        def run_hotkey() -> None:
            try:
                hotkey_main(hotkey)
            except Exception as e:
                log.error("hotkey_listener_failed", error=str(e))

        thread = Thread(target=run_hotkey, daemon=True, name="hotkey_listener")
        thread.start()
        return thread
    except ImportError:
        log.warning("hotkey_module_not_available")
        return None


def main() -> None:
    from vosk import KaldiRecognizer
    from assistant.core.transcribe import transcribe_wav

    model = _load_model()
    mic_dev = _find_mic()
    log.info("wake_listening", wake_words=WAKE_WORDS, mic_device=mic_dev)

    # Start hotkey listener if enabled
    hotkey_thread = _start_hotkey_listener()
    if hotkey_thread:
        print(f"Say 'Computer' or press {os.environ.get('AETHER_HOTKEY', 'Win+Alt+A').upper()} to talk.")
    else:
        print("Say 'Computer' to talk.")
    print("Say 'stop listening' to quit. Ctrl+C also works.")

    rec = KaldiRecognizer(model, RATE)
    cooldown = 0.0
    with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", device=mic_dev) as stream:
        while True:
            frame, _ = stream.read(FRAME)
            mono = frame[:, 0]
            is_final = rec.AcceptWaveform(mono.tobytes())
            if is_final:
                text = json.loads(rec.Result()).get("text", "").lower().strip()
            else:
                text = json.loads(rec.PartialResult()).get("partial", "").lower().strip()
            now = time.monotonic()
            # Check for stop phrase on final results
            if is_final and text and any(w in text for w in STOP_WORDS):
                log.info("stop_phrase_detected", heard=text)
                print("Stopping. Goodbye!")
                break
            # Only trigger on FINAL results to avoid false positives from partials
            if is_final and text and any(w in text for w in WAKE_WORDS) and now > cooldown:
                log.info("wake_detected", heard=text)
                _chime()
                # Reset recognizer
                rec = KaldiRecognizer(model, RATE)
                # Record the command as audio, then use Whisper for accurate transcription
                log.info("listening_for_command")
                stream.stop()
                samples = _record_utterance(mic_dev)
                stream.start()
                if len(samples) > RATE * 0.3:  # at least 0.3s of audio
                    wav = _save_wav(samples)
                    try:
                        _notify_planner_audio(wav)
                    except OSError as e:
                        log.error("planner_unreachable", error=str(e))
                else:
                    log.info("no_command_heard")
                # Reset for next wake detection
                rec = KaldiRecognizer(model, RATE)
                cooldown = time.monotonic() + 1.0
            elif is_final and text:
                log.debug("vosk_final", text=text)


if __name__ == "__main__":
    main()
