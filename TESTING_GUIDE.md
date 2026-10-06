# Aether Testing Guide

Complete step-by-step testing instructions for all new features.

## Pre-Testing Checklist

Before testing, ensure you have:
- [ ] Python 3.11+ installed
- [ ] Ollama installed and models downloaded
- [ ] Virtual environment created
- [ ] All dependencies installed

## Test 1: Enhanced Error Handling

### Test Audio Driver Fallback

**Steps:**
1. Open a terminal
2. Navigate to planner directory:
   ```powershell
   cd D:\hive\assistant\planner
   ```
3. Start the wake listener:
   ```powershell
   .venv\Scripts\python.exe -m assistant.core.wake
   ```

**Expected Results:**
- ✅ Shows "Aether Wake Word Listener" header
- ✅ Checks audio devices
- ✅ Shows "✓ Microphone found (device X)"
- ✅ Shows "✓ Speech recognition model loaded"
- ✅ Shows configuration details
- ✅ Displays "Aether is listening! Say 'Computer' to start."

**If Microphone Fails:**
- ✅ Shows "❌ ERROR: No working microphone found!"
- ✅ Provides clear solutions
- ✅ Suggests hotkey mode as alternative
- ✅ Waits for user input before exiting

### Test Port Conflict Detection

**Steps:**
1. Start the planner in one terminal:
   ```powershell
   cd D:\hive\assistant\planner
   .venv\Scripts\python.exe -m assistant.core.listener
   ```

2. Try to start another planner in a different terminal:
   ```powershell
   cd D:\hive\assistant\planner
   .venv\Scripts\python.exe -m assistant.core.listener
   ```

**Expected Results:**
- ✅ Second planner shows "❌ ERROR: Port 48100 is already in use!"
- ✅ Shows instructions to find and kill the process
- ✅ Suggests closing the other terminal
- ✅ Waits for user input before exiting

### Test Ollama Detection

**Steps:**
1. Stop Ollama if running (Ctrl+C in Ollama terminal)
2. Start the planner:
   ```powershell
   cd D:\hive\assistant\planner
   .venv\Scripts\python.exe -m assistant.core.listener
   ```

**Expected Results:**
- ✅ Shows "❌ ERROR: Ollama is not running!"
- ✅ Provides instructions to start Ollama
- ✅ Suggests downloading Ollama if not installed
- ✅ Waits for user input before exiting

## Test 2: System Tray Application

### Test Tray Installation

**Steps:**
1. Install tray dependencies:
   ```powershell
   cd D:\hive\assistant\planner
   .venv\Scripts\pip.exe install pystray pillow
   ```

2. Start the tray app:
   ```powershell
   .venv\Scripts\python.exe -m assistant.core.tray_app
   ```

**Expected Results:**
- ✅ Shows "Starting Aether components..."
- ✅ Starts Ollama (if not running)
- ✅ Starts planner
- ✅ Starts wake listener
- ✅ Shows "Aether system tray started"
- ✅ Blue icon with 'A' appears in system tray

### Test Tray Menu Options

**Steps:**
1. Right-click the Aether tray icon
2. Test each menu option:

**Test "Status":**
- ✅ Shows status of Ollama, Planner, and Wake listener
- ✅ Shows "Running" or "Stopped" for each component

**Test "Stop All":**
- ✅ Stops wake listener
- ✅ Stops planner
- ✅ Stops Ollama
- ✅ Shows confirmation messages

**Test "Start All":**
- ✅ Starts Ollama
- ✅ Starts planner
- ✅ Starts wake listener
- ✅ Shows confirmation messages

**Test "Start Planner" / "Stop Planner":**
- ✅ Individually controls planner
- ✅ Other components unaffected

**Test "Start Wake Listener" / "Stop Wake Listener":**
- ✅ Individually controls wake listener
- ✅ Other components unaffected

**Test "Open Dashboard":**
- ✅ Opens browser to http://127.0.0.1:8001
- ✅ Dashboard loads (if backend is running)

**Test "Enable Auto-start":**
- ✅ Shows "Auto-start enabled"
- ✅ Check Registry: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- ✅ "Aether" entry exists

**Test "Disable Auto-start":**
- ✅ Shows "Auto-start disabled"
- ✅ Registry entry removed

**Test "Quit":**
- ✅ Stops all components
- ✅ Tray icon disappears
- ✅ Shows "Exiting Aether..."

## Test 3: Startup Scripts

### Test start_aether.bat

**Steps:**
1. Copy scripts to planner directory:
   ```powershell
   copy D:\hive\installer\start_aether.bat D:\hive\assistant\planner\
   copy D:\hive\installer\stop_aether.bat D:\hive\assistant\planner\
   ```

2. Stop any running Aether components first

3. Run the startup script:
   ```powershell
   cd D:\hive\assistant\planner
   start_aether.bat
   ```

