"""Wake-word listener — say "Computer" to talk.

Uses faster-whisper for speech recognition with better accuracy than Vosk.
On wake word detection: plays a chime, then transcribes the command
and sends the text to the planner.

Conversation Mode: After responding, Aether stays in conversation mode
for CONVERSATION_TIMEOUT_S seconds (default 10s), allowing follow-up
questions without needing the wake word again. Say "that's all", "done",
or "thank you" to exit conversation mode early.

Usage: python -m assistant.core.wake_whisper
Can also run hotkey listener in parallel for reliable activation.

Environment variables:
    AETHER_ENABLE_HOTKEY: Set to "1" to enable hotkey listener (default: off)
    AETHER_HOTKEY: Hotkey combination (default: win+alt+a)
    AETHER_CONVERSATION_TIMEOUT: Seconds to wait for follow-up (default: 10.0)
    AETHER_WHISPER_MODEL: Model to use (default: tiny, options: tiny, base, small, medium)
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
from dotenv import load_dotenv

from assistant.core.crash_handler import setup_global_crash_handler

# Load .env file from project root
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

# Set up crash handler
crash_handler = setup_global_crash_handler("Aether Wake Listener")

log = structlog.get_logger()

RATE = 16_000  # Whisper expects 16 kHz
FRAME = 1600  # 100 ms at 16k
SILENCE_RMS = 300  # int16 RMS below this counts as silence
SILENCE_STOP_S = 1.5  # stop after this much trailing silence
GRACE_PERIOD_S = 2.0  # wait this long before silence detection kicks in
MAX_UTTERANCE_S = 12.0
CONVERSATION_TIMEOUT_S = float(os.environ.get("AETHER_CONVERSATION_TIMEOUT", "0.0"))  # 0 = no timeout (continuous listening)
PLANNER_ADDR = ("127.0.0.1", 48100)
WAKE_WORDS = ("computer", "hey computer")
STOP_WORDS = ("stop listening", "stop", "shut down", "go to sleep", "goodbye")
EXIT_CONVERSATION_WORDS = ("that's all", "that's it", "done", "thank you", "thanks")

# Whisper model settings
WHISPER_MODEL = os.environ.get("AETHER_WHISPER_MODEL", "tiny")  # tiny, base, small, medium


def _find_mic() -> int:
    """Find best mic device with better error handling and fallbacks."""
    try:
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        if not input_devices:
            log.error("no_input_devices")
            return -1
        
        # Try MME default input first (device 1 on this system has 10x better signal)
        for api in sd.query_hostapis():
            if api["name"] == "MME":
                dev = api.get("default_input_device")
                if dev is not None and dev >= 0:
                    # Test if this device actually works
                    if _test_mic(dev):
                        log.info("mic_found_mme", device=dev)
                        return dev
        
        # Try to find a device named "Microphone" or similar
        for i, dev in enumerate(input_devices):
            if 'microphone' in dev['name'].lower():
                if _test_mic(i):
                    log.info("mic_found_by_name", device=dev['name'], index=i)
                    return i
        
        # Default to first input device
        if _test_mic(0):
            log.info("mic_using_default", device=input_devices[0]['name'], index=0)
            return 0
        
        # If all else fails, try each device
        for i, dev in enumerate(input_devices):
            if _test_mic(i):
                log.info("mic_fallback", device=dev['name'], index=i)
                return i
        
        log.error("no_working_mic")
        return -1
        
    except Exception as e:
        log.error("mic_detection_failed", error=str(e))
        return -1


def _test_mic(device_id: int) -> bool:
    """Test if a microphone device is working."""
    try:
        with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", device=device_id) as stream:
            # Try to read one frame
            stream.read(FRAME)
        return True
    except Exception as e:
        log.debug("mic_test_failed", device=device_id, error=str(e))
        return False


def _load_whisper_model():
    """Load faster-whisper model."""
    from faster_whisper import WhisperModel
    
    # Use int8 quantization for faster inference and lower memory
    model = WhisperModel(
        WHISPER_MODEL,
        device="cpu",
        compute_type="int8",
        download_root=str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Aether" / "whisper_models")
    )
    return model


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


def _transcribe_audio(wav_path: Path, model) -> str:
    """Transcribe audio using faster-whisper."""
    segments, _ = model.transcribe(str(wav_path), language="en")
    text = " ".join(seg.text for seg in segments)
    return text.strip().lower()


def _notify_planner_text(text: str) -> None:
    """Send transcribed text directly to the planner."""
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


def _check_wake_word(text: str) -> bool:
    """Check if text contains wake word."""
    return any(w in text for w in WAKE_WORDS)


def main() -> None:
    print_header("Aether Wake Word Listener (Whisper)")
    print("Checking audio devices...")
    
    # Check microphone availability
    mic_dev = _find_mic()
    if mic_dev == -1:
        print("\n❌ ERROR: No working microphone found!")
        print("\nPossible solutions:")
        print("1. Check if your microphone is connected and enabled")
        print("2. Go to Settings > System > Sound > Input")
        print("3. Set your microphone as the default input device")
        print("4. Restart your computer if needed")
        print("\nAlternative: Use hotkey mode (no microphone needed):")
        print("   set AETHER_ENABLE_HOTKEY=1")
        print("   python -m assistant.core.wake_whisper")
        print("   Then press Win+Alt+A to activate")
        input("\nPress Enter to exit...")
        return
    
    print(f"✓ Microphone found (device {mic_dev})")
    
    try:
        print(f"Loading Whisper model ({WHISPER_MODEL})...")
        model = _load_whisper_model()
        print("✓ Whisper model loaded")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to load Whisper model: {e}")
        print("\nThe model will be downloaded automatically on first run.")
        print("If this error persists, please check your internet connection.")
        input("\nPress Enter to exit...")
        return
    
    log.info("wake_listening", wake_words=WAKE_WORDS, mic_device=mic_dev, model=WHISPER_MODEL)
    
    # Start hotkey listener if enabled
    hotkey_thread = _start_hotkey_listener()
    if hotkey_thread:
        print(f"✓ Hotkey enabled: {os.environ.get('AETHER_HOTKEY', 'Win+Alt+A').upper()}")
    else:
        print("ℹ Hotkey disabled (set AETHER_ENABLE_HOTKEY=1 to enable)")
    
    print("✓ Wake words: Computer, Hey Computer")
    print("✓ Stop words: Stop listening, Stop, Goodbye")
    print(f"✓ Whisper model: {WHISPER_MODEL}")
    if CONVERSATION_TIMEOUT_S > 0:
        print(f"✓ Conversation timeout: {CONVERSATION_TIMEOUT_S}s")
    else:
        print("✓ Continuous listening enabled")
    print(f"✓ Exit phrases: That's all, Done, Thank you")
    print("\n" + "=" * 60)
    print("  Aether is listening! Say 'Computer' to start.")
    print("=" * 60 + "\n")

    cooldown = 0.0
    in_conversation_mode = False
    conversation_timeout = 0.0
    last_speech_time = 0.0
    
    try:
        with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", device=mic_dev) as stream:
            print("(Listening...)")
            while True:
                # Record utterance
                stream.stop()
                samples = _record_utterance(mic_dev)
                stream.start()
                
                if len(samples) < RATE * 0.3:  # Ignore very short recordings
                    continue
                
                # Transcribe with Whisper
                wav = _save_wav(samples)
                text = _transcribe_audio(wav, model)
                
                if not text:
                    continue
                
                log.debug("whisper_transcription", text=text)
                now = time.monotonic()
                
                # Check for stop phrase
                if any(w in text for w in STOP_WORDS):
                    log.info("stop_phrase_detected", heard=text)
                    print("\n🛑 Stopping. Goodbye!\n")
                    break
                
                # In conversation mode: reset timeout on speech
                if in_conversation_mode and CONVERSATION_TIMEOUT_S > 0:
                    last_speech_time = now
                    conversation_timeout = now + CONVERSATION_TIMEOUT_S
                
                # In conversation mode: check for exit words
                if in_conversation_mode and any(w in text for w in EXIT_CONVERSATION_WORDS):
                    log.info("conversation_exit", heard=text)
                    in_conversation_mode = False
                    print("(Conversation mode ended - say 'Computer' to start again)")
                    print("(Listening...)")
                    continue
                
                # In conversation mode: check for timeout
                if in_conversation_mode and CONVERSATION_TIMEOUT_S > 0:
                    if now > conversation_timeout and (now - last_speech_time) > CONVERSATION_TIMEOUT_S:
                        log.info("conversation_timeout", timeout=CONVERSATION_TIMEOUT_S)
                        in_conversation_mode = False
                        print("(Conversation mode ended - say 'Computer' to start again)")
                        print("(Listening...)")
                        continue
                
                # In conversation mode: treat as follow-up command
                if in_conversation_mode and len(text) > 2:
                    # Ignore wake words in conversation mode
                    if _check_wake_word(text):
                        log.debug("ignoring_wake_word_in_conversation", text=text)
                        continue
                    log.info("follow_up_detected", text=text)
                    try:
                        _notify_planner_text(text)
                    except OSError as e:
                        log.error("planner_unreachable", error=str(e))
                        print("⚠️  Warning: Planner not responding. Make sure the planner is running.")
                    print("(Listening...)")
                    continue
                
                # Check for wake word
                if _check_wake_word(text) and now > cooldown:
                    log.info("wake_detected", heard=text)
                    _chime()
                    in_conversation_mode = True
                    if CONVERSATION_TIMEOUT_S > 0:
                        conversation_timeout = time.monotonic() + CONVERSATION_TIMEOUT_S
                        last_speech_time = time.monotonic()
                    
                    # Extract command (remove wake word)
                    command = text
                    for w in WAKE_WORDS:
                        command = command.replace(w, "").strip()
                    
                    if command:
                        log.info("command_detected", command=command)
                        try:
                            _notify_planner_text(command)
                        except OSError as e:
                            log.error("planner_unreachable", error=str(e))
                            print("⚠️  Warning: Planner not responding. Make sure the planner is running.")
                    
                    cooldown = time.monotonic() + 1.0
                    print("(Listening...)")
                else:
                    log.debug("no_wake_word", text=text)
    
    except sd.PortAudioError as e:
        print(f"\n❌ Audio driver error: {e}")
        print("\nThis is a common issue with PortAudio drivers on Windows.")
        print("\nSolutions:")
        print("1. Open Device Manager (Win+X → Device Manager)")
        print("2. Expand 'Sound, video and game controllers'")
        print("3. Right-click your audio device → Uninstall device")
        print("4. Restart your computer (Windows will reinstall the driver)")
        print("\nTemporary workaround: Use hotkey mode (no microphone needed):")
        print("   set AETHER_ENABLE_HOTKEY=1")
        print("   python -m assistant.core.wake_whisper")
        print("   Then press Win+Alt+A to activate")
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user.\n")
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
