@echo off
REM Aether Stop Script
REM This script stops all Aether components

echo Stopping Aether AI Assistant...
echo.

REM Kill wake listener
echo Stopping Wake Listener...
taskkill /FI "WINDOWTITLE eq Aether Wake Listener*" /F >nul 2>&1

REM Kill planner
echo Stopping Planner...
taskkill /FI "WINDOWTITLE eq Aether Planner*" /F >nul 2>&1

REM Kill system tray
echo Stopping System Tray...
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Aether*" /F >nul 2>&1

REM Optionally stop Ollama (commented out by default)
REM echo Stopping Ollama...
REM taskkill /IM ollama.exe /F >nul 2>&1

echo.
echo Aether components stopped.
echo.
echo Note: Ollama may still be running. To stop it, run: ollama stop
echo.
pause