**Expected Results:**
- ✅ Shows "Starting Aether AI Assistant..."
- ✅ Checks Python installation
- ✅ Checks virtual environment
- ✅ Installs dependencies (if needed)
- ✅ Checks Ollama
- ✅ Starts Ollama (if not running)
- ✅ Opens "Aether Planner" window
- ✅ Opens "Aether Wake Listener" window
- ✅ Starts system tray (if available)
- ✅ Shows "Aether is now running!"
- ✅ Shows wake word and hotkey instructions
- ✅ Shows dashboard URL

### Test stop_aether.bat

**Steps:**
1. With Aether running, run:
   ```powershell
   cd D:\hive\assistant\planner
   stop_aether.bat
   ```

**Expected Results:**
- ✅ Shows "Stopping Aether AI Assistant..."
- ✅ Closes "Aether Wake Listener" window
- ✅ Closes "Aether Planner" window
- ✅ Closes system tray
- ✅ Shows "Aether components stopped"
- ✅ Notes that Ollama may still be running

## Test 4: Model Download Script

### Test download_models.bat

**Steps:**
1. Copy script to planner directory:
   ```powershell
   copy D:\hive\installer\download_models.bat D:\hive\assistant\planner\
   ```

2. Ensure Ollama is running:
   ```powershell
   ollama serve
   ```

3. In another terminal, run:
   ```powershell
   cd D:\hive\assistant\planner
   download_models.bat
   ```

**Expected Results:**
- ✅ Shows "Downloading Aether models..."
- ✅ Shows size warning (~6GB)
- ✅ Shows "[1/3] Downloading qwen2.5:1.5b-instruct..."
- ✅ Downloads successfully
- ✅ Shows "[2/3] Downloading llama3:8b..."
- ✅ Downloads successfully
- ✅ Shows "[3/3] Downloading nomic-embed-text..."
- ✅ Downloads successfully
- ✅ Shows "All models downloaded successfully!"
- ✅ Lists all installed models

**To verify models:**
```powershell
ollama list
```
Should show:
- qwen2.5:1.5b-instruct
- llama3:8b
- nomic-embed-text

## Test 5: One-Click Setup Script

### Test setup.py

**Steps:**
1. Stop all Aether components
2. Navigate to project root:
   ```powershell
   cd D:\hive
   ```

3. Run the setup script:
   ```powershell
   python setup.py
   ```

**Expected Results:**
- ✅ Shows "Aether One-Click Setup" header
- ✅ Checks Python version
- ✅ Shows "✓ Python 3.11+ installed" (or error if not)
- ✅ Checks RAM
- ✅ Shows "✓ X GB RAM detected"
- ✅ Checks disk space
- ✅ Shows "✓ X GB free space"
- ✅ Checks Ollama
- ✅ Shows "✓ Ollama is running" (or warning if not)
- ✅ Installs Python dependencies
- ✅ Shows "✓ Dependencies installed"
- ✅ Asks about downloading models
- ✅ Creates desktop shortcuts (if yes to models)
- ✅ Shows setup complete message
- ✅ Shows startup instructions

## Test 6: Full Integration Test

### Test Complete Workflow

**Steps:**
1. **Clean start:** Stop all Aether components

2. **Start with tray:**
   ```powershell
   cd D:\hive\assistant\planner
   .venv\Scripts\python.exe -m assistant.core.tray_app
   ```

3. **Verify components:**
   - Right-click tray icon → Status
   - All should show "Running"

4. **Test voice activation:**
   - Say "Computer"
   - Should hear chime
   - Should see "(Listening...)"
   - Say "What time is it?"
   - Should get spoken response

5. **Test conversation mode:**
   - Without wake word, ask "What's the weather?"
   - Should get response
   - Ask "What is AI?"
   - Should get response
   - Say "That's all"
   - Should show "(Conversation mode ended)"

6. **Test hotkey (if enabled):**
   - Press Win+Alt+A
   - Should hear chime
   - Say "Open Notepad"
   - Notepad should open

7. **Test dashboard:**
   - Right-click tray → Open Dashboard
   - Browser should open to http://127.0.0.1:8001
   - Dashboard should load

8. **Test auto-start:**
   - Right-click tray → Enable Auto-start
   - Check Registry Editor
   - Verify entry exists
   - Disable auto-start
   - Verify entry removed

9. **Clean shutdown:**
   - Right-click tray → Stop All
   - All components should stop
   - Right-click tray → Quit
   - Tray icon should disappear

## Test 7: Error Recovery

### Test Microphone Failure Recovery

**Steps:**
1. Disconnect your microphone
2. Start wake listener:
   ```powershell
   .venv\Scripts\python.exe -m assistant.core.wake
   ```

**Expected Results:**
- ✅ Shows microphone error
- ✅ Provides clear error message
- ✅ Suggests solutions
- ✅ Suggests hotkey mode

3. Reconnect microphone
4. Restart wake listener
5. Should work normally

### Test Ollama Failure Recovery

**Steps:**
1. Stop Ollama
2. Start planner:
   ```powershell
   .venv\Scripts\python.exe -m assistant.core.listener
   ```

