# Features — What / Why / How

## 1. Voice + Hotkey Input

- **What**: Always-listening wake word ("Hey Aether") and a user-configurable global hotkey (push-to-talk). Text input always available as fallback.
- **Why**: Hands-free, instant access during live work — no window switching.
- **How**: `porcupine`/`openwakeword` (wake) + `silero-vad` (speech segmentation) + `faster-whisper` (streaming STT) in the Rust daemon. Audio kept in a ring buffer; nothing leaves the device.

## 2. Intent Classification + Routing

- **What**: Raw transcript → structured `{intent, entities, confidence}` → routed to best skill(s).
- **Why**: One entry point for every request; input modality decoupled from action logic.
- **How**: Quantized local LLM (Phi-3-mini / Gemma-2B) with few-shot JSON prompting. Router scores `can_handle()` across the skill registry.

## 3. Real-time Q&A During Work

- **What**: Answer questions about your system, files, code, schedule while you work.
- **Why**: Eliminates context-switching to a browser or docs.
- **How**: Planner retrieves from memory (files, codebase index, past actions) + optional web-search skill; response spoken via `piper` and shown in HUD.

## 4. System Automation

- **What**: Open/close/control applications, manage windows, run shell commands, type/paste, manipulate files.
- **Why**: The core "automate my laptop" promise.
- **How**: `SystemControlSkill` — Windows UI Automation / `pywinauto` + PowerShell; elevation via the daemon's broker (allowlist + UAC). Every mutation goes through the Safety Gate.

## 5. System Error & Anomaly Detection

- **What**: Detects failing services, memory leaks, disk pressure, abnormal CPU/network patterns; explains and proposes fixes.
- **Why**: "The system should know how, when, why, and what" — proactive health.
- **How**: Daemon streams perf counters/ETW → anomaly model (autoencoder, ONNX; post-MVP) + deterministic thresholds (MVP). Findings become proactive HUD suggestions with fix actions gated by approval.

## 6. Unnecessary-File Intelligence

- **What**: Finds duplicates, orphaned packages, stale caches, giant build artifacts (`node_modules`, `__pycache__`, `target/`); safe cleanup with preview + undo.
- **Why**: Reclaims disk space; keeps the machine healthy without risky manual cleanup.
- **How**: Rust FS scanner (xxHash content hashing, USN journal incremental) → `FileCleanupSkill` classifies keep/cache/duplicate/orphan (rules for MVP, trained classifier later). Deletion = `high` risk → always preview + trash-based rollback.

## 7. Dev Environment & Codebase Setup

- **What**: Detects installed toolchains, sets up venvs/node_modules/rust targets, diagnoses missing deps, indexes local repos for semantic Q&A ("where is the auth middleware?").
- **Why**: Setup and onboarding are the most repetitive dev chores.
- **How**: `DevEnvSkill` (toolchain detection + package manager drivers) and `CodebaseSkill` (tree-sitter symbols + embeddings in lancedb). Modifications gated at `medium` risk.

## 8. Safety Gate — Generalized HITL

- **What**: Every mutating action is risk-classified (`safe`/`low`/`medium`/`high`); medium asks once per session, high always requires explicit approval with preview + rollback plan.
- **Why**: Automation without fear; trust is the product.
- **How**: Deterministic rules first, LLM judge for ambiguity; approval via voice / HUD / tray. Details in [SAFETY.md](./SAFETY.md).

## 9. Two-Tier Memory

- **What**: Short-term session context (active windows, recent turns) + long-term store (files, actions, preferences, codebases, conversations).
- **Why**: "The file I edited yesterday", "never touch my project folders" — context and personalization.
- **How**: lancedb with embeddings + typed metadata; hybrid retrieval with recency decay. Details in [MEMORY.md](./MEMORY.md).

## 10. Self-Learning

- **What**: Learns preferences, phrasing, risk tolerance, and repeated workflows from approvals/rejections/clarifications — locally, transparently, per-item forgettable.
- **Why**: The assistant must get better *for you* without cloud training.
- **How**: Tier 0 explicit rules → Tier 1 nightly preference mining → Tier 2 workflow-macro detection → Tier 3 optional on-device LoRA. Details in [LEARNING.md](./LEARNING.md).

## 11. Workflow Macros

- **What**: Detects repeated multi-step sequences and offers them as one command or hotkey ("Email to Notepad").
- **Why**: Compresses your personal routines into single actions.
- **How**: Sequence mining over session action logs (frequency ≥ N in M days → propose macro). Macros replay through the same Safety Gate.

## 12. Clarifier

- **What**: When intent is ambiguous or confidence is low, asks one targeted question instead of guessing.
- **Why**: Wrong actions destroy trust faster than slow ones.
- **How**: Planner emits `clarification_question` when confidence < 0.7 or required entities missing; answer captured by voice/HUD and merged into the same turn.

## 13. Rollback / Undo

- **What**: "Undo that" reverses the last high-risk action (restore from trash, revert setting, un-send where possible).
- **Why**: Safety net that makes users comfortable approving automation.
- **How**: Skills return `rollback_plan` JSON; executor stores it in the audit log; undo replays the inverse operation.

## 14. Email & Calendar (Hive Skill)

- **What**: Summarize inbox, draft replies in your tone, schedule meetings — with Hive's own critic + approval chain.
- **Why**: Reuse a working, safety-gated implementation instead of rebuilding.
- **How**: `HiveSkill` adapter calls Hive's FastAPI (`/run`, `/approve`, `/reject`); Hive's HITL maps onto Aether's `high`-risk approval channel.

## 15. Response Pipeline (TTS + HUD)

- **What**: Speaks answers aloud and/or shows a compact HUD with action buttons.
- **Why**: Multimodal feedback — listen while working or glance at the screen.
- **How**: `piper` local TTS streamed to audio out; Tauri HUD renders text, previews, and Approve/Reject controls.

## 16. Audit & Transparency

- **What**: Every action, approval, and learned preference is inspectable; per-item "Forget"; global "Reset learning".
- **Why**: Production trust requirement; also invaluable for debugging.
- **How**: Append-only JSONL audit log + settings UI backed by the same store. See [PRODUCTION.md](./PRODUCTION.md).
