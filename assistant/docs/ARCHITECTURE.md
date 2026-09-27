# Architecture

## 1. Process Model

Aether runs as **three cooperating processes**:

```
┌──────────────────────────┐   gRPC / named pipe   ┌──────────────────────────┐
│  DAEMON (Rust, service)  │◄─────────────────────►│  PLANNER (Python, user)  │
│  - wake word + VAD       │                       │  - intent classification │
│  - audio ring buffer     │                       │  - LLM planner loop      │
│  - FS watcher (USN)      │                       │  - skill registry        │
│  - perf/ETW telemetry    │                       │  - memory (lancedb)      │
│  - elevation broker      │                       │  - safety gate           │
└────────────┬─────────────┘                       └────────────┬─────────────┘
             │                                                  │
             │              local HTTP / events                 │
             └────────────────────┬─────────────────────────────┘
                                  ▼
                     ┌──────────────────────────┐
                     │  UI (Tauri)              │
                     │  - tray icon             │
                     │  - HUD / toasts          │
                     │  - approval dialogs      │
                     │  - settings + audit view │
                     └──────────────────────────┘
```

| Process | Privileges | Restart policy |
|---------|-----------|----------------|
| Daemon | User by default; elevation broker per action | Windows Service / systemd, auto-restart |
| Planner | User | Watchdog: daemon restarts it on crash |
| UI | User | On demand; assistant works headless without it |

---

## 2. Data Flow (One Turn)

```
1. TRIGGER    wake word detected OR hotkey pressed OR text typed
2. CAPTURE    daemon streams mic audio → VAD segments speech
3. STT        faster-whisper streaming → partial + final transcript
4. CLASSIFY   local LLM → {intent, entities, confidence}
5. RETRIEVE   memory query (top-k, filtered by type) → context
6. ROUTE      skill registry: can_handle() scores → top-k skills
7. PLAN       planner LLM decides skill call(s) + arguments
8. GATE       risk classifier → safe/low: execute; medium/high: approval queue
9. APPROVE    user approves via voice / HUD / tray (or rejects)
10. EXECUTE   skill runs; high-risk actions record rollback_plan
11. LEARN     feedback collector logs decision for preference mining
12. RESPOND   text → piper TTS + HUD render
```

Latency budget (wake → first spoken token): **< 800 ms** (see PRODUCTION.md).

---

## 3. Component Contracts

### 3.1 Daemon ↔ Planner (gRPC)

```protobuf
service Daemon {
  // Audio
  rpc StreamAudio(AudioRequest) returns (stream AudioChunk);
  rpc SetWakeWord(WakeWordConfig) returns (Ack);

  // System
  rpc GetTelemetry(TelemetryRequest) returns (TelemetrySnapshot);
  rpc WatchFileSystem(WatchRequest) returns (stream FsEvent);

  // Privileged actions (broker pattern)
  rpc RequestElevatedAction(ElevatedActionRequest) returns (ElevatedActionResult);
}

service Planner {
  rpc OnTranscript(Transcript) returns (Ack);
  rpc OnHotkey(HotkeyEvent) returns (Ack);
  rpc GetPendingApprovals(Empty) returns (ApprovalList);
  rpc ResolveApproval(ApprovalDecision) returns (Ack);
}
```

### 3.2 Planner State Machine

LangGraph-style loop with these nodes:

| Node | Responsibility | Failure behavior |
|------|---------------|-----------------|
| `classify` | intent + entities + confidence | confidence < 0.7 → `clarify` |
| `retrieve` | memory hits injected into context | empty OK, proceed |
| `route` | pick top-k skills by `can_handle()` | no skill ≥ 0.3 → `clarify` |
| `gate` | risk classification | ambiguous → LLM judge → still ambiguous → treat as `high` |
| `execute` | invoke skill(s) | error → retry once → report |
| `clarify` | ask user one question | timeout 30 s → abort turn politely |
| `respond` | compose answer, TTS + HUD | — |

State is a single Pydantic model (`TurnState`) checkpointed per turn for audit.

### 3.3 Elevation Broker (security-critical)

The planner **never** holds admin rights. For privileged actions:

1. Skill calls `daemon.RequestElevatedAction(action, rationale, rollback_plan)`
2. Daemon validates action against an **allowlist** of elevatable operation types
3. OS elevation prompt (UAC / polkit) shown with human-readable rationale
4. Daemon executes, returns result, records audit entry

Not on the allowlist → hard reject, no prompt.

---

## 4. Storage Layout

```
%LOCALAPPDATA%/Aether/          (or ~/.local/share/aether)
├── models/                     # downloaded GGUF/ONNX models
├── memory/
│   └── store.lance             # lancedb — encrypted at rest (AES-256)
├── audit/
│   └── actions-YYYY-MM.jsonl   # append-only audit log
├── learning/
│   ├── preferences.lance       # learned preferences
│   └── user_lora.safetensors   # optional Tier-3 adapter
├── config.toml                 # user settings
└── logs/
```

Encryption key lives in the OS keyring (DPAPI / Keychain / Secret Service).

---

## 5. Concurrency Model

- **Daemon**: `tokio` async; audio pipeline on a dedicated real-time thread.
- **Planner**: single logical turn at a time (queue); memory queries and skill I/O async.
- **Approvals**: pending approvals persist across restarts (sqlite queue); resolving one resumes the paused turn.

---

## 6. Failure Modes & Degradation

| Failure | Behavior |
|---------|----------|
| STT model missing/corrupt | Fall back to text input; toast with fix instructions |
| LLM OOM / too slow | Drop to smaller quantization; disable proactive suggestions |
| Vector DB corrupt | Rebuild index from audit log + file scan; preferences re-mined |
| Daemon crash | Service auto-restart; planner reconnects with backoff |
| Planner crash mid-approval | Approval queue is persistent; turn resumes on restart |
| Mic unavailable | Hotkey + text mode only |

---

## 7. Why Rust + Python (and not one language)

| Concern | Winner | Reason |
|---------|--------|--------|
| Always-on, low idle CPU | Rust | No GC pauses, tiny memory footprint |
| OS hooks (audio, ETW, USN) | Rust | Native APIs, safe concurrency |
| ML/LLM inference + iteration | Python | onnxruntime, llama-cpp-python, sentence-transformers |
| Skill authoring by contributors | Python | Low barrier, rich ecosystem |
| Bridging | `pyo3`/gRPC | Mature, typed, fast |

C++ would work for the daemon but Rust gives the same performance with far fewer memory-safety CVEs — important for a privileged, always-running process.
