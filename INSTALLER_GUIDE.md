# Aether Production Installation Guide

## Overview

Aether now has a production-ready installation system with:
- ✅ System tray application for easy control
- ✅ Windows installer (Inno Setup)
- ✅ Auto-start on boot option
- ✅ One-click startup scripts
- ✅ Model download helper

## New Components

### 1. System Tray Application (`tray_app.py`)

**Location:** `assistant/planner/src/assistant/core/tray_app.py`

**Features:**
- Start/stop all Aether components from system tray
- Individual control of planner, wake listener, and Ollama
- Open dashboard in browser
- Enable/disable auto-start on boot
- Status display
- Custom blue icon with 'A' logo

**How to Use:**
```powershell
cd D:\hive\assistant\planner
.venv\Scripts\python.exe -m assistant.core.tray_app
```

**Dependencies:** (already added to pyproject.toml)
- pystray
- pillow

### 2. Windows Installer (`aether_setup.iss`)

**Location:** `installer/aether_setup.iss`

**Features:**
- Professional installer wizard
- Checks for Python installation
- Checks for Ollama installation
- Offers to download missing dependencies
- Creates desktop and quick launch icons
- Auto-start on boot option
- Clean uninstallation

**How to Build:**
1. Download Inno Setup from: https://jrsoftware.org/isdl.php
2. Open `aether_setup.iss` in Inno Setup Compiler
3. Click "Compile"
4. Output: `installer\Output\Aether-Setup.exe`

**What Gets Installed:**
- All source files
- Documentation
- Start/stop scripts
- Desktop icons
- Start menu shortcuts

### 3. Startup Scripts

**start_aether.bat**
- Checks Python installation
- Creates virtual environment if needed
- Installs dependencies
- Starts Ollama if not running
- Starts planner and wake listener
- Starts system tray
- Shows status and instructions

**stop_aether.bat**
- Stops all Aether components
- Clean shutdown

**download_models.bat**
- Downloads qwen2.5:1.5b-instruct (fast model)
- Downloads llama3:8b (smart model)
- Downloads nomic-embed-text (embeddings)
- ~6GB total size

### 4. Auto-Start on Boot

**Enabled via:**
- System tray menu: "Enable Auto-start"
- Installer option during setup
- Windows Registry: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`

**Disabled via:**
- System tray menu: "Disable Auto-start"
- Uninstaller removes registry entry

## Installation Process

### Option 1: Using the Installer (Recommended for Users)

1. **Build the installer:**
   ```powershell
   # Download Inno Setup first
   # Open aether_setup.iss and compile
   ```

2. **Run the installer:**
   - Double-click `Aether-Setup.exe`
   - Follow the wizard
   - Install to default location or choose custom
   - Select desktop icon and auto-start options

3. **First-time setup:**
   - If prompted, install Python 3.11+
   - If prompted, install Ollama
   - Click "Start Aether" after installation

4. **Download models:**
   - Run `download_models.bat` from installation directory
   - Wait for download (~6GB, may take 10-30 minutes)

5. **Start using Aether:**
   - Use desktop shortcut
   - Or use system tray icon
   - Say "Computer" or press Win+Alt+A

### Option 2: Manual Installation (For Developers)

1. **Clone repository:**
   ```powershell
   git clone https://github.com/DivyanshYadav12/Assistant.git
   cd Assistant
   ```

2. **Run setup script:**
   ```powershell
   python setup.py
   ```

3. **Download models:**
   ```powershell
   ollama pull qwen2.5:1.5b-instruct
   ollama pull llama3:8b
   ollama pull nomic-embed-text
   ```

4. **Start components:**
   ```powershell
   # Terminal 1: Start Ollama
   ollama serve

   # Terminal 2: Start planner
   cd assistant\planner
   .venv\Scripts\python.exe -m assistant.core.listener

   # Terminal 3: Start wake listener
   .venv\Scripts\python.exe -m assistant.core.wake

   # Terminal 4: Start system tray (optional)
   .venv\Scripts\python.exe -m assistant.core.tray_app
   ```

## System Tray Usage

### Menu Options

**Start/Stop Controls:**
- Start All - Starts all components
- Stop All - Stops all components
- Start Planner - Starts only the planner
- Stop Planner - Stops the planner
- Start Wake Listener - Starts wake word detection
- Stop Wake Listener - Stops wake word detection

**Dashboard:**
- Open Dashboard - Opens web interface at http://127.0.0.1:8001

**Auto-Start:**
- Enable Auto-start - Adds to Windows startup
- Disable Auto-start - Removes from Windows startup

**Other:**
- Status - Shows running status of all components
- Quit - Exits the tray application

### Icon States

- **Blue circle with 'A'** - Normal operation
- **Grayed out** - Components stopped
- **Red indicator** (future) - Error state

## File Structure After Installation

```
C:\Program Files\Aether\
├── src/
│   └── assistant/
│       ├── core/
│       │   ├── listener.py
│       │   ├── wake.py
│       │   ├── tray_app.py
│       │   └── ...
│       └── skills/
├── docs/
│   ├── USER_GUIDE.md
│   ├── COMMANDS.md
│   └── MODEL_SETUP.md
├── .env
├── pyproject.toml
├── start_aether.bat
├── stop_aether.bat
├── download_models.bat
├── aether.ico
├── LICENSE.txt
└── README.txt
```

## Updating the Installer

When making changes to Aether:

1. **Update version in `aether_setup.iss`:**
   ```iss
   AppVersion=1.0.1
   ```

2. **Rebuild the installer:**
   - Open in Inno Setup
   - Click "Compile"

3. **Test the installer:**
   - Run on clean Windows system
   - Verify all components work
   - Test uninstallation

## Troubleshooting

### Installer Won't Compile

**Problem:** Inno Setup not installed
**Solution:** Download from https://jrsoftware.org/isdl.php

### System Tray Won't Start

**Problem:** pystray or pillow not installed
**Solution:**
```powershell
.venv\Scripts\pip.exe install pystray pillow
```

### Auto-Start Not Working

**Problem:** Registry entry not created
**Solution:**
- Run as administrator
- Check Registry Editor at:
  `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`

### Models Won't Download

**Problem:** Ollama not running or no internet
**Solution:**
- Run `ollama serve` first
- Check internet connection
- Try downloading models manually

## Next Steps for Production

### Still Needed:

1. **Bundled Python** - Don't require users to install Python
   - Use PyInstaller to create standalone executables
   - Reduces installation complexity

2. **Model Quantization** - Reduce model size
   - Use 4-bit quantization (llama3:8b → ~2GB)
   - Reduces download time and disk space

3. **Crash Reporting** - Track and fix issues
   - Add error logging
   - Add crash dump collection
   - Add automatic error reporting

4. **Auto-Updates** - Keep Aether updated
   - Add update checker
   - Add auto-download and install
   - Notify users of updates

5. **Configuration GUI** - No more .env editing
   - Add settings dialog
   - Add model selection
   - Add audio device selection

## Summary

✅ **Completed High Priority Tasks:**
- System tray application with full control
- Windows installer with dependency checking
- Auto-start on boot option
- One-click startup/stop scripts
- Model download helper

🎯 **Production Readiness: 80%**

The installer and system tray make Aether much more user-friendly. Users can now:
- Install with a double-click
- Start/stop from system tray
- Auto-start with Windows
- Use desktop shortcuts

Still needed for 100% production readiness:
- Bundled Python (no external dependency)
- Quantized models (smaller download)
- Crash reporting (better support)
- Auto-updates (easier maintenance)
