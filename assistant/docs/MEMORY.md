# Memory — Schema, Retrieval, Retention

Two tiers: an in-process **session state** and a persistent **vector + metadata store** (lancedb).

---

## 1. Short-Term (Session)

In-memory only, TTL ≈ 30 min of inactivity:

```python
session = {
    "active_windows": [...],       # app, title, pid — sampled by daemon
    "recent_turns": [...],         # last 10 user/assistant turns
    "pending_approvals": [...],
    "current_plan": {...},
    "approved_flags": {...},       # per-skill "asked once this session"
}
```

---

## 2. Long-Term Store

Single lancedb table `memory`, encrypted at rest:

| Column | Type | Notes |
|--------|------|-------|
| `id` | string | UUID |
| `type` | string | `file` \| `action` \| `preference` \| `codebase` \| `conversation` \| `macro` |
| `content` | string | text that gets embedded |
| `embedding` | f32[384] | `all-MiniLM-L6-v2` |
| `metadata` | JSON | per-type schema below |
| `timestamp` | i64 | unix ms, drives recency decay |

### Metadata schemas

```typescript
// file
{ path, size, mtime, hash, tags: string[], project?: string }

// action
{ skill, risk, approved: bool, outcome, duration_ms, applied_preference_id?: string,
  rollback?: { reversible: bool, method, restore_token?, expires? } }

// preference
{ scope,                       // "skill:file_cleanup" | "path:D:/photos" | "global"
  rule,                        // human-readable
  confidence: f32,             // 0..1
  source: "user" | "learned",
  evidence_count: i64,
  hard: bool }                 // hard rules can never be overridden by learning

// codebase
{ repo_path, language, framework?, symbol_count, last_indexed }

// conversation
{ thread_id, role: "user"|"assistant", intent?, entities: string[] }

// macro
{ name, steps: [{skill, args_template}], trigger_phrases: string[], uses: i64 }
```

---

## 3. Retrieval API

```python
def retrieve(
    query: str,
    top_k: int = 8,
    filters: dict | None = None,     # {"type": ["file", "preference"]}
    recency_weight: float = 0.3,     # score = (1-w)*cosine + w*recency
) -> list[MemoryHit]: ...
```

Planner usage per turn:

1. `retrieve(intent_text, filters={"type": ["preference"]})` — always, to load applicable rules.
2. `retrieve(intent_text, filters by routed skill)` — e.g. `file` + `codebase` for dev questions.
3. Hits injected into the planner prompt as structured context blocks (never as instructions).

Performance target: **< 50 ms** per query on laptop CPU.

---

## 4. Write Paths

| Event | Written as |
|-------|-----------|
| Turn completed | `conversation` (user + assistant, summarized if long) |
| Skill executed | `action` with outcome + rollback info |
| User states a rule ("never touch X") | `preference` with `source="user"`, `hard=true` if phrased absolutely |
| Nightly mining finds a pattern | `preference` with `source="learned"` (see LEARNING.md) |
| FS indexer scans | `file` upserts (hash-keyed, incremental via USN journal) |
| Repo indexer runs | `codebase` upserts |
| Macro accepted by user | `macro` |

---

## 5. Retention & Decay

| Type | Policy |
|------|--------|
| `conversation` | Summarize after 7 days; delete raw turns after 30 (configurable) |
| `action` | Keep 90 days full; then keep embedding + outcome only |
| `file` | Evict entries whose path no longer exists (scanner reconciliation) |
| `preference` (learned) | Confidence decays without fresh evidence; below 0.4 → demoted to suggestion; below 0.2 → pruned |
| `preference` (user, hard) | Never auto-pruned |
| `macro` | Unused for 60 days → prompt user to archive |

Global cap ≈ 100k rows; LRU-style pruning on low-value types first.

---

## 6. Privacy Controls

- **Forget item**: settings UI → delete row + tombstone in audit log.
- **Forget scope**: `forget(path="D:/private/**")` removes file/codebase/action entries matching scope.
- **Export**: full JSON export for portability/support.
- **Kill switch**: "Pause all memory writes" toggle for sensitive sessions.
- Store never syncs anywhere unless the user enables (future, E2E-encrypted) sync.
