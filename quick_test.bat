@echo off
REM Quick Test Script for Aether
REM Tests the most important features quickly

echo ============================================
echo Aether Quick Test Suite
echo ============================================
echo.

REM Test 1: Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found
    goto :error
)
echo [PASS] Python installed
python --version
echo.

REM Test 2: Check Virtual Environment
echo [2/5] Checking virtual environment...
cd /d D:\hive\assistant\planner
if not exist ".venv\Scripts\python.exe" (
    echo [FAIL] Virtual environment not found
    echo Run: python -m venv .venv
    goto :error
)
echo [PASS] Virtual environment exists
echo.

REM Test 3: Check Dependencies
echo [3/5] Checking dependencies...
.venv\Scripts\python.exe -c "import structlog" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Dependencies not installed
    echo Run: .venv\Scripts\pip.exe install -e .
    goto :error
)
echo [PASS] Dependencies installed
echo.

REM Test 4: Check Ollama
echo [4/5] Checking Ollama...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama not running
    echo Start Ollama with: ollama serve
) else (
    echo [PASS] Ollama is running
)
echo.

REM Test 5: Check Models
echo [5/5] Checking Ollama models...
ollama list >nul 2>&1
if errorlevel 1 (
    echo [WARN] Cannot check models (Ollama not running)
) else (
    ollama list | findstr "qwen2.5" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] qwen2.5:1.5b-instruct not found
        echo Run: ollama pull qwen2.5:1.5b-instruct
    ) else (
        echo [PASS] qwen2.5:1.5b-instruct installed
    )
    
    ollama list | findstr "llama3:8b" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] llama3:8b not found
        echo Run: ollama pull llama3:8b
    ) else (
        echo [PASS] llama3:8b installed
    )
    
    ollama list | findstr "nomic-embed" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] nomic-embed-text not found
        echo Run: ollama pull nomic-embed-text
    ) else (
        echo [PASS] nomic-embed-text installed
    )
)
echo.

echo ============================================
echo Quick Test Complete
echo ============================================
echo.
echo For full testing, see TESTING_GUIDE.md
echo.
echo To start Aether:
echo   1. Start Ollama: ollama serve
echo   2. Start planner: .venv\Scripts\python.exe -m assistant.core.listener
echo   3. Start wake: .venv\Scripts\python.exe -m assistant.core.wake
echo.
echo Or use system tray:
echo   .venv\Scripts\python.exe -m assistant.core.tray_app
echo.
pause
goto :end

:error
echo.
echo ============================================
echo TEST FAILED
echo ============================================
echo.
echo Please fix the errors above before continuing.
echo.
pause
exit /b 1

:end
