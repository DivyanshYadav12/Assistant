@echo off
REM Aether Startup Script
REM This script starts all Aether components

echo Starting Aether AI Assistant...
echo.

REM Change to Aether directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Install dependencies if needed
echo Installing dependencies...
.venv\Scripts\pip.exe install -e . --quiet
if errorlevel 1 (
    echo WARNING: Some dependencies may not have installed correctly
)

REM Check if Ollama is running
echo Checking Ollama...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Starting Ollama...
    start "" ollama serve
    echo Waiting for Ollama to start...
    timeout /t 5 /nobreak >nul
)

REM Start the planner in a new window
echo Starting Planner...
start "Aether Planner" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m assistant.core.listener"

REM Wait for planner to start
echo Waiting for Planner to initialize...
timeout /t 3 /nobreak >nul

REM Start the wake listener in a new window
echo Starting Wake Listener...
start "Aether Wake Listener" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m assistant.core.wake"

REM Start the system tray (if available)
if exist "src\assistant\core\tray_app.py" (
    echo Starting System Tray...
    start "" .venv\Scripts\python.exe src\assistant\core\tray_app.py
)

echo.
echo ============================================
echo Aether is now running!
echo ============================================
echo.
echo Wake Word: Say "Computer" or "Hey Computer"
echo Hotkey: Press Win+Alt+A (if enabled)
echo Dashboard: http://127.0.0.1:8001
echo.
echo Press any key to close this window...
pause >nul
