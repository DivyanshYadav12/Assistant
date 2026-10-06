Aether AI Assistant - Installation Guide
========================================

Welcome to Aether, a privacy-first AI desktop assistant!

System Requirements
------------------
- Windows 10 or 11 (64-bit)
- Python 3.11 or later
- 8 GB RAM minimum (16 GB recommended)
- 10 GB free disk space
- Microphone (optional - hotkey mode available)

Installation Steps
-------------------
1. Run Aether-Setup.exe
2. Follow the installation wizard
3. If prompted, install Python 3.11+ from python.org
4. If prompted, install Ollama from ollama.com
5. After installation, click "Start Aether" to begin

First Time Setup
----------------
1. The installer will create a virtual environment
2. It will install Python dependencies
3. It will check if Ollama is running
4. It will start the planner and wake listener

Starting Aether
----------------
Option 1: Desktop Shortcut
- Double-click the Aether icon on your desktop

Option 2: Start Menu
- Click Start > Aether > Start Aether

Option 3: System Tray
- Right-click the Aether icon in the system tray
- Select "Start All"

Using Aether
------------
- Wake Word: Say "Computer" or "Hey Computer"
- Hotkey: Press Win+Alt+A
- Dashboard: Open http://127.0.0.1:8001 in your browser

Voice Commands
--------------
- "What time is it?"
- "Open Notepad"
- "Search for files named report"
- "Write a Python program to add two numbers"
- "What is machine learning?"
- "That's all" (to stop listening)

Troubleshooting
---------------
Problem: "No working microphone found"
Solution: Check your microphone settings in Windows Sound settings
Alternative: Use hotkey mode (Win+Alt+A)

Problem: "Ollama is not running"
Solution: Run: ollama serve
Or start it from the system tray menu

Problem: "Port 48100 is already in use"
Solution: Another instance of Aether is running. Close it first.

Problem: Audio driver error
Solution: Update your audio drivers or use hotkey mode

Uninstalling
-----------
1. Go to Settings > Apps > Installed apps
2. Find Aether AI Assistant
3. Click Uninstall
4. Follow the uninstall wizard

Getting Help
------------
- Documentation: Open docs/USER_GUIDE.md
- GitHub: https://github.com/DivyanshYadav12/Assistant
- Issues: Report bugs on GitHub

Privacy
-------
Aether is designed with privacy in mind:
- All processing happens on your computer
- No data is sent to the cloud
- Your conversations are stored locally
- You can delete your data at any time

Thank you for using Aether!
