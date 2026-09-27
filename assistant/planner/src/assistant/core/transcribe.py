"""Whisper transcription (faster-whisper), lazily loaded.

Model size is controlled by AETHER_WHISPER_MODEL (default: "base").
With a GPU, set AETHER_WHISPER_DEVICE=cuda for much faster inference.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel


@lru_cache(maxsize=1)
def _model() -> WhisperModel:
    name = os.environ.get("AETHER_WHISPER_MODEL", "tiny")
    device = os.environ.get("AETHER_WHISPER_DEVICE", "auto")
    compute = "float16" if device == "cuda" else "int8"
    return WhisperModel(name, device=device, compute_type=compute)


def transcribe_wav(path: Path) -> str:
    segments, _info = _model().transcribe(str(path), vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()
