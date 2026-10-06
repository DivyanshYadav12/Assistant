@echo off
REM Download required Ollama models for Aether

echo Downloading Aether models...
echo This may take several minutes and requires ~6GB of disk space.
echo.

cd /d "%~dp0"

REM Download fast model for routing
echo [1/3] Downloading qwen2.5:1.5b-instruct (fast model)...
ollama pull qwen2.5:1.5b-instruct
if errorlevel 1 (
    echo ERROR: Failed to download qwen2.5:1.5b-instruct
    pause
    exit /b 1
)

REM Download smart model for conversation
echo [2/3] Downloading llama3:8b (smart model)...
ollama pull llama3:8b
if errorlevel 1 (
    echo ERROR: Failed to download llama3:8b
    pause
    exit /b 1
)

REM Download embedding model
echo [3/3] Downloading nomic-embed-text (embedding model)...
ollama pull nomic-embed-text
if errorlevel 1 (
    echo ERROR: Failed to download nomic-embed-text
    pause
    exit /b 1
)

echo.
echo ============================================
echo All models downloaded successfully!
echo ============================================
echo.
echo Models installed:
echo - qwen2.5:1.5b-instruct (fast routing)
echo - llama3:8b (smart conversation)
echo - nomic-embed-text (embeddings)
echo.
echo You can now start using Aether!
echo.
pause
