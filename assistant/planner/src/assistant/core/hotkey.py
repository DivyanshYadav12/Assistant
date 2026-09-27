"""Hotkey listener — press Win+Alt+A to activate voice input.

Runs alongside the wake word listener. Provides a reliable alternative
to voice activation in noisy environments.

Usage: python -m assistant.core.hotkey
"""

from __future__ import annotations

import json
import os
import socket
import tempfile
import time
import wave
from pathlib import Path
from threading import Event, Thread

import numpy as np
import sounddevice as sd
import structlog

log = structlog.get_logger()

RATE = 16_000
FRAME = 1600
SILENCE_RMS = 300
SILENCE_STOP_S = 1.5
GRACE_PERIOD_S = 2.0
MAX_UTTERANCE_S = 12.0
PLANNER_ADDR = ("127.0.0.1", 48100)
DEFAULT_HOTKEY = "win+alt+a"


def _find_mic() -> int:
    """Find best mic device. Prefers MME (better gain on some systems)."""
    for api in sd.query_hostapis():
        if api["name"] == "MME":
            dev = api.get("default_input_device")
            if dev is not None and dev >= 0:
                return dev
    return sd.default.device[0]


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
            if elapsed > GRACE_PERIOD_S:
                silent_for = silent_for + FRAME / RATE if rms < SILENCE_RMS else 0.0
            if (silent_for >= SILENCE_STOP_S and elapsed > GRACE_PERIOD_S) or elapsed >= MAX_UTTERANCE_S:
                break
    return np.concatenate(chunks)


def _save_wav(samples: np.ndarray) -> Path:
    path = Path(tempfile.gettempdir()) / "aether_hotkey_capture.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(samples.tobytes())
    return path


def _notify_planner_audio(wav_path: Path) -> None:
    """Send WAV to planner for Whisper transcription."""
    msg = json.dumps({"type": "audio_captured", "wav_path": str(wav_path)})
    with socket.create_connection(PLANNER_ADDR, timeout=5) as s:
        s.sendall(msg.encode() + b"\n")


def _chime() -> None:
    """Play activation chime."""
    try:
        import winsound
        winsound.Beep(880, 120)
        winsound.Beep(1320, 120)
    except Exception:  # noqa: BLE001
        pass


def _on_hotkey_trigger(mic_dev: int, stop_event: Event) -> None:
    """Called when hotkey is pressed. Records audio and sends to planner."""
    if stop_event.is_set():
        return

    log.info("hotkey_triggered")
    _chime()

    log.info("listening_for_command")
    try:
        samples = _record_utterance(mic_dev)
        if len(samples) > RATE * 0.3:
            wav = _save_wav(samples)
            try:
                _notify_planner_audio(wav)
                log.info("audio_sent_to_planner", path=str(wav))
            except OSError as e:
                log.error("planner_unreachable", error=str(e))
        else:
            log.info("no_command_heard")
    except Exception as e:
        log.error("hotkey_recording_failed", error=str(e))


def main(hotkey: str = DEFAULT_HOTKEY) -> None:
    """Start hotkey listener.

    Args:
        hotkey: Keyboard shortcut to listen for (default: win+alt+a)
    """
    import keyboard

    mic_dev = _find_mic()
    stop_event = Event()

    log.info("hotkey_listening", hotkey=hotkey, mic_device=mic_dev)
    print(f"Hotkey listener running. Press {hotkey.upper()} to talk. Ctrl+C to quit.")

    try:
        keyboard.add_hotkey(
            hotkey,
            lambda: _on_hotkey_trigger(mic_dev, stop_event),
        )
        # Keep the main thread alive
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        log.info("hotkey_listener_stopped")
        print("\nStopping hotkey listener...")
    finally:
        keyboard.unhook_all_hotkeys()
        stop_event.set()


if __name__ == "__main__":
    import sys

    hotkey_str = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOTKEY
    main(hotkey_str)
