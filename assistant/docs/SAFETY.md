# Safety Gate — Risk Classification, Approval, Rollback

The Safety Gate is the single choke point between "the planner wants to do X" and "X actually happens". No skill may mutate state without passing through it.

---

## 1. Risk Levels

| Level | Criteria | Default policy |
|-------|----------|----------------|
| `safe` | Read-only, no side effects | Auto-execute |
| `low` | Creates temp/cache, opens apps, reversible UI actions | Auto-execute + audit log |
| `medium` | Modifies user files/settings, installs user-scope packages | Ask once per session (configurable to "always ask") |
| `high` | Deletes data, sends external comms, runs untrusted code, privileged system changes | **Always** explicit approval + preview; cannot be bypassed — not by config, not by learned preference |

---

## 2. Classification Pipeline

```
Action proposal
      │
      ▼
┌───────────────────┐   match   ┌──────────────┐
│ Deterministic     ├──────────►│ risk_level   │
│ rules (fast path) │           └──────────────┘
└─────────┬─────────┘
          │ no match / ambiguous
          ▼
┌───────────────────┐
│ LLM judge         │  prompt: action, targets, reversibility, blast radius
│ (local model)     │  output: {risk_level, confidence, rationale}
└─────────┬─────────┘
          │ confidence < 0.6
          ▼
   treat as `high`   ← fail-closed, never fail-open
```

### Deterministic rules (excerpt)

| Pattern | Risk |
|---------|------|
| `read`, `list`, `search`, `summarize` verbs, no write targets | `safe` |
| Target under `%TEMP%`, browser cache dirs | `low` |
| Write/move within user profile, non-hidden files | `medium` |
| `delete`/`rm` anything, `send` to external address, registry/service/firewall change, `curl \| sh` equivalents | `high` |
| Target matches user's protected-path list | `high` (hard rule) |

---

## 3. Approval Flow

```
needs approval
      │
      ▼
┌────────────────────────┐
│ Approval queue         │  persistent (sqlite) — survives restart
│ {action, preview,      │
│  rationale, rollback}  │
└─────────┬──────────────┘
          │ notify via configured channels
          ▼
  Voice ("approve" / "reject")  •  HUD buttons  •  Tray menu
          │
   ┌──────┴────────┬──────────────┐
   ▼               ▼              ▼
Approve         Reject         Modify
   │               │              │
   ▼               ▼              ▼
Execute +      Abort, log     Re-plan with
store rollback                user's edit
```

Rules:

- **Preview is mandatory** for `high`: human-readable summary + affected targets (diff for file edits, recipient/body for sends).
- **Timeout**: unanswered approvals expire after a configurable window (default 10 min) → action aborted, user notified.
- **Voice approval** requires the wake session to still be active (no stale "yes" hijacking).
- **Batching**: a multi-step plan shows one consolidated preview; any `high` step forces the whole batch to `high`.

---

## 4. Rollback Design

Every `high` action must supply a rollback plan **before** execution:

```json
{
  "kind": "file_delete",
  "targets": ["D:/projects/old/node_modules"],
  "reversible": true,
  "method": "trash",
  "restore_token": "trash://uuid-1234",
  "expires": "2026-09-15T00:00:00Z"
}
```

| Action kind | Rollback method |
|-------------|-----------------|
| File delete | Move to app-managed trash; restore by token |
| File edit | Pre-image stored (content-addressed); restore bytes |
| Setting/registry change | Pre-value snapshot; write back |
| Package install | Uninstall command recorded |
| Email send | **Not reversible** → preview is strictly enforced; rollback = follow-up draft |
| Elevated system change | Daemon snapshots (e.g., service state) before applying |

Non-reversible actions are labeled `reversible: false` in the preview so the user knows before approving.

Undo UX: "undo that" / "undo last 3" → executor replays inverse operations from the audit log, newest first.

---

## 5. Interaction with Learning

- Learned preferences may **lower friction** for `medium` (e.g., stop re-asking each session) — never for `high`.
- A learned preference can **raise** risk ("always ask before touching D:/photos") — hard rules always win over learned ones.
- Every learned auto-approval logs `applied_preference_id` in the audit entry for traceability.

---

## 6. Threat Model (summary)

| Threat | Mitigation |
|--------|-----------|
| Prompt injection via file contents / window titles | Skill inputs sanitized; planner treats retrieved text as data, not instructions; high-risk still gated by human |
| Malicious skill plugin | Skills run in restricted subprocesses; privileged ops only via daemon allowlist; plugin signing for third-party skills |
| Stale/replayed approval | Approvals bound to action hash + expiry; resolving twice is a no-op |
| Audio hijack ("yes" from TV) | Voice approval only within active session + optional speaker verification (post-MVP) |
| Tampering with audit log | Append-only, hash-chained entries; separate file ACLs |

Full threat model to be maintained as `THREAT_MODEL.md` once implementation starts (see PRODUCTION.md).
