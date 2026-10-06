# Aether User Guide

## Welcome to Aether

Aether is a privacy-first, AI-powered desktop assistant that runs entirely on your computer. It helps you with tasks, answers questions, writes code, and automates your workflow - all without sending your data to the cloud.

## Quick Start

### First Time Setup

1. **Run the setup script:**
   ```powershell
   python setup.py
   ```
   This will check your system and install all dependencies automatically.

2. **Start Ollama:**
   ```powershell
   ollama serve
   ```
   Keep this window open.

3. **Start the Planner:**
   ```powershell
   cd assistant\planner
   .venv\Scripts\python.exe -m assistant.core.listener
   ```
   Keep this window open.

4. **Start the Wake Listener:**
   ```powershell
   .venv\Scripts\python.exe -m assistant.core.wake
   ```

5. **Start talking!**
   - Say "Computer" or "Hey Computer" to activate
   - Or press `Win+Alt+A` (if hotkey mode is enabled)

## Daily Use

### Starting Aether

**Option 1: Wake Word**
1. Start the wake listener (as above)
2. Say "Computer" or "Hey Computer"
3. Aether will chime and start listening

**Option 2: Hotkey**
1. Enable hotkey mode:
   ```powershell
   set AETHER_ENABLE_HOTKEY=1
   ```
2. Start the wake listener
3. Press `Win+Alt+A` to activate

### Conversation Mode

Once activated, Aether stays in conversation mode and continues listening until you say:
- "That's all"
- "Done"
- "Thank you"
- "Stop listening"
- "Stop"

You can ask multiple questions without repeating the wake word!

## What Can Aether Do?

### Information & Questions
- "What time is it?"
- "What's the weather?"
- "Tell me about machine learning"
- "How do I fix a leaky faucet?"

### Coding Help
- "Write a Python function to sort a list"
- "Create a C++ program to add two numbers"
- "Generate a JavaScript function for the Fibonacci sequence"

### File Operations
- "Open Notepad"
- "Search for files named 'report'"
- "Delete temporary files"
- "Create a new folder called 'project'"

### Web Search
- "Search for Python tutorials"
- "Find information about climate change"

### Math
- "What is two plus two?"
- "Calculate 15 times 3"
- "What's the square root of 25?"

### System Control
- "Increase volume"
- "Open calculator"
- "Lock my computer"

## Voice Commands Reference

### Wake Words
- "Computer"
- "Hey Computer"

### Exit Phrases
- "That's all"
- "That's it"
- "Done"
- "Thank you"
- "Thanks"
- "Stop listening"
- "Stop"
- "Goodbye"

### Common Commands

**Time & Date:**
- "What time is it?"
- "What's the date?"
- "What day is it?"

**Applications:**
- "Open Notepad"
- "Open calculator"
- "Open Chrome"
- "Close Notepad"

**Files:**
- "Search for files named [name]"
- "Create a new folder"
- "Delete temporary files"
- "Open Documents folder"

**Web:**
- "Search for [query]"
- "Search the web for [topic]"

**Math:**
- "What is [number] plus [number]?"
- "Calculate [expression]"
- "What's [number] times [number]?"

**Coding:**
- "Write a [language] program to [task]"
- "Generate code for [task]"
- "Create a function to [task]"

**Text Entry:**
- "Write [text] in Notepad"
- "Type [text]"
- "Note down [text]"

## Safety & Approvals

Aether protects you by asking for approval before medium and high-risk actions:

### Safe Actions (No approval needed)
- Answering questions
- Web search
- Opening applications
- Time queries
- Math calculations

### Medium Risk (Requires approval)
- File operations
- System changes
- Typing text into applications

### High Risk (Requires approval)
- Deleting multiple files
- System shutdown
- Large file operations

You can approve actions by:
- Voice: Say "yes" or "approve"
- Dialog: Click "Approve" in the popup

## Troubleshooting

### "No working microphone found"
**Solution:**
1. Check if your microphone is connected
2. Go to Settings > System > Sound > Input
3. Set your microphone as default
4. Restart the wake listener

**Alternative:** Use hotkey mode instead (no microphone needed)

### "Ollama is not running"
**Solution:**
1. Start Ollama: `ollama serve`
2. Keep this window open
3. Restart the planner

### "Port 48100 is already in use"
**Solution:**
1. Another instance of Aether is running
2. Close the other terminal
3. Or kill the process:
   ```powershell
   netstat -ano | findstr :48100
   taskkill /PID <PID> /F
   ```

### Audio driver error
**Solution:**
1. Open Device Manager (Win+X → Device Manager)
2. Expand "Sound, video and game controllers"
3. Right-click your audio device → Uninstall
4. Restart your computer
5. Windows will reinstall the driver

**Alternative:** Use hotkey mode

### Aether doesn't respond
**Solution:**
1. Make sure the planner is running
2. Make sure the wake listener is running
3. Make sure Ollama is running
4. Check that you said the wake word clearly
5. Try the hotkey instead: `Win+Alt+A`

### Speech recognition is poor
**Solution:**
1. Speak clearly and at a normal pace
2. Reduce background noise
3. Move closer to the microphone
4. Check your microphone settings
5. Try using a different microphone

## Tips for Better Experience

1. **Speak clearly** - Enunciate words, especially for technical terms
2. **Minimize noise** - Reduce background noise for better recognition
3. **Use natural language** - Aether understands conversational commands
4. **Be specific** - Detailed commands get better results
5. **Use conversation mode** - Ask follow-up questions without repeating the wake word
6. **Check approvals** - Review what Aether plans to do before approving

## Keyboard Shortcuts

- `Win+Alt+A` - Activate Aether (if hotkey mode enabled)
- `Ctrl+C` - Stop any Aether process

## Advanced Features

### Hotkey Mode
Enable hotkey mode to use keyboard instead of wake word:
```powershell
set AETHER_ENABLE_HOTKEY=1
```

### Continuous Listening
Aether stays in conversation mode by default. To add a timeout:
```powershell
set AETHER_CONVERSATION_TIMEOUT=10
```
(This sets a 10-second timeout)

### Custom Hotkey
Change the hotkey combination:
```powershell
set AETHER_HOTKEY=ctrl+shift+a
```

## Privacy

Aether is designed with privacy in mind:
- All processing happens on your computer
- No data is sent to the cloud
- Your conversations are stored locally
- You can delete your data at any time

## System Requirements

**Minimum:**
- Windows 10 or 11
- 8 GB RAM
- 10 GB free disk space
- Python 3.11 or later
- Microphone (or use hotkey mode)

**Recommended:**
- 16 GB RAM
- 20 GB free disk space
- Good quality microphone

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Check the logs in the terminal windows
3. Visit the GitHub repository for known issues
4. Report bugs with details about your system and the error

## Updates

To update Aether:
1. Pull the latest changes from GitHub
2. Run `python setup.py` again
3. Restart all Aether processes

## Uninstalling

To completely remove Aether:
1. Stop all Aether processes
2. Delete the `D:\hive` folder
3. Uninstall Ollama (if desired)
4. Delete any desktop shortcuts

## Thank You

Thank you for using Aether! We hope it helps you be more productive while keeping your data private.

For the latest updates and documentation, visit the GitHub repository.
