# Aether Crash Reporting Guide

## Overview

Aether now includes automatic crash reporting and error logging to help diagnose and fix issues.

## How It Works

### Automatic Crash Detection

When Aether crashes (unhandled exception), the crash handler:

1. **Logs the crash** to `~/.aether/logs/crashes.log`
2. **Creates a human-readable report** at `~/.aether/logs/crash_<timestamp>.txt`
3. **Prints crash information** to the console
4. **Shows the crash report location**

### Error Logging

Non-fatal errors are logged to:
- `~/.aether/logs/errors.log` (JSON format)
- `~/.aether/logs/error_<timestamp>.txt` (human-readable)

## Log Location

Logs are stored in:
```
C:\Users\<YourUsername>\.aether\logs\
```

## Viewing Crash Reports

### Find Recent Crashes

```powershell
cd C:\Users\<YourUsername>\.aether\logs
dir *.txt /O-D
```

### View a Crash Report

Open any `crash_*.txt` file in a text editor.

### View Error Logs

```powershell
cd C:\Users\<YourUsername>\.aether\logs
type errors.log
```

## Crash Report Contents

Each crash report includes:
- **Timestamp** - When the crash occurred
- **Crash Type** - Exception type (e.g., OSError, ValueError)
- **Crash Message** - Error message
- **Context** - Additional context information
- **Full Traceback** - Complete stack trace

## Example Crash Report

```
CRASH REPORT: Aether Planner
==================================================
Timestamp: 2026-10-05T14:30:00
Crash Type: OSError
Crash Message: [WinError 10048] Only one usage of each socket address

Context:
  component: planner
  port: 48100

Full Traceback:
Traceback (most recent call last):
  File "listener.py", line 80, in main
    req = urllib.request.Request(...)
OSError: [WinError 10048] Only one usage of each socket address
```

## Automatic Log Cleanup

Logs older than 30 days are automatically cleaned up to save disk space.

To change this, modify the `clear_old_logs()` call in the code.

## Reporting Crashes

If you experience a crash:

1. **Check the crash report** in `~/.aether/logs/`
2. **Copy the crash ID** (e.g., `crash_2026-10-05T14-30-00`)
3. **Check if it's a known issue** on GitHub
4. **Report the issue** with:
   - Crash ID
   - What you were doing when it crashed
   - System information (Windows version, RAM, etc.)
   - The crash report content

## Common Crashes and Solutions

### Port Already in Use

**Error:** `[WinError 10048] Only one usage of each socket address`

**Solution:**
```powershell
netstat -ano | findstr :48100
taskkill /PID <PID> /F
```

### Audio Driver Error

**Error:** `Unanticipated host error [PaErrorCode -9999]`

**Solution:**
- Use hotkey mode instead
- Or reinstall audio drivers

### Ollama Not Running

**Error:** `Connection refused` when checking Ollama

**Solution:**
```powershell
ollama serve
```

### Model Not Found

**Error:** `Failed to load model`

**Solution:**
```powershell
ollama pull llama3:8b
```

## Disabling Crash Reporting

To disable automatic crash reporting (not recommended), comment out the crash handler setup in:
- `listener.py`
- `wake.py`
- `tray_app.py`

## Troubleshooting

### Logs Not Created

**Check:**
- Log directory exists: `~/.aether/logs/`
- Write permissions on the directory
- Disk space available

### Crash Handler Not Working

**Check:**
- Crash handler imported correctly
- No conflicting exception handlers
- Python version compatibility

## Integration with Components

The crash handler is integrated into:
- **Planner** (`listener.py`) - Main planning component
- **Wake Listener** (`wake.py`) - Speech recognition
- **System Tray** (`tray_app.py`) - GUI control

Each component logs crashes with context specific to that component.

## For Developers

### Adding Context to Logs

```python
from assistant.core.crash_handler import log_error

try:
    # Your code
    risky_operation()
except Exception as e:
    log_error(e, context={
        "component": "my_component",
        "operation": "risky_operation",
        "user_id": user_id
    })
```

### Manual Crash Logging

```python
from assistant.core.crash_handler import CrashHandler

handler = CrashHandler("MyComponent")
error_id = handler.log_error(error, context={"key": "value"})
```

## Summary

✅ **Automatic crash detection and logging**
✅ **Human-readable crash reports**
✅ **Error logging for non-fatal issues**
✅ **Automatic log cleanup**
✅ **Integrated into all major components**

Crash reporting helps make Aether more stable and easier to debug!
