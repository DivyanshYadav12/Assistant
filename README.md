# Aether — Intelligent Voice Assistant

> A production-grade, local-first desktop assistant that listens (voice or hotkey), understands your intent, automates your system, learns from your behavior, and asks before doing anything risky.

Think Jarvis/Cortana — but private, extensible, and under your control.

## 🚀 What It Does

| Capability | Description |
|------------|-------------|
| **Voice + Hotkey Input** | Wake word ("Computer") or Win+Alt+A hotkey; streaming speech-to-text |
| **Real-time Assistance** | Answers questions, executes tasks while you work |
| **System Automation** | Open/control apps, manage windows, run shell commands, manipulate files |
| **File Intelligence** | Find duplicates, clean caches, identify large files, smart file search |
| **Math & Notepad** | Spoken arithmetic, solve math problems directly from Notepad |
| **Web Search** | Google searches via voice command |
| **Email/Calendar** | Gmail/Calendar integration via Hive skill |
| **Safety Gate** | Every risky action requires your approval, with preview and rollback |
| **Self-Learning** | Learns your preferences, phrasing, workflows — locally and transparently |
| **Multi-Agent** | Planner, Critic, QA agents collaborate on complex tasks |

## 🎯 Design Principles

1. **Local-first** — All models (STT, TTS, LLM, embeddings) run on-device. No cloud required.
2. **Safety by default** — Mutating actions are risk-classified; high-risk always needs explicit approval.
3. **Learn, don't leak** — Behavior learning happens locally, is auditable, and can be forgotten per-item.
4. **Skills, not monolith** — Every capability is a plugin implementing one narrow contract.
5. **Production quality** — Audit logs, error recovery, encryption at rest, rollback capabilities.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: Wake Word / Hotkey  →  Vosk (Wake) → Whisper (STT)      │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR: Planner ─ Memory ─ Safety Gate ─ Voice Approval │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  SKILLS: System │ File │ Math │ Web │ Hive │ Cleanup │ ...      │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  MULTI-AGENT: Critic │ QA │ Planner (collaborative decisions)  │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: TTS (pyttsx3) + Voice Confirmation + System Actions    │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Core Runtime | **Python 3.11+** | ML ecosystem, fast iteration |
| Wake Word | `vosk` | Always-on, low CPU, on-device |
| STT | `faster-whisper` | Local, fast, accurate transcription |
| TTS | `pyttsx3` | Windows SAPI integration, reliable |
| LLM (intent/planner) | Ollama (qwen2.5:1.5b-instruct) | Local, quantized, runs on laptop |
| Embeddings | Ollama (nomic-embed-text) | Local semantic search |
| Memory | SQLite + Custom retrieval | File-based, no server, encryption-friendly |
| IPC | TCP Socket (port 48100) | Simple, reliable communication |
| Hotkey | `keyboard` | Global hotkey support |

**No API keys required for core features.** Optional cloud models are opt-in.

## 📚 Documentation

| Document | Contents |
|----------|----------|
| [docs/COMMANDS.md](./assistant/docs/COMMANDS.md) | Complete voice command reference |
| [docs/FEATURES.md](./assistant/docs/FEATURES.md) | Every feature: what / why / how |
| [docs/ROADMAP.md](./assistant/docs/ROADMAP.md) | Phased plan from MVP to production v1.0 |

## 🚦 Project Status

**Phase: Functional MVP** — Core features implemented and working.

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | Docs + architecture | ✅ Complete |
| 1 | Audio loop (wake → STT → TTS) | ✅ Complete |
| 2 | Planner + 12 skills + safety gate | ✅ Complete |
| 3 | Memory + learning Tier 0-1 | ✅ Complete |
| 4 | File intelligence + Hive + macros | 🔶 ~60% complete |
| 5 | Beta packaging + auto-update | ⬜ Not started |
| 6 | Production v1.0 | ⬜ Not started |

See [docs/ROADMAP.md](./assistant/docs/ROADMAP.md) for exit criteria and timelines.

## 🎤 Voice Commands

Aether responds to over 50 voice commands across categories:

- **Getting Started**: "Computer", "Hey Computer", "Stop listening"
- **System Control**: "Minimize window", "Set volume to 50", "Take screenshot"
- **File Operations**: "Create file notes.txt", "Find duplicate files", "Clean up my disk"
- **Math**: "What is 2 plus 2?", "Solve this on Notepad"
- **Web**: "Search for Python documentation"
- **Email/Calendar**: "Check my inbox", "Schedule a meeting"
- **Hotkey**: Press Win+Alt+A for reliable activation in noisy environments

[See full command reference →](./assistant/docs/COMMANDS.md)

## 🔧 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.11+
- Ollama (optional but recommended for LLM features)
- Vosk model (auto-downloaded on first run)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/aether.git
cd aether
```

2. **Install Python dependencies**
```bash
cd assistant/planner
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

3. **Download Vosk model** (auto-downloaded to `%LOCALAPPDATA%\Aether\vosk-model-small-en-us-0.15`)

4. **Start Ollama** (optional but recommended)
```bash
ollama serve
ollama pull qwen2.5:1.5b-instruct
ollama pull nomic-embed-text
```

### Running Aether

Open three terminals:

