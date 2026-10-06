@echo off
REM Aether System Tray Launcher
REM Double-click this to start Aether with system tray control

cd /d D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.tray_app
