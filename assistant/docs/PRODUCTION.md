# Production Readiness — Packaging, Security, Performance, Compliance

Requirements for shipping Aether to real users (not a class/personal project).

---

## 1. Packaging & Distribution

| Item | Implementation |
|------|----------------|
| Installers | Windows `.msi` (WiX via Tauri bundler) first; macOS `.dmg` notarized; Linux `.AppImage`/`.deb` later |
| Code signing | EV certificate (SmartScreen reputation); Apple Developer ID + notarization |
| Auto-update | Tauri updater, signed manifests, staged rollout (1% → 10% → 100%) |
| Channels | `stable` / `beta` / `nightly` feeds |
| Model delivery | Models downloaded on first run (resumable, checksummed), not bundled — keeps installer < 30 MB |
| Uninstall | Removes service, scheduled tasks, models; asks before deleting user memory/audit data |

---

## 2. Security

| Area | Requirement |
|------|-------------|
| Privilege separation | Planner/UI run as user; daemon elevates per-action via broker + allowlist (ARCHITECTURE.md §3.3) |
| Data at rest | AES-256-GCM for memory store, preferences, audit; key in OS keyring (DPAPI/Keychain/Secret Service) |
| Data in transit | Local IPC only; gRPC over named pipes/UDS with peer authentication; no open TCP ports by default |
| Skill sandboxing | Skills in restricted subprocesses (AppContainer / seccomp); declared permissions (network, paths) enforced |
| Plugin signing | Third-party skills signed; unsigned = dev-mode only, flagged in every approval preview |
| Supply chain | `cargo-audit`, `pip-audit`, pinned lockfiles, SBOM (CycloneDX) generated in CI |
| Secrets | Never in config files; keyring only |
| Threat model | `THREAT_MODEL.md` maintained per release (STRIDE); SAFETY.md §6 is the seed |

---

## 3. Privacy & Compliance

| Item | Policy |
|------|--------|
| Default posture | 100% local; zero network calls without an explicitly enabled skill |
| Telemetry | Opt-in only; anonymized crash dumps (minidump scrubbed of paths/usernames) |
| User data rights | Export-all (JSON), forget-item, forget-scope, full reset — required by GDPR/CCPA if any cloud feature ships |
| Privacy policy + EULA | Required at first launch of any cloud-touching build; reviewed by counsel before v1.0 |
| License | Decide pre-release: Apache-2.0 core + proprietary distribution is a common hybrid |
| Accessibility | WCAG 2.1 AA for HUD/settings; full keyboard navigation; screen-reader labels; captions for spoken output |

---

## 4. Reliability

| Mechanism | Detail |
|-----------|--------|
| Watchdog | Daemon supervises planner (heartbeat, auto-restart with backoff); OS service manager supervises daemon |
| Persistent queues | Approval queue + turn checkpoints in sqlite — crash mid-approval resumes cleanly |
| Transactional actions | High-risk ops: rollback plan recorded **before** execution; failure mid-batch triggers auto-rollback of completed steps |
| Degradation | Missing model → text-only mode; corrupt vector DB → rebuild from audit log; mic busy → hotkey/text mode |
| Crash reporting | Local crash log always; upload only with consent |

---

## 5. Performance Budgets (enforced in CI where possible)

| Metric | Budget |
|--------|--------|
| Idle CPU (daemon + planner) | < 1% average |
| Idle RAM total | < 300 MB (with small LLM resident) |
| Wake → first spoken token | < 800 ms |
| Memory retrieval query | < 50 ms |
| FS event → index update | < 50 ms |
| Approval HUD render | < 100 ms |
| Battery impact | "Low" in Windows battery report; throttle indexing/mining on battery |

Techniques: 4-bit GGUF, ONNX Runtime CPU EP, lazy model loading, mmap'd vectors, ring buffers, real-time audio thread isolation.

---

## 6. Observability

- **Logging**: `tracing` (Rust) + `structlog` (Python), structured JSON, rotating files; local log viewer in settings.
- **Audit**: append-only, hash-chained JSONL (`audit/actions-YYYY-MM.jsonl`) — every action, approval, learned-preference application.
- **Metrics**: local-only counters (latency histograms, undo rate, prompts-per-task) surfaced in a diagnostics panel; exportable for support.

---

## 7. Quality Gates (CI/CD)

| Gate | Tooling |
|------|---------|
| Lint/format | `ruff` + `mypy --strict` (Python); `clippy` + `rustfmt` (Rust) |
| Unit + integration tests | `pytest`, `cargo test`; ≥ 70% coverage on planner, gate, skills |
| E2E | Scripted voice-file → action → approval flows on Windows runner |
| Security | `cargo-audit`, `pip-audit`, secret scanning, SBOM diff |
| Perf regression | Latency benchmarks vs. budgets on reference hardware |
| Release | Tag → build → sign → notarize → staged update feed; reproducible builds goal |

---

## 8. Support & Operations

| Item | Plan |
|------|------|
| Versioning | SemVer; adapters/preferences/memory schemas carry migration versions |
| Docs | User guide + skill-author guide + ADRs (`docs/adr/`) |
| Issue intake | GitHub issues w/ templates; diagnostics bundle export (scrubbed) attachable in one click |
| EOL policy | Last two minor versions receive security fixes |
| Backup/restore | One-file export/import of settings + memory (encrypted archive) |

---

## 9. Pre-Launch Checklist

- [ ] Threat model reviewed & mitigations verified
- [ ] EV cert acquired; signing pipeline green
- [ ] EULA + privacy policy approved
- [ ] Accessibility audit passed (WCAG 2.1 AA)
- [ ] Perf budgets met on min-spec hardware (8 GB RAM, no GPU)
- [ ] Beta crash rate < 1%/week over 4 consecutive weeks
- [ ] Uninstall/reinstall/upgrade matrix tested
- [ ] "Forget everything" verified to leave zero user data
- [ ] Support process staffed and documented
