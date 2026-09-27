"""Voice input for short responses — captures a brief utterance and transcribes it.

Used by the approval flow to listen for "yes"/"no"/"approve"/"reject"
without needing the wake word listener process.
"""

from __future__ import annotations

import tempfile
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from assistant.core.transcribe import transcribe_wav

RATE = 16_000
FRAME = 1600  # 100 ms at 16k
SILENCE_RMS = 300
SILENCE_STOP_S = 1.2  # stop after this much trailing silence
GRACE_PERIOD_S = 0.5  # brief grace before silence detection
MAX_UTTERANCE_S = 6.0  # max wait for a response


def _find_mic() -> int:
    """Find best mic device — same logic as wake.py."""
    for api in sd.query_hostapis():
        if api["name"] == "MME":
            dev = api.get("default_input_device")
            if dev is not None and dev >= 0:
                return dev
    return sd.default.device[0]


def capture_utterance(timeout_s: float = MAX_UTTERANCE_S) -> str:
    """Record a short voice utterance and return the transcribed text.

    Records until silence detected or timeout. Returns empty string if
    no speech detected.
    """
    mic_dev = _find_mic()
    chunks: list[np.ndarray] = []
    silent_for = 0.0
    started = time.monotonic()
    has_speech = False

    try:
        with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", device=mic_dev) as stream:
            while True:
                frame, _ = stream.read(FRAME)
                mono = frame[:, 0]
                chunks.append(mono.copy())
                rms = float(np.sqrt(np.mean(mono.astype(np.float64) ** 2)))
                elapsed = time.monotonic() - started

                if rms > SILENCE_RMS:
                    has_speech = True

                if elapsed > GRACE_PERIOD_S:
                    silent_for = silent_for + FRAME / RATE if rms < SILENCE_RMS else 0.0

                if (silent_for >= SILENCE_STOP_S and elapsed > GRACE_PERIOD_S) or elapsed >= timeout_s:
                    break
    except Exception:
        return ""

    if not has_speech:
        return ""

    samples = np.concatenate(chunks)
    if len(samples) < RATE * 0.2:  # less than 0.2s of audio
        return ""

    # Save to temp WAV and transcribe
    wav_path = Path(tempfile.gettempdir()) / "aether_approval_response.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(samples.tobytes())

    try:
        text = transcribe_wav(wav_path)
        return text.lower().strip()
    except Exception:
        return ""