**Terminal 1 — Planner (skills + TTS)**
```powershell
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.listener
```

**Terminal 2 — Wake word listener (microphone)**
```powershell
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.wake
```

**Terminal 3 — Hive (email/calendar, optional)**
```powershell
cd d:\hive\src
python -m hive serve
```

**Optional — Web Dashboard (recommended)**
```powershell
# Terminal 4 — Dashboard backend
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.dashboard.main

# Terminal 5 — Dashboard frontend
cd d:\hive\assistant\dashboard\frontend
npm install
npm run dev
```

Then say **"Computer"** or press **Win+Alt+A** to start giving commands, or access the web dashboard at `http://localhost:5173` for real-time monitoring, command history, and settings.

**Enable hotkey mode** (more reliable in noisy environments):
```powershell
$env:AETHER_ENABLE_HOTKEY="1"
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.wake
```

## 🎯 Current Skills

Aether includes 12 production-ready skills:

| Skill | Description |
|-------|-------------|
| **TimeSkill** | Time, date, day of week queries |
| **OpenAppSkill** | Launch applications (Notepad, Chrome, VS Code, etc.) |
| **TypeTextSkill** | Type/write text into applications |
| **FileSearchSkill** | Search files by name across user profile |
| **FileOpsSkill** | Create/delete files with trash rollback |
| **UndoSkill** | Restore last deleted/created file |
| **WebSearchSkill** | Google search integration |
| **MathSkill** | Spoken arithmetic calculations |
| **NotepadSolveSkill** | Solve math problems from Notepad selection |
| **HiveSkill** | Email/calendar via Hive API |
| **SystemControlSkill** | Windows, volume, brightness, screenshot, clipboard, power, shell |
| **FileCleanupSkill** | Duplicate/cache/large file scanner with rollback |

## 🔒 Safety & Privacy

- **Risk Classification**: Every action is classified as Safe, Low, Medium, or High risk
- **Approval Flow**: Medium/High-risk actions require voice or dialog approval
- **Audit Log**: All actions, approvals, and conversations are logged with hash-chained integrity
- **Rollback**: File operations use trash-based rollback for easy recovery
- **Local-First**: All processing happens on-device; no data leaves your machine
- **Explicit Rules**: Create permanent rules like "Never touch D:/photos" or "Always approve notepad"

## 🧠 Learning System

Aether learns in three tiers:

- **Tier 0 (Explicit Rules)**: User-defined rules that persist across restarts
- **Tier 1 (Preference Mining)**: Learns from approval/rejection patterns, adapts behavior
- **Tier 2 (Macro Detection)**: Identifies frequent action sequences, proposes macros (in progress)

All learning is local, auditable, and reversible.

## 🤝 Multi-Agent Architecture

Aether uses collaborative agents for complex decisions:

- **Planner**: Intent routing, multi-step command orchestration
- **Critic**: Evaluates outputs, suggests improvements
- **QA**: Answers questions, retrieves from memory
- **Skills**: Specialized execution engines (one per capability)

Agents communicate via shared memory and can debate decisions before execution.

## 📊 Environment Variables

Configure Aether via environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `AETHER_OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API URL |
| `AETHER_LLM_MODEL` | `qwen2.5:1.5b-instruct` | LLM model for intent classification |
| `AETHER_EMBED_MODEL` | `nomic-embed-text` | Model for memory embeddings |
| `AETHER_ENABLE_HOTKEY` | `0` | Enable hotkey listener |
| `AETHER_HOTKEY` | `win+alt+a` | Hotkey combination |
| `AETHER_DATA_DIR` | `planner/data` | Data directory for memory/audit/learning |

## 🐛 Troubleshooting

**Wake word not detected?**
- Enable hotkey mode: `$env:AETHER_ENABLE_HOTKEY="1"`
- Check microphone permissions in Windows settings
- Try a different microphone device

**Ollama connection failed?**
- Ensure Ollama is running: `ollama serve`
- Check Ollama is accessible: `curl http://127.0.0.1:11434`

**Voice approval not working?**
- Falls back to Windows dialog if voice not detected
- Check microphone volume levels
- Try speaking closer to microphone

## 🗺️ Roadmap

- [ ] DevEnvSkill — toolchain detection and venv setup
- [ ] CodebaseSkill — semantic code Q&A with tree-sitter
- [ ] Macro replay — trigger saved macros by voice
- [ ] Tauri desktop app with tray UI
- [ ] Windows MSI installer with auto-update
- [ ] Plugin system for community skills
- [ ] Multi-user support with RBAC
- [ ] macOS/Linux support

See [docs/ROADMAP.md](./assistant/docs/ROADMAP.md) for details.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

Areas needing help:
- Additional skills (browser automation, smart home, etc.)
- Cross-platform support (macOS, Linux)
- UI/UX improvements
- Documentation improvements
- Bug fixes and performance optimizations

## 📄 License

MIT License — see [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- **Vosk** — On-device speech recognition
- **faster-whisper** — Fast STT implementation
- **Ollama** — Local LLM inference
- **Hive** — Multi-agent email/calendar assistant (parent project)

## 📞 Contact

- Issues: [GitHub Issues](https://github.com/yourusername/aether/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/aether/discussions)

---

**Built with ❤️ for privacy-first AI assistants**
