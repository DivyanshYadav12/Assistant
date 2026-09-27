# Self-Learning — Tiers, Mining, Adaptation

Aether improves from user behavior **locally**, with full transparency and per-item forgetting. No cloud training, no silent drift.

---

## 1. Learning Tiers

| Tier | Mechanism | Update cadence | Ship phase |
|------|-----------|----------------|-----------|
| **0** | Explicit rules ("always approve X", "never touch Y") | Immediate | MVP |
| **1** | Implicit preference mining from approvals/rejections/clarifications | Nightly batch | Beta |
| **2** | Workflow macro detection from repeated action sequences | Weekly | Beta |
| **3** | On-device LoRA adaptation of the intent/risk LLM | Monthly, user-triggered | v2.0+ |

---

## 2. Signals Collected (Feedback Collector)

Every turn logs (locally, into `action`/`conversation` memory):

- intent text → routed skill + confidence
- risk level assigned → user decision (approve / reject / modify / timeout)
- clarification question → which option the user chose
- undo events (strong negative signal)
- explicit corrections ("no, I meant …")

---

## 3. Tier 1 — Preference Mining (nightly)

```
1. AGGREGATE actions by (skill, context_signature)
   context_signature = hash(entities_subset + time_bucket + active_app)

2. COMPUTE per group:
   approval_rate, rejection_rate, modal_clarification_choice, undo_rate

3. DETECT:
   approval_rate ≥ 0.9 ∧ n ≥ 5  →  preference{auto_relax medium friction, conf=rate}
   rejection_rate ≥ 0.7 ∧ n ≥ 3 →  preference{raise risk / always-ask, conf=rate}
   modal_choice ≥ 0.8           →  preference{default entity value}
   undo_rate ≥ 0.3              →  preference{always-ask + never auto-relax}

4. STORE as memory type=preference, source="learned",
   with evidence_count and last_updated.
```

Guard rails:

- Learned preferences **can never** relax `high` risk (see SAFETY.md §5).
- Confidence decays over time without fresh evidence (MEMORY.md §5).
- Every application of a learned preference is stamped into the audit log (`applied_preference_id`).

---

## 4. Tier 2 — Macro Detection (weekly)

```
Input:  session action logs (skill_id sequences with timestamps)
Method: frequent-sequence mining (PrefixSpan-style) with constraints:
        gap ≤ 60 s between steps, length 2–6, support ≥ 3 occurrences / 14 days
Output: candidate macro {steps, args_template, suggested trigger phrase}
```

UX: HUD proposes — "You often do these 3 steps together. Create macro 'Email to Notepad'?" Accept → stored as `macro` memory; replay always passes through the Safety Gate (a macro containing a `high` step still requires approval each run).

---

## 5. Tier 3 — On-Device LoRA (optional, v2.0+)

- **Base**: the small intent/risk model (Phi-3-mini / Gemma-2B, 4-bit).
- **Data**: (utterance → corrected intent) pairs and (action context → user decision) pairs harvested from Tier-1 logs; ~500+ examples before first run.
- **Method**: QLoRA on-device; GPU ≈ 30–60 min, CPU allowed overnight. Adapter saved as `learning/user_lora.safetensors`.
- **Inference**: base + adapter merged at load; A/B check against held-out user examples — adapter only activates if it beats base accuracy.
- **Controls**: opt-in toggle, "Reset learning" deletes adapter, adapter never leaves the device.

---

## 6. Transparency UX (required for all tiers)

Settings → **Learning** panel:

| Element | Behavior |
|---------|----------|
| Learned preferences list | rule, confidence, evidence count, last used |
| Per-item actions | Forget • Convert to hard rule • Pin (no decay) |
| Global toggle | "Learn from my behavior" (on/off) |
| Reset | "Forget everything learned" (Tier 1–3 wipe, Tier 0 user rules kept) |
| Audit link | Jump to actions where a given preference was applied |

---

## 7. Evaluation

- **Offline**: replay historical logs → would the learned preferences have reduced prompts without causing undos? Report weekly precision/recall in a local dashboard.
- **Online**: track prompts-per-task and undo-rate trends; regression alarms if undo-rate rises after a mining run (auto-rollback that run's preferences).
- **CI**: synthetic user-log fixtures verify mining logic deterministically.
