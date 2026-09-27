# Aether — Voice Command Reference

## Starting the Assistant

Before you can use voice commands, you need to start the assistant's backend services. Open a terminal and run these commands.

### 1. Start the Planner (intent processing + skills + TTS)

```powershell
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.listener
```

This starts the planner server on `127.0.0.1:48100`. It listens for transcribed text from the wake word listener or hotkey daemon, routes it to the right skill, and speaks responses.

### 2. Start the Wake Word Listener (voice input)

```powershell
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.wake
```

This starts continuous microphone listening using Vosk. Say **"Computer"** to activate it, then speak your command. It records your voice and sends it to the planner for transcription and processing.

**Optional: Enable hotkey mode** (more reliable in noisy environments):
```powershell
$env:AETHER_ENABLE_HOTKEY="1"
.\.venv\Scripts\python.exe -m assistant.core.wake
```

Now you can press **Win+Alt+A** instead of saying "Computer". Both methods work simultaneously.

### 3. Start Hive (email & calendar — optional)

```powershell
cd d:\hive\src
python -m hive serve
```

Starts Hive's FastAPI server on `127.0.0.1:8000`. Only needed if you want email/calendar commands. The planner will auto-start Hive if it's not running when you issue an email/calendar command.

### 4. Start Ollama (local LLM — optional but recommended)

```powershell
ollama serve
```

Starts the Ollama API on `127.0.0.1:11434`. Used for intent classification, conversation fallback, and memory embeddings. Without Ollama, the assistant falls back to keyword-based routing (still works, just less accurate).

### Quick Start (all-in-one)

Open three terminals and run in order:

```powershell
# Terminal 1 — Ollama (LLM backend)
ollama serve

# Terminal 2 — Planner (skills + TTS)
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.listener

# Terminal 3 — Wake word listener (microphone)
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.wake
```

Then say **"Computer"** and start giving commands.

### Stopping the Assistant

| Method | What to do |
|--------|-----------|
| Voice | Say **"Stop listening"**, **"Shut down"**, or **"Goodbye"** |
| Keyboard | Press **Ctrl+C** in the wake word listener terminal |
| Force stop | Close all three terminal windows |

---

## Voice Commands

All commands are spoken after the wake word **"Computer"** or hotkey **Win+Alt+A**. The assistant chimes to confirm it's listening, then speaks your answer or asks for approval.

---

## Getting Started

### Voice Activation

| Say | What happens |
|-----|-------------|
| **Computer** | Wake word — assistant starts listening for a command |
| **Hey Computer** | Alternative wake word |
| **Stop listening** | Stops the assistant (no need for Ctrl+C) |
| **Shut down** | Same as stop listening |
| **Goodbye** | Same as stop listening |

### Hotkey Activation

| Press | What happens |
|-------|-------------|
| **Win+Alt+A** | Activates voice input (alternative to wake word) |
| **Ctrl+C** | Stops the assistant |
| **Ctrl+C** | Stops the assistant |

**Why use hotkey?** More reliable in noisy environments where wake word detection is flaky. Works like Iron Man's JARVIS.

**To enable hotkey mode:**
Set the environment variable before starting the wake word listener:
```powershell
$env:AETHER_ENABLE_HOTKEY="1"
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.wake
```

**To customize the hotkey:**
```powershell
$env:AETHER_ENABLE_HOTKEY="1"
$env:AETHER_HOTKEY="ctrl+shift+a"  # or any keyboard combination
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.wake
```

Both wake word and hotkey work simultaneously when enabled.

---

## Conversation & Q&A

| Say | What happens |
|-----|-------------|
| **Hello, how are you?** | Human-like conversation via local LLM |
| **What is the capital of France?** | General knowledge Q&A |
| **Tell me a joke** | Casual chat |
| **Explain how HTTPS works** | Educational explanations |

The assistant remembers conversation context within a session and persists it to memory for future reference.

---

## Time & Date

| Say | What happens |
|-----|-------------|
| **What time is it?** | Speaks the current time |
| **What's the date?** | Speaks today's date |
| **What day is it?** | Speaks the day of the week |

---

## Math

### Spoken Math (instant answer)

| Say | Response |
|-----|----------|
| **What is 2 plus 2?** | "2 + 2 equals 4" |
| **Calculate 15 times 3** | "15 * 3 equals 45" |
| **What's 100 divided by 7?** | "100 / 7 equals 14.2857" |
| **How much is 50 minus 18?** | "50 - 18 equals 32" |

### Notepad Math (reads & solves from screen)