**Expected Results:**
- ✅ Shows Ollama not running error
- ✅ Provides instructions
- ✅ Exits gracefully

3. Start Ollama
4. Restart planner
5. Should work normally

## Test 8: Documentation

### Test User Guide

**Steps:**
1. Open `assistant/docs/USER_GUIDE.md`
2. Read through sections

**Verify:**
- ✅ Clear instructions
- ✅ Comprehensive troubleshooting
- ✅ Voice commands reference
- ✅ System requirements
- ✅ Tips for better experience

### Test Installer Guide

**Steps:**
1. Open `INSTALLER_GUIDE.md`
2. Read through sections

**Verify:**
- ✅ Installation instructions
- ✅ System tray usage
- ✅ Troubleshooting
- ✅ File structure
- ✅ Update instructions

## Test 9: Production Build

### Test Frontend Build

**Steps:**
1. Navigate to frontend:
   ```powershell
   cd D:\hive\assistant\dashboard\frontend
   ```

2. Build production version:
   ```powershell
   npm run build
   ```

**Expected Results:**
- ✅ No TypeScript errors
- ✅ Builds successfully
- ✅ Creates `dist` folder
- ✅ dist folder size: ~0.4 MB (not 2GB)

3. Check dist folder:
   ```powershell
   cd dist
   dir
   ```

**Verify:**
- ✅ index.html exists
- ✅ assets folder exists
- ✅ CSS and JS files exist
- ✅ Total size < 1 MB

## Test 10: Regression Testing

### Test Existing Features Still Work

**Steps:**
1. Start all components normally
2. Test all existing skills:

**Time Skill:**
- Say "What time is it?"
- ✅ Should speak current time

**Open App Skill:**
- Say "Open Notepad"
- ✅ Notepad should open

**Math Skill:**
- Say "What is two plus two?"
- ✅ Should say "4"

**Web Search:**
- Say "Search for Python tutorials"
- ✅ Should open browser with search

**Code Generation:**
- Say "Write a Python program to add two numbers"
- ✅ Should generate code and write to Notepad

**File Operations:**
- Say "Search for files named test"
- ✅ Should search and report results

## Test Results Checklist

Print this checklist and mark each test as you complete it:

### Error Handling Tests
- [ ] Audio driver fallback works
- [ ] Port conflict detected correctly
- [ ] Ollama detection works
- [ ] User-friendly error messages shown

### System Tray Tests
- [ ] Tray app starts successfully
- [ ] All menu options work
- [ ] Status display accurate
- [ ] Auto-start enable/disable works
- [ ] Dashboard opens correctly
- [ ] Clean quit works

### Startup Scripts Tests
- [ ] start_aether.bat works
- [ ] stop_aether.bat works
- [ ] All components start correctly
- [ ] Windows open properly

### Model Download Tests
- [ ] download_models.bat works
- [ ] All models download
- [ ] Models verified with ollama list

### Setup Script Tests
- [ ] setup.py checks system
- [ ] Dependencies install
- [ ] Shortcuts created
- [ ] Instructions clear

### Integration Tests
- [ ] Full workflow works
- [ ] Voice activation works
- [ ] Conversation mode works
- [ ] Hotkey works (if enabled)
- [ ] Dashboard loads
- [ ] Clean shutdown works

### Error Recovery Tests
- [ ] Microphone failure handled
- [ ] Ollama failure handled
- [ ] Recovery after fixing issues

### Documentation Tests
- [ ] User guide is clear
- [ ] Installer guide is clear
- [ ] All instructions accurate

### Production Build Tests
- [ ] Frontend builds successfully
- [ ] Build size is optimized (< 1 MB)
- [ ] No TypeScript errors

### Regression Tests
- [ ] All existing skills work
- [ ] No features broken
- [ ] Performance acceptable

## Performance Benchmarks

After testing, record these metrics:

**Startup Time:**
- Time to start all components: _____ seconds
- Time to first response: _____ seconds

**Response Time:**
- Time query (fast model): _____ seconds
- Conversation response (8B model): _____ seconds
- Code generation: _____ seconds

**Memory Usage:**
- Planner memory: _____ MB
- Wake listener memory: _____ MB
- Ollama memory: _____ MB
- Total memory: _____ MB

**Accuracy:**
- Wake word detection rate: _____%
- Speech recognition accuracy: _____%
- Intent classification accuracy: _____%

## Known Issues

Document any issues found during testing:

1. ___________________________
2. ___________________________
3. ___________________________

## Test Summary

**Total Tests:** 30
**Passed:** _____
**Failed:** _____
**Skipped:** _____

**Overall Status:** [ ] PASS / [ ] FAIL

**Notes:**
___________________________
___________________________
___________________________

## Next Steps After Testing

If all tests pass:
1. Build the Windows installer
2. Test the installer on a clean system
3. Create release notes
4. Prepare for distribution

If tests fail:
1. Document failures
2. Fix issues
3. Re-test
4. Repeat until all pass
