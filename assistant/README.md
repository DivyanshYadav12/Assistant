# Aether — Intelligent OS Assistant

> A production-grade, local-first desktop assistant that listens (voice or hotkey), understands your intent, automates your system, learns from your behavior, and asks before doing anything risky.

Think Jarvis/Cortana — but private, extensible, and under your control.

---

## What It Does

| Capability | Description |
|------------|-------------|
| **Voice + Hotkey Input** | Wake word ("Hey Aether") or configurable global hotkey; streaming speech-to-text |
| **Real-time Assistance** | Answers questions, executes tasks while you work, context-aware of your active apps |
| **System Automation** | Open/control apps, manage windows, run shell commands, manipulate files |
| **System Intelligence** | Detects errors, anomalies, unnecessary files (duplicates, orphans, bloated caches) |
| **Dev Environment Setup** | Detects/configures toolchains (Python, Node, Rust...), fixes missing deps, indexes codebases |
| **Safety Gate (HITL)** | Every risky action requires your approval, with preview and rollback |
| **Self-Learning** | Learns your preferences, phrasing, workflows — locally, transparently, reversibly |
| **Email/Calendar** | Delegates to the Hive skill (Gmail/Calendar with its own critic + approval chain) |

---

## Design Principles

1. **Local-first.** All models (STT, TTS, LLM, embeddings) run on-device. No cloud required.
2. **Safety by default.** Mutating actions are risk-classified; high-risk always needs explicit approval.
3. **Learn, don't leak.** Behavior learning happens locally, is auditable, and can be forgotten per-item.
4. **Skills, not monolith.** Every capability is a plugin implementing one narrow contract.
5. **Production quality.** Signed installers, auto-update, encryption at rest, audit logs, watchdog.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: Wake Word / Hotkey / Text  →  VAD → STT → Intent        │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR: Planner ─ Memory ─ Safety Gate ─ Clarifier       │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  SKILLS: System Control │ File Intelligence │ DevEnv │ Hive │ … │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  PRIVILEGED DAEMON (Rust): telemetry, FS watch, elevation       │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: TTS (piper) + HUD / Toast / Tray                       │
└─────────────────────────────────────────────────────────────────┘
```

Full details: [docs/ARCHITECTURE.md](./ARCHITECTURE.md)

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Daemon / privileged runtime | **Rust** (`tokio`, `pyo3`) | Memory safety, low overhead, clean Python FFI |
| Planner, skills, ML | **Python 3.11+** (`pydantic`, `langgraph`) | ML ecosystem, fast iteration |
| UI (tray, HUD, settings) | **Tauri** (Rust + webview) | Small footprint, single bundle, auto-update |
| Wake word | `porcupine` / `openwakeword` | Always-on, low CPU |
| VAD | `silero-vad` (ONNX) | Streaming friendly |
| STT | `faster-whisper` | Local, fast, accurate |
| TTS | `piper` | Local, natural voices, streaming |
| LLM (intent/planner) | Phi-3-mini / Gemma-2B via `llama.cpp` | Quantized, runs on laptop |
| Embeddings | `all-MiniLM-L6-v2` | Small, fast, good quality |
| Memory / vectors | `lancedb` | File-based, no server, encryption-friendly |
| IPC | gRPC / named pipes | Low latency daemon ↔ planner |

**No API keys required for core features.** Optional cloud models are opt-in.

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Component design, data flow, IPC contracts |
| [docs/FEATURES.md](./docs/FEATURES.md) | Every feature: what / why / how |
| [docs/SAFETY.md](./docs/SAFETY.md) | Risk classifier, approval flow, rollback design |
| [docs/MEMORY.md](./docs/MEMORY.md) | Two-tier memory schema, retrieval, retention |
| [docs/LEARNING.md](./docs/LEARNING.md) | Self-learning tiers, preference mining, LoRA adaptation |
| [docs/SKILLS.md](./docs/SKILLS.md) | Skill protocol, lifecycle, how to write a plugin |
| [docs/ROADMAP.md](./docs/ROADMAP.md) | Phased plan from MVP to production v1.0 |
| [docs/PRODUCTION.md](./docs/PRODUCTION.md) | Packaging, signing, security, compliance, performance targets |

---

## Project Status

**Phase: Design / Documentation.** No code yet — this documentation set is the blueprint.

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | Docs + architecture | ✅ this |
| 1 | Audio loop PoC (wake → STT → TTS) | ⬜ |
| 2 | Planner + 2 skills + safety gate | ⬜ |
| 3 | Memory + learning Tier 0-1 | ⬜ |
| 4 | File intelligence + DevEnv skills | ⬜ |
| 5 | Beta packaging + auto-update | ⬜ |
| 6 | Production v1.0 | ⬜ |

See [docs/ROADMAP.md](./docs/ROADMAP.md) for exit criteria and timelines.

---

## Relationship to Hive

**Hive** (the parent project at `d:\hive`, code in `d:\hive\src`) is a working multi-agent Gmail/Calendar assistant with a Critic + HITL approval chain. In Aether, Hive becomes **one skill** — the email/calendar specialist — invoked through its FastAPI (`hive serve`). Aether generalizes Hive's safety model to *all* system actions.

---

## License

TBD — decide before first public release (MIT/Apache-2.0 vs. proprietary). See [docs/PRODUCTION.md](./docs/PRODUCTION.md#3-privacy--compliance).
