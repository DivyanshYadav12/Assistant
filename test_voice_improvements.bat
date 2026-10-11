@echo off
REM Test voice improvements

echo ========================================
echo Testing Voice Improvements
echo ========================================
echo.

echo [1/3] Testing TTS voice listing...
cd /d D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.tts list
echo.

echo [2/3] Testing TTS speech...
echo "Testing TTS with default voice..."
.venv\Scripts\python.exe -m assistant.core.tts
echo.

echo [3/3] Checking Whisper model download...
echo "Note: Whisper model will download on first run of wake_whisper.py"
echo "Model sizes:"
echo "  tiny: ~400MB (fastest, good accuracy)"
echo "  base: ~1GB (balanced)"
echo "  small: ~1.5GB (better accuracy)"
echo "  medium: ~3GB (best accuracy)"
echo.

echo ========================================
echo To test Whisper STT, run:
echo   set AETHER_WHISPER_MODEL=base
echo   .venv\Scripts\python.exe -m assistant.core.wake_whisper
echo ========================================
echo.

pause
