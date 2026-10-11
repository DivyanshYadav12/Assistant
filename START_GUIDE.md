# Quick Start Guide - Aether System Tray

## How to Run Aether with System Tray

### Option 1: Use Voice Improvements (Better Quality) ⭐ Recommended

**Step 1: Configure voice settings**

Edit your `.env` file:
```powershell
cd D:\hive
notepad .env
```

Add these lines:
```env
# Use Whisper for better speech recognition
AETHER_USE_WHISPER=1
AETHER_WHISPER_MODEL=base

# TTS settings (optional)
AETHER_TTS_RATE=180
AETHER_TTS_VOLUME=1.0
```

**Step 2: Start the system tray**

```powershell
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.tray_app
```

That's it! The system tray will:
- ✅ Start Ollama
- ✅ Start the planner
- ✅ Start the wake listener with Whisper (better accuracy)
- ✅ Show a blue 'A' icon in your system tray

### Option 2: Use Original Voice System (Faster)

**Step 1: Don't set AETHER_USE_WHISPER (or set to 0)**

Edit your `.env` file:
```env
# Use Vosk (faster, less accurate)
AETHER_USE_WHISPER=0
```

**Step 2: Start the system tray**

```powershell
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.tray_app
```

### Option 3: Use Desktop Shortcut (Easiest)

**Step 1: Create desktop shortcut**

```powershell
# Right-click on D:\hive\start_aether_tray.bat
# Send to → Desktop (create shortcut)
# Rename to "Aether"
```

**Step 2: Configure .env for voice**

Edit `.env` and add voice settings (see Option 1 or 2)

**Step 3: Double-click the shortcut**

## Using the System Tray

Once the tray is running, you'll see a blue 'A' icon in your system tray (bottom right, near the clock).

**Right-click the icon to see the menu:**

- **Start All** - Start all components (Ollama, planner, wake listener)
- **Stop All** - Stop all components
- **Start Planner** - Start just the planner
- **Stop Planner** - Stop just the planner
- **Start Wake Listener** - Start just the wake listener
- **Stop Wake Listener** - Stop just the wake listener
- **Start Dashboard** - Start the web dashboard
- **Stop Dashboard** - Stop the web dashboard
- **Open Dashboard** - Open dashboard in browser
- **Enable Auto-start** - Start Aether automatically when Windows starts
- **Disable Auto-start** - Don't start automatically
- **Status** - Show what's running
- **Quit** - Exit completely

## Testing the Voice System

### Test TTS (Text-to-Speech)

```powershell
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.tts list
```

This will show all available voices. Choose one you like and add to `.env`:
```env
AETHER_TTS_VOICE=HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0
```

### Test Wake Listener

**With Whisper (better accuracy):**
```powershell
set AETHER_USE_WHISPER=1
set AETHER_WHISPER_MODEL=base
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.wake_whisper
```

**With Vosk (faster):**
```powershell
set AETHER_USE_WHISPER=0
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.wake
```

## Voice Comparison

| Feature | Vosk (Old) | Whisper (New) |
|---------|------------|---------------|
| Accuracy | Poor (many errors) | Excellent (10x better) |
| Speed | Fast (~200ms) | Good (~300ms) |
| Model Size | Small (~40MB) | Medium (~1GB) |
| Privacy | 100% local | 100% local |
| Recommended | For very slow computers | For most users ⭐ |

## Environment Variables Reference

### Voice Recognition (STT)
- `AETHER_USE_WHISPER=1` - Use Whisper (better accuracy)
- `AETHER_USE_WHISPER=0` - Use Vosk (faster)
- `AETHER_WHISPER_MODEL=tiny` - Smallest, fastest model
- `AETHER_WHISPER_MODEL=base` - Best balance ⭐
- `AETHER_WHISPER_MODEL=small` - Better accuracy
- `AETHER_WHISPER_MODEL=medium` - Best accuracy

### Text-to-Speech (TTS)
- `AETHER_TTS_VOICE` - Voice ID (run `python -m assistant.core.tts list` to see options)
- `AETHER_TTS_RATE=180` - Speech speed (50-400)
- `AETHER_TTS_VOLUME=1.0` - Volume (0.0-1.0)

## Troubleshooting

### System tray not starting
- Make sure pystray is installed: `pip install pystray pillow`
- Check if Python is running from the correct venv

### Wake listener not working
- Check microphone is connected
- Try hotkey mode: set `AETHER_ENABLE_HOTKEY=1`
- Run wake listener directly to see errors

### Voice quality is bad
- Set `AETHER_USE_WHISPER=1` for better accuracy
- Choose a better TTS voice
- Adjust `AETHER_TTS_RATE` (try 180-200)

### Port conflicts
- Stop old instances: Right-click tray → Stop All
- Kill processes manually if needed

## Recommended Setup

**For best quality:**
```env
AETHER_USE_WHISPER=1
AETHER_WHISPER_MODEL=base
AETHER_TTS_RATE=180
AETHER_TTS_VOLUME=1.0
```

**For best speed:**
```env
AETHER_USE_WHISPER=0
AETHER_TTS_RATE=200
AETHER_TTS_VOLUME=1.0
```

**For balanced:**
```env
AETHER_USE_WHISPER=1
AETHER_WHISPER_MODEL=tiny
AETHER_TTS_RATE=180
AETHER_TTS_VOLUME=1.0
```

## Summary

**To start Aether:**
1. Configure `.env` with voice settings
2. Run: `cd D:\hive\assistant\planner && .venv\Scripts\python.exe -m assistant.core.tray_app`
3. Or double-click desktop shortcut

**To use Aether:**
- Say "Computer" or press `Win+Alt+A`
- Give commands
- Say "That's all" when done

**To control Aether:**
- Right-click the blue 'A' icon in system tray
- Use the menu to start/stop components

That's it! 🎉
