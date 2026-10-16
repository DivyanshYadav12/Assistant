# VoxCPM TTS Integration Guide

## Overview

VoxCPM is a state-of-the-art Text-to-Speech model with advanced features:

- **30 languages** support
- **Voice cloning** from short audio clips
- **Voice design** - create voices from text descriptions
- **Controllable style** - adjust emotion, pace, tone
- **High fidelity** - 48kHz audio output
- **100% local** - runs entirely on your computer
- **Open source** - Apache 2.0 license

## Requirements

- Python 3.10-3.12 ✅ (Aether uses 3.11.9)
- PyTorch 2.5.0+ (need to check)
- CUDA 12.0+ (optional, for GPU acceleration)
- Several GB disk space
- voxcpm package

## Installation

### Step 1: Check PyTorch Version

```powershell
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -c "import torch; print(torch.__version__)"
```

If version < 2.5.0, upgrade:
```powershell
.venv\Scripts\pip.exe install --upgrade torch torchaudio
```

### Step 2: Install VoxCPM

```powershell
cd D:\hive\assistant\planner
.venv\Scripts\pip.exe install voxcpm
```

Or install with optional dependencies:
```powershell
.venv\Scripts\pip.exe install -e ".[voxcpm]"
```

### Step 3: Configure Aether

Edit `.env` file:
```env
# Use VoxCPM for TTS
AETHER_TTS_ENGINE=tts_voxcpm

# Choose model (VoxCPM2 for best quality, VoxCPM-0.5B for speed)
AETHER_TTS_VOICE_MODEL=openbmb/VoxCPM2
```

## Usage Modes

### Mode 1: Default Voice (Easiest)

Just set the engine and model:
```env
AETHER_TTS_ENGINE=tts_voxcpm
AETHER_TTS_VOICE_MODEL=openbmb/VoxCPM2
```

VoxCPM will use its built-in voice.

### Mode 2: Voice Cloning (Advanced)

Clone your voice or someone else's voice:

1. **Record a reference audio** (10-30 seconds is enough)
2. **Save as WAV file** (e.g., `my_voice.wav`)
3. **Configure Aether:**
```env
AETHER_TTS_ENGINE=tts_voxcpm
AETHER_TTS_VOICE_MODEL=openbmb/VoxCPM2
AETHER_TTS_VOICE_CLONE=C:\path\to\my_voice.wav
```

Aether will now speak in the cloned voice!

### Mode 3: Voice Design (Creative)

Create a voice from text description:

```env
AETHER_TTS_ENGINE=tts_voxcpm
AETHER_TTS_VOICE_MODEL=openbmb/VoxCPM2
AETHER_TTS_VOICE_DESCRIPTION="A young woman, gentle and warm"
```

**Example descriptions:**
- "A deep male voice, authoritative"
- "A cheerful, energetic voice"
- "A calm, soothing voice for meditation"
- "A robotic, monotone voice"
- "An elderly grandfather, kind and wise"

### Mode 4: Voice Cloning with Style Control

Combine cloning with style control:

```env
AETHER_TTS_ENGINE=tts_voxcpm
AETHER_TTS_VOICE_MODEL=openbmb/VoxCPM2
AETHER_TTS_VOICE_CLONE=C:\path\to\my_voice.wav
AETHER_TTS_VOICE_DESCRIPTION="(slightly faster, cheerful tone)"
```

This preserves the voice timbre but adjusts the style.

## Model Comparison

| Model | Parameters | Quality | Speed | Size |
|-------|-----------|---------|-------|------|
| VoxCPM2 | 2B | Best | Slower | ~4GB |
| VoxCPM-0.5B | 0.5B | Good | Faster | ~1GB |

**Recommendation:**
- Use **VoxCPM-0.5B** for faster response
- Use **VoxCPM2** for best quality (if you have GPU)

## Testing

### Test VoxCPM Installation

```powershell
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.tts_voxcpm list
```

### Test Speech

```powershell
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.tts_voxcpm
```

