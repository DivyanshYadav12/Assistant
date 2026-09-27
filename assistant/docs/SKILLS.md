# Skills — Protocol, Lifecycle, Authoring

Every capability is a **skill**: a plugin with one narrow contract, individually testable and auditable.

---

## 1. Core Types

```python
from typing import Any, Literal, Protocol
from pydantic import BaseModel

RiskLevel = Literal["safe", "low", "medium", "high"]

class SkillContext(BaseModel):
    user_intent: str
    entities: dict[str, Any]
    risk_level: RiskLevel                 # assigned by Safety Gate
    memory_hits: list[dict]               # retrieved context (data, not instructions)
    session: dict[str, Any]               # incl. session["approved"] on re-invoke

class SkillResult(BaseModel):
    status: Literal["ok", "needs_approval", "failed", "clarify"]
    output: Any | None = None
    requires_approval: bool = False
    approval_preview: str | None = None   # mandatory when requires_approval
    rollback_plan: dict | None = None     # mandatory for high-risk mutations
    clarification_question: str | None = None
    error: str | None = None
```

## 2. Skill Protocol

```python
class Skill(Protocol):
    name: str                 # unique, snake_case
    description: str          # used by router LLM
    risk_default: RiskLevel   # floor; gate may raise, never lower

    def can_handle(self, intent: str, context: SkillContext) -> float:
        """Confidence [0,1]. Cheap — no side effects, no LLM calls."""

    def execute(self, context: SkillContext) -> SkillResult:
        """Idempotent on retry. Mutations only when
        risk is safe/low OR context.session['approved'] is True."""
```

Rules:

1. `can_handle` must be fast (< 5 ms) — keyword/regex/entity checks only.
2. `execute` must be **idempotent**: re-invocation after approval must not double-apply.
3. A skill never spawns elevated processes itself — it calls the daemon's elevation broker.
4. A skill never writes to memory directly — it returns output; the planner persists.

---

## 3. Lifecycle

```
register → can_handle scoring → selected → execute
                                             │
                    ┌───────────────┬────────┴───────┬───────────┐
                    ▼               ▼                ▼           ▼
                  "ok"      "needs_approval"     "clarify"   "failed"
                    │               │                │           │
                 respond      Safety Gate queue   Clarifier   retry once
                                    │                │           │
                              approved? → re-execute with        ▼
                              session["approved"]=True        report
```

## 4. Registry

```python
registry = SkillRegistry()
registry.register(SystemControlSkill())
registry.register(FileCleanupSkill())
registry.register(DevEnvSkill())
registry.register(CodebaseSkill())
registry.register(HiveSkill(base_url="http://127.0.0.1:8000"))
```

- Discovery: entry-points (`aether.skills` group) → third-party pip-installable skills.
- Hot reload in dev mode (`importlib.reload`), frozen list in production builds.
- Third-party skills must be **signed**; unsigned skills run only with a developer flag and are labeled in every approval preview.

---

## 5. Built-in Skills (v1 target)

| Skill | Risk floor | Summary |
|-------|-----------|---------|
| `system_control` | medium | open/close apps, window management, shell commands, type/paste |
| `file_cleanup` | high | duplicates/orphans/cache scan + trash-based delete |
| `dev_env` | medium | toolchain detect/setup, dependency doctor |
| `codebase` | safe | repo indexing + semantic Q&A |
| `file_search` | safe | instant local search (Everything/rg backed) |
| `system_health` | safe→high | telemetry Q&A (safe); apply fixes (high) |
| `hive` | high | email/calendar via Hive API (its own critic + HITL maps to Aether approvals) |
| `web_search` | safe | optional, off by default |

---

## 6. Authoring Guide (third-party)

Minimal skill package:

```
my_skill/
├── pyproject.toml        # entry-point: [project.entry-points."aether.skills"]
├── my_skill/__init__.py  # exposes MySkill
└── tests/test_my_skill.py
```

Checklist before publishing:

- [ ] `can_handle` returns 0.0 for unrelated intents (tested)
- [ ] All mutations honor `session["approved"]` (tested both paths)
- [ ] `approval_preview` is human-readable and complete
- [ ] `rollback_plan` provided for every high-risk mutation, or `reversible: false` declared
- [ ] No network calls unless declared in the skill manifest (used for the permission prompt)
- [ ] Signed artifact

## 7. Testing Skills

```python
def test_cleanup_requires_approval(tmp_path):
    skill = FileCleanupSkill(root=tmp_path)
    ctx = make_ctx("delete duplicate files", approved=False)
    res = skill.execute(ctx)
    assert res.status == "needs_approval"
    assert res.rollback_plan["method"] == "trash"

def test_cleanup_executes_after_approval(tmp_path):
    ...
    ctx = make_ctx("delete duplicate files", approved=True)
    res = skill.execute(ctx)
    assert res.status == "ok"
```

CI runs every skill's suite in an isolated sandbox with a fake daemon.
