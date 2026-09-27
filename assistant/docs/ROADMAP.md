# Roadmap — MVP to Production v1.0

Phased plan with hard exit criteria. Each phase ships something runnable.

---

## Phase 0 — Design & Docs ✅

- Architecture, safety, memory, learning, skills specs (this docs set).

**Exit**: docs reviewed, stack locked (Rust + Python + Tauri).

---

## Phase 1 — Audio Loop PoC (1–2 weeks)

- Rust daemon: mic capture, ring buffer, `porcupine` wake word, `silero-vad`.
- `faster-whisper` STT → transcript → `piper` TTS echo ("you said …").
- Global hotkey trigger as alternative to wake word.

**Exit**: wake → transcript → spoken echo round-trip **< 800 ms** on a mid-range laptop; idle CPU < 1%.

---

## Phase 2 — Planner + 2 Skills + Safety Gate (4–6 weeks)

- Python planner loop: classify → retrieve(stub) → route → gate → execute → respond.
- Local LLM (Phi-3-mini GGUF) for intent JSON.
- Skills: `system_control` (open app, type/paste) + `file_search`.
- Safety Gate v1: deterministic rules, HUD approval dialog (Tauri), persistent approval queue.
- Audit log (append-only JSONL).

**Exit**: "open notepad and type hello" works end-to-end with a `medium` approval prompt; approvals survive process restart.

---

## Phase 3 — Memory + Learning Tier 0–1 (6–8 weeks)

- lancedb store with typed schema; retrieval in planner.
- FS indexer (incremental, USN journal) for `file` memories.
- Tier 0 explicit rules; Feedback Collector; Tier 1 nightly mining job.
- Learning transparency panel (list / forget / hard-rule).

**Exit**: "never touch D:/photos" is enforced; after 5 identical approvals, the session prompt for that action disappears (visible in audit as applied preference).

---

## Phase 4 — File Intelligence + DevEnv + Hive (8–12 weeks)

- Rust FS scanner (xxHash) + `file_cleanup` skill with trash rollback.
- `dev_env` (toolchain detect, venv/node setup) + `codebase` (tree-sitter + embeddings).
- `hive` skill adapter (email/calendar through Hive's API + HITL mapping).
- Tier 2 macro detection.

**Exit**: duplicate scan of 500k files < 5 min; "set up this repo" creates a working venv; a Hive email draft flows through Aether's approval HUD.

---

## Phase 5 — Beta Packaging (≈ 2 months)

- Tauri bundles: signed `.msi` (Windows first), auto-updater with staged channels.
- First-run onboarding: permissions, model download, wake-word pick, hotkey.
- Encryption at rest (keyring-held key); watchdog + crash recovery.
- Telemetry strictly opt-in; crash reports anonymized.
- 50–100 external beta testers.

**Exit**: crash rate < 1%/week across beta fleet; update-in-place works; uninstall leaves no residue.

---

## Phase 6 — Production v1.0 (≈ 2 months)

- Security pass: threat model doc, `cargo-audit`/`pip-audit` gates, plugin signing.
- Accessibility (keyboard nav, screen-reader labels), i18n scaffolding.
- Docs site, support process, EULA/privacy policy, license decision.
- macOS build (notarized) if resources allow; otherwise v1.1.

**Exit**: public release; onboarding-to-first-successful-task > 80% in usability tests.

---

## Post-1.0

| Version | Highlights |
|---------|-----------|
| v1.x | System anomaly detection (autoencoder), trained file-usefulness classifier, macOS/Linux parity |
| v2.0 | Tier 3 on-device LoRA personalization, speaker verification, team/policy features |

---

## Timeline Summary

| Milestone | Cumulative time (2–3 experienced engineers) |
|-----------|--------------------------------------------|
| Audio PoC | 2 weeks |
| Usable core (Ph. 2–3) | ~4 months |
| Feature-complete beta (Ph. 4–5) | ~7 months |
| **Production v1.0** | **~9 months** |

Solo developer: roughly double. The critical path is Phases 2–3 (planner + safety + memory) — everything else parallelizes.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Local LLM too slow/weak for intent | Fallback chain: rules → tiny model → optional cloud (opt-in) |
| Always-on battery drain | Aggressive idle states; wake-word chip offload where available |
| Windows API churn (UIA) | Wrap in one crate; integration tests on multiple Windows builds |
| Scope creep | Skill registry enforces "new capability = new skill", core stays frozen |
| Solo burnout | Phase gates are shippable products; stop-and-still-useful at every exit |