This will speak "Hello, this is a test of VoxCPM text to speech."

### Test with Aether

1. Configure `.env` with VoxCPM settings
2. Start Aether:
```powershell
.venv\Scripts\python.exe -m assistant.core.tray_app
```
3. Say "Computer" and ask a question
4. Aether will respond with VoxCPM voice

## Switching Between Engines

### Use SAPI5 (Windows Default, Fast)

```env
AETHER_TTS_ENGINE=tts_sapi5
AETHER_TTS_VOICE=Microsoft Zira Desktop
AETHER_TTS_RATE=180
```

### Use VoxCPM (Advanced, Voice Cloning)

```env
AETHER_TTS_ENGINE=tts_voxcpm
AETHER_TTS_VOICE_MODEL=openbmb/VoxCPM-0.5B
```

## Troubleshooting

### Import Error: No module named 'voxcpm'

**Solution:** Install VoxCPM:
```powershell
.venv\Scripts\pip.exe install voxcpm
```

### PyTorch Version Too Old

**Solution:** Upgrade PyTorch:
```powershell
.venv\Scripts\pip.exe install --upgrade torch torchaudio
```

### Model Download Fails

**Solution:** Check internet connection. Models are downloaded from Hugging Face on first run.

### Out of Memory

**Solution:** Use smaller model:
```env
AETHER_TTS_VOICE_MODEL=openbmb/VoxCPM-0.5B
```

Or close other applications.

### Slow Response

**Solution:** 
- Use smaller model (VoxCPM-0.5B)
- Enable GPU acceleration (CUDA 12.0+)
- Reduce inference_timesteps in code (advanced)

## Voice Cloning Tips

### Reference Audio Requirements

- **Duration:** 10-30 seconds is ideal
- **Quality:** Clear speech, minimal background noise
- **Format:** WAV, 16kHz or higher sample rate
- **Content:** Varied speech for better cloning

### Best Practices

1. **Use clear speech** - no mumbling
2. **Minimize noise** - quiet environment
3. **Varied pitch** - helps capture voice characteristics
4. **Consistent tone** - don't mix emotions

### Privacy Note

Voice cloning is powerful technology. Always:
- Only clone voices you have permission to use
- Clearly mark AI-generated content
- Don't use for impersonation or fraud
- Respect privacy and consent

## Performance Tips

### For Best Speed

1. Use VoxCPM-0.5B model
2. Enable GPU acceleration (CUDA)
3. Close unnecessary applications
4. Use SSD for model storage

### For Best Quality

1. Use VoxCPM2 model
2. Use high-quality reference audio for cloning
3. Enable denoiser (set load_denoiser=True)
4. Use voice design for precise control

## Advanced: Ultimate Cloning

For maximum fidelity, provide both reference audio AND its exact transcript:

```python
# This is advanced usage, requires code modification
wav = model.generate(
    text="This is an ultimate cloning demonstration.",
    prompt_wav_path="speaker_reference.wav",
    prompt_text="The exact transcript of the reference audio.",
    reference_wav_path="speaker_reference.wav",
)
```

This preserves every vocal nuance for near-perfect cloning.

## Future Enhancements

Potential future additions:
- Multiple voice profiles (switch between voices)
- Emotion detection and matching
- Real-time voice conversion
- Voice training from longer samples
- Integration with LLM for voice style suggestions

## Summary

**VoxCPM Integration:**
- ✅ 30 languages support
- ✅ Voice cloning capabilities
- ✅ Voice design from text
- ✅ Controllable style
- ✅ 100% local
- ✅ Open source

**To Use:**
1. Install: `pip install voxcpm`
2. Configure: `AETHER_TTS_ENGINE=tts_voxcpm`
3. Choose model: `AETHER_TTS_VOICE_MODEL=openbmb/VoxCPM-0.5B`
4. (Optional) Add voice cloning or design
5. Start Aether

**VoxCPM is a significant upgrade from Windows SAPI5, offering professional-quality TTS with advanced voice control!** 🎙️
