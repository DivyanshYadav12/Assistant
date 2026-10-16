"""Text-to-speech via VoxCPM — advanced multilingual TTS with voice cloning.

VoxCPM is a state-of-the-art TTS model with:
- 30 languages support
- Voice cloning capabilities
- Voice design from text descriptions
- Controllable style (emotion, pace, tone)
- 48kHz high-fidelity audio
- 100% local operation

Requirements:
- Python 3.10-3.12
- PyTorch 2.5.0+
- CUDA 12.0+ (optional, for GPU acceleration)
- voxcpm package: pip install voxcpm

Environment variables:
    AETHER_TTS_ENGINE: tts_voxcpm (VoxCPM) or tts_sapi5 (Windows SAPI5)
    AETHER_TTS_VOICE_MODEL: openbmb/VoxCPM2 (default) or openbmb/VoxCPM-0.5B
    AETHER_TTS_VOICE_CLONE: Path to reference audio for voice cloning (optional)
    AETHER_TTS_VOICE_DESCRIPTION: Text description for voice design (optional)
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

_lock = threading.Lock()
_model = None
_config = None


def _load_model():
    """Load VoxCPM model (cached)."""
    global _model, _config
    
    if _model is not None:
        return _model, _config
    
    try:
        from voxcpm import VoxCPM
        
        model_name = os.environ.get("AETHER_TTS_VOICE_MODEL", "openbmb/VoxCPM2")
        
        print(f"Loading VoxCPM model: {model_name}")
        print("This may take a few minutes on first run...")
        
        _model = VoxCPM.from_pretrained(
            model_name,
            load_denoiser=False,  # Set to True if using voice cloning with noisy audio
        )
        
        _config = {
            "sample_rate": _model.tts_model.sample_rate,
            "model_name": model_name,
        }
        
        print(f"[OK] VoxCPM model loaded: {model_name}")
        return _model, _config
        
    except ImportError:
        print("[WARN] VoxCPM not installed. Install with: pip install voxcpm")
        print("Falling back to SAPI5 TTS...")
        return None, {"fallback": True}
    except Exception as e:
        print(f"[WARN] Failed to load VoxCPM: {e}")
        print("Falling back to SAPI5 TTS...")
        return None, {"fallback": True}


def speak(text: str) -> None:
    """Speak text aloud using VoxCPM, blocking. Thread-safe."""
    if not text:
        return
    
    with _lock:
        model, config = _load_model()
        
        # Fallback to SAPI5 if VoxCPM not available
        if config.get("fallback"):
            _speak_sapi5(text)
            return
        
        try:
            import soundfile as sf
            import tempfile
            
            # Check for voice cloning or voice design
            reference_audio = os.environ.get("AETHER_TTS_VOICE_CLONE")
            voice_description = os.environ.get("AETHER_TTS_VOICE_DESCRIPTION")
            
            generation_kwargs = {
                "text": text,
                "cfg_value": 2.0,
                "inference_timesteps": 10,
            }
            
            # Voice cloning mode
            if reference_audio and Path(reference_audio).exists():
                print(f"[INFO] Using voice cloning from: {reference_audio}")
                generation_kwargs["reference_wav_path"] = reference_audio
            
            # Voice design mode
            if voice_description:
                print(f"[INFO] Using voice design: {voice_description}")
                generation_kwargs["text"] = f"({voice_description}){text}"
            
            # Generate audio
            wav = model.generate(**generation_kwargs)
            
            # Save to temp file and play
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            sf.write(temp_path, wav, config["sample_rate"])
            
            # Play audio
            import sounddevice as sd
            sd.play(wav, config["sample_rate"])
            sd.wait()
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            print(f"[WARN] VoxCPM TTS error: {e}")
            print("Falling back to SAPI5...")
            _speak_sapi5(text)


def _speak_sapi5(text: str) -> None:
    """Fallback TTS using Windows SAPI5."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        
        # Load voice settings from .env
        voice_id = os.environ.get("AETHER_TTS_VOICE")
        if voice_id:
            try:
                voices = engine.getProperty('voices')
                for voice in voices:
                    if voice_id in voice.id or voice_id in voice.name:
                        engine.setProperty('voice', voice.id)
                        break
            except:
                pass
        
        rate = int(os.environ.get("AETHER_TTS_RATE", "180"))
        engine.setProperty('rate', rate)
        
        volume = float(os.environ.get("AETHER_TTS_VOLUME", "1.0"))
        engine.setProperty('volume', volume)
        
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"⚠️  SAPI5 TTS error: {e}")


def list_voices() -> None:
    """List available TTS options for VoxCPM."""
    print("\n" + "=" * 60)
    print("  VoxCPM TTS Options")
    print("=" * 60)
    print("\nAvailable Models:")
    print("  - openbmb/VoxCPM2 (2B parameters, best quality)")
    print("  - openbmb/VoxCPM-0.5B (0.5B parameters, faster)")
    print("\nVoice Modes:")
    print("  1. Default: Use built-in voice")
    print("  2. Voice Cloning: Set AETHER_TTS_VOICE_CLONE=path/to/audio.wav")
    print("  3. Voice Design: Set AETHER_TTS_VOICE_DESCRIPTION='description'")
    print("\nExample Voice Descriptions:")
    print("  - 'A young woman, gentle and warm'")
    print("  - 'A deep male voice, authoritative'")
    print("  - 'A cheerful, energetic voice'")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_voices()
    else:
        # Test TTS
        print("Testing VoxCPM TTS...")
        list_voices()
        print("\nTesting default voice...")
        speak("Hello, this is a test of VoxCPM text to speech.")
        print("Done.")