| Say | What happens |
|-----|-------------|
| **Solve this on Notepad** | Reads selected text in Notepad, solves the math, writes the answer below |
| **Solve it on Notepad** | Same as above |
| **Answer this on Notepad** | Same as above |

**Steps for Notepad solve:**
1. Open Notepad and type or paste a math problem
2. Select the problem text (Ctrl+A or drag-select)
3. Say "Computer, solve this on Notepad"
4. Approve when asked — the answer appears below the problem

Supports: arithmetic (`2 + 2`), word problems (`what is 15 times 3?`), and simple equations (`x + 5 = 10` → `x = 5`).

---

## Opening Apps

| Say | What happens |
|-----|-------------|
| **Open Notepad** | Launches Notepad |
| **Open Calculator** | Launches Calculator |
| **Open Chrome** | Launches Google Chrome |
| **Open VS Code** | Launches Visual Studio Code |
| **Open File Explorer** | Launches File Explorer |
| **Open Task Manager** | Launches Task Manager |
| **Open Terminal** | Launches Windows Terminal |
| **Open Paint** | Launches MS Paint |
| **Open Edge** | Launches Microsoft Edge |

---

## Typing & Writing

| Say | What happens |
|-----|-------------|
| **Write hello world in Notepad** | Types "hello world" into Notepad |
| **Type meeting notes at 3pm** | Types the text into Notepad |
| **Note down buy groceries** | Writes "buy groceries" into Notepad |
| **Jot down call mom tomorrow** | Writes "call mom tomorrow" into Notepad |

---

## File Operations

| Say | What happens |
|-----|-------------|
| **Create a file called notes.txt** | Creates the file in Documents |
| **Create file test.py on Desktop** | Creates the file on Desktop |
| **Delete file old_report.txt** | Moves to Aether's trash (recoverable) |
| **Delete file notes.txt from Downloads** | Deletes from specific location |
| **Undo that** | Restores the last deleted/created file |
| **Restore** | Same as undo |

**Locations supported:** Desktop, Documents, Downloads.

---

## File Search

| Say | What happens |
|-----|-------------|
| **Find files named budget** | Searches user profile for matching files |
| **Search for files called report** | Same as above |
| **Locate file config.json** | Searches for specific filename |

---

## File Cleanup

| Say | What happens |
|-----|-------------|
| **Find duplicate files** | Scans for duplicates by content hash |
| **Scan for cache files** | Finds node_modules, __pycache__, .venv, etc. |
| **What large files do I have?** | Lists files over 100 MB |
| **Clean up my disk** | Combined scan: duplicates + caches + large files |
| **Find junk files** | Same as combined scan |
| **Free up space** | Same as combined scan |

When you approve deletion, files move to Aether's trash — say **"undo"** to restore.

---

## System Control

### Window Management

| Say | What happens |
|-----|-------------|
| **Minimize Notepad** | Minimizes the Notepad window |
| **Maximize Chrome** | Maximizes the Chrome window |
| **Close window Explorer** | Closes the window (high risk — asks approval) |
| **Switch to VS Code** | Focuses the VS Code window |
| **Bring to front Chrome** | Brings Chrome to front |
| **Show desktop** | Minimizes all windows (Win+D) |
| **Minimize all** | Same as show desktop |

### Volume

| Say | What happens |
|-----|-------------|
| **Mute the volume** | Mutes system audio |
| **Unmute** | Unmutes system audio |
| **Set volume to 50** | Sets volume to 50% |
| **Set volume to 80** | Sets volume to 80% |

### Brightness

| Say | What happens |
|-----|-------------|
| **Set brightness to 80** | Sets screen brightness to 80% |
| **Set brightness to 30** | Sets screen brightness to 30% |

### Screenshot

| Say | What happens |
|-----|-------------|
| **Take a screenshot** | Saves screenshot to Pictures/Screenshots |
| **Capture screen** | Same as above |

### Clipboard

| Say | What happens |
|-----|-------------|
| **Copy hello to clipboard** | Copies text to clipboard |
| **Paste from clipboard** | Pastes clipboard content (Ctrl+V) |

### System Power

| Say | What happens |
|-----|-------------|
| **Lock the screen** | Locks the workstation |
| **Sleep the system** | Puts system to sleep (asks approval) |
| **Hibernate** | Hibernates the system (asks approval) |

### Shell Commands

| Say | What happens |
|-----|-------------|
| **Run command echo hello** | Runs the shell command (asks approval) |
| **Execute ipconfig** | Runs the command (asks approval) |
| **Kill process chrome** | Kills chrome.exe (asks approval) |
| **End process notepad** | Kills notepad.exe (asks approval) |

---

## Web Search

| Say | What happens |
|-----|-------------|
| **Search for Python documentation** | Opens Google search in browser |
| **Google weather today** | Opens Google search |
| **Look up Rust async tutorial** | Opens Google search |

---

## Email & Calendar (Hive)

| Say | What happens |
|-----|-------------|
| **Check my inbox** | Summarizes unread emails |
| **Summarize my emails** | Same as above |
| **Draft a reply to John about the project** | Drafts an email reply |
| **Schedule a meeting with Sarah tomorrow at 3pm** | Proposes a calendar event |
| **What's on my calendar today?** | Lists today's events |
| **Book a meeting with the team** | Schedules a meeting |

Hive auto-starts if not running. Email/calendar actions are **high risk** — always require approval. If Gemini quota is exhausted, falls back to Ollama automatically.

---

## Approval Flow (Voice)

When the assistant needs approval for a medium or high-risk action:

1. It **speaks** the action preview: *"Approval required. Delete file: notes.txt. Do you approve?"*
2. **Listen for your response** (6 seconds):

| Say | Meaning |
|-----|---------|
| **Yes** | Approve |
| **Approve** | Approve |
| **OK** | Approve |
| **Okay** | Approve |
| **Confirm** | Approve |
| **Go ahead** | Approve |
| **Do it** | Approve |
| **Sure** | Approve |
| **Yeah** | Approve |
| **Continue** | Approve |
| **Proceed** | Approve |
| **No** | Reject / cancel |
| **Reject** | Reject |
| **Cancel** | Reject |
| **Deny** | Reject |
| **Stop** | Reject |
| **Nope** | Reject |
| **Abort** | Reject |

3. If no voice response is heard, falls back to a Windows Yes/No dialog.

---

## Learning — Explicit Rules

| Say | What happens |
|-----|-------------|
| **Never touch D:/photos** | Creates a permanent rule — blocks any file operation on D:/photos |
| **Always approve notepad** | Creates a rule to auto-approve Notepad actions |
| **Never delete files in Documents** | Blocks delete operations in Documents |

Rules are enforced before every skill execution and persist across restarts.

---

## Undo

| Say | What happens |
|-----|-------------|
| **Undo that** | Reverses the last reversible action |
| **Restore** | Same as undo |

Works for: file creation, file deletion, duplicate cleanup, cache cleanup. Deleted files are restored from Aether's trash.

---

## Risk Levels & Approval Behavior

| Risk | Examples | Approval |
|------|----------|----------|
| **Safe** | Time, math, screenshot, file search, lock screen | No approval needed |
| **Low** | Open app, web search, mute/unmute, volume, brightness, clipboard, show desktop | No approval needed |
| **Medium** | Type text, create files, minimize/maximize windows, Notepad solve, sleep | Ask once per session, then auto-approve |
| **High** | Delete files, close windows, shell commands, kill process, email/calendar, hibernate, file cleanup deletion | **Always asks** — voice approval required |

---

## Tips

- **Speak naturally** — the assistant understands free-form commands, not just exact phrases
- **Multi-step commands** work: *"Open Notepad and then write hello world"*
- **It learns your preferences** — if you always approve the same action, it stops asking (Tier 1)
- **It detects workflows** — repeated action sequences are proposed as macros (Tier 2)
- **Everything is logged** — actions, approvals, and conversations are in the audit log
- **Memory persists** — past actions and conversations are stored for future context

---

## Environment Variables (Configuration)

| Variable | Default | Purpose |
|----------|---------|---------|
| `AETHER_OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API URL for LLM + embeddings |
| `AETHER_LLM_MODEL` | `qwen2.5:1.5b-instruct` | Ollama model for intent classification |
| `AETHER_EMBED_MODEL` | `nomic-embed-text` | Ollama model for memory embeddings |
| `AETHER_WHISPER_MODEL` | `tiny` | Whisper model size (tiny/base/small/medium) |
| `AETHER_WHISPER_DEVICE` | `auto` | Whisper device (auto/cpu/cuda) |
| `AETHER_HIVE_URL` | `http://127.0.0.1:8000` | Hive API URL |
| `AETHER_HIVE_DIR` | `../hivechild` | Hive project directory |
| `AETHER_DATA_DIR` | `planner/data` | Data directory for memory/audit/learning |
| `AETHER_ENABLE_HOTKEY` | `0` | Enable hotkey listener (set to "1" to enable) |
| `AETHER_HOTKEY` | `win+alt+a` | Hotkey combination for voice activation |
