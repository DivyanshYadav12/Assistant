"""Planner loop v1: transcript -> route -> gate -> execute -> respond.

Rule-based routing for Phase 2; LLM-based intent classification replaces
the router scoring in a later phase without changing this loop.
"""

from __future__ import annotations

import re

import structlog

from assistant.audit import get_log
from assistant.core import gate, llm
from assistant.core.approval_queue import get_queue
from assistant.learning import get_collector, get_preferences
from assistant.memory import get_store
from assistant.skills.base import SkillContext, SkillRegistry, SkillResult
from assistant.skills.builtin import (
    FileSearchSkill,
    OpenAppSkill,
    TimeSkill,
    TypeTextSkill,
)
from assistant.skills.cleanup import FileCleanupSkill
from assistant.skills.file_ops import FileOpsSkill, UndoSkill
from assistant.skills.hive import HiveSkill
from assistant.skills.math import MathSkill, NotepadSolveSkill
from assistant.skills.system import SystemControlSkill
from assistant.skills.web import WebSearchSkill

log = structlog.get_logger()


def build_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(TimeSkill())
    registry.register(OpenAppSkill())
    registry.register(TypeTextSkill())
    registry.register(FileSearchSkill())
    registry.register(FileOpsSkill())
    registry.register(UndoSkill())
    registry.register(WebSearchSkill())
    registry.register(MathSkill())
    registry.register(NotepadSolveSkill())
    registry.register(HiveSkill())
    registry.register(SystemControlSkill())
    registry.register(FileCleanupSkill())
    return registry


_STEP_SPLIT = re.compile(r"\s+(?:and then|then|and)\s+", re.IGNORECASE)


class Planner:
    def __init__(self) -> None:
        self.registry = build_registry()
        self.session: dict = {}
        self.chat_history: list[dict] = []
        self.llm_enabled = llm.is_available()
        self.memory = get_store()
        self.audit = get_log()
        self.feedback = get_collector()
        self.preferences = get_preferences()
        self.approval_queue = get_queue()
        # Expire any stale approvals from a previous session
        self.approval_queue.expire_stale()
        pending = self.approval_queue.count_pending()
        if pending:
            log.info("pending_approvals_restored", count=pending)
        log.info("planner_ready", llm_routing=self.llm_enabled)

    def handle(self, transcript: str) -> str:
        """Process one user turn; supports multi-step commands ("X and then Y")."""
        steps = self._split_steps(transcript)
        if len(steps) > 1:
            log.info("multi_step", steps=steps)
            replies = [self._handle_step(s) for s in steps]
            return " ".join(replies)
        return self._handle_step(transcript)

    def _split_steps(self, transcript: str) -> list[str]:
        """Split on and/then only if EVERY part routes to a skill on its own —
        so "write cats and dogs in notepad" stays one step."""
        parts = [p.strip() for p in _STEP_SPLIT.split(transcript) if p.strip()]
        if len(parts) < 2:
            return [transcript]
        probe = SkillContext(user_intent="", session=self.session)
        for part in parts:
            if not self.registry.route(part, probe):
                return [transcript]
        return parts

    def _handle_step(self, transcript: str) -> str:
        context = SkillContext(user_intent=transcript, session=self.session)

        # Retrieve relevant memories for this intent
        memory_hits = self.memory.retrieve(
            transcript, top_k=5, filters={"type": ["preference", "action", "conversation"]}
        )
        context.session["memory_hits"] = memory_hits

        # Check for explicit user rules (Tier 0)
        rules = self._check_rules(transcript)
        if rules:
            for rule in rules:
                if rule.get("block"):
                    self.audit.append("rule_blocked", {
                        "intent": transcript,
                        "rule": rule["rule"],
                    })
                    return f"I won't do that — you told me: {rule['rule']}"

        skill, confidence = self._route(transcript, context)
        if skill is None:
            # Fallback: human-like conversation via LLM
            reply = self._chat_fallback(transcript)
            # Persist conversation to memory
            self.memory.write(
                type="conversation",
                content=f"User: {transcript}\nAssistant: {reply}",
                metadata={"role": "user+assistant"},
            )
            self.audit.append("conversation", {"intent": transcript, "reply": reply[:200]})
            return reply

        risk = gate.classify_risk(transcript, skill)
        context.risk_level = risk
        log.info("routed", skill=skill.name, confidence=confidence, risk=risk)

        result = skill.execute(context)

        if result.status == "needs_approval":
            # Check learned preferences for auto-approve (Tier 1)
            learned_auto = self._check_learned_auto_approve(skill.name, risk)
            if learned_auto:
                approved = True
                self.audit.append("learned_auto_approve", {
                    "skill": skill.name,
                    "preference_id": learned_auto,
                })
            elif gate.auto_approvable(risk, self.session):
                approved = True
            else:
                # Enqueue to persistent queue (survives crash/restart)
                approval_id = self.approval_queue.enqueue(
                    skill=skill.name,
                    intent=transcript,
                    risk=risk,
                    preview=result.approval_preview or transcript,
                    rollback_plan=result.rollback_plan,
                )
                approved = gate.request_approval(
                    result.approval_preview or transcript, risk
                )
                # Resolve in the queue
                self.approval_queue.resolve(approval_id, approved)
                if approved and risk == "medium":
                    self.session["medium_approved_this_session"] = True

            # Record feedback signal
            self.feedback.record(
                intent=transcript, skill=skill.name, confidence=confidence,
                risk=risk, decision="approve" if approved else "reject",
            )
            self.audit.append("approval", {
                "skill": skill.name, "risk": risk,
                "approved": approved, "preview": result.approval_preview or transcript,
            })

            if not approved:
                return "Okay, cancelled."
            context.session["approved"] = True
            result = skill.execute(context)
            context.session.pop("approved", None)

        if result.rollback_plan:
            self.session.setdefault("rollback_stack", []).append(result.rollback_plan)

        reply = self._respond(result)

        # Track conversation context
        self.chat_history.append({"role": "user", "content": transcript})
        self.chat_history.append({"role": "assistant", "content": reply})

        # Persist action to memory + audit
        self.memory.write(
            type="action",
            content=f"{skill.name}: {transcript} -> {result.status}",
            metadata={
                "skill": skill.name,
                "risk": risk,
                "outcome": result.status,
                "rollback": result.rollback_plan,
            },
        )
        self.audit.append("action", {
            "skill": skill.name,
            "intent": transcript,
            "risk": risk,
            "outcome": result.status,
            "rollback": result.rollback_plan,
        })

        # Record feedback signal for executed actions
        if result.status != "needs_approval":
            self.feedback.record(
                intent=transcript, skill=skill.name, confidence=confidence,
                risk=risk, decision="executed", outcome=result.status,
            )

        return reply

    def _check_rules(self, transcript: str) -> list[dict]:
        """Check explicit user rules (Tier 0) that might block this action."""
        text = transcript.lower()
        rules = self.preferences.get_all()
        matched = []
        for pref in rules:
            if pref["source"] != "user":
                continue
            rule_text = pref["rule"].lower()
            # Simple matching: if rule contains "never" or "don't" and the intent matches the scope
            if any(w in rule_text for w in ("never", "don't", "do not", "avoid")):
                # Check if the rule's scope keywords appear in the intent
                scope_parts = pref["scope"].split(":")
                for part in scope_parts:
                    if part in text or part in rule_text:
                        matched.append({"rule": pref["rule"], "block": True, "id": pref["id"]})
                        self.preferences.mark_used(pref["id"])
                        break
        return matched

    def _check_learned_auto_approve(self, skill_name: str, risk: str) -> str | None:
        """Check if a learned preference allows auto-approving this skill.
        Only applies to medium risk — never high (see SAFETY.md §5).
        """
        if risk != "medium":
            return None
        prefs = self.preferences.get_rules_for_skill(skill_name)
        for pref in prefs:
            if pref["source"] != "learned":
                continue
            if "auto-approve" in pref["rule"].lower() and pref["confidence"] >= 0.9:
                self.preferences.mark_used(pref["id"])
                return pref["id"]
        return None

    def add_rule(self, rule_text: str, scope: str = "global", hard: bool = True) -> str:
        """Add an explicit user rule (Tier 0). Called when user says
        'never touch X' or 'always approve Y'."""
        pid = self.preferences.add_rule(scope=scope, rule=rule_text, hard=hard)
        self.audit.append("rule_added", {"scope": scope, "rule": rule_text})
        return pid

    def mine_preferences(self) -> list[dict]:
        """Run Tier 1 preference mining on collected feedback signals."""
        from assistant.learning import get_miner
        miner = get_miner()
        signals = self.feedback.get_signals()
        results = miner.mine(signals)
        self.audit.append("preference_mining", {"signals": len(signals), "detected": len(results)})
        return results

    def detect_macros(self) -> list[dict]:
        """Run Tier 2 macro detection on collected action signals.

        Returns proposed macros (not yet accepted). User can accept them
        via the planner or UI to create reusable shortcuts.
        """
        from assistant.learning import get_macro_detector
        detector = get_macro_detector()
        signals = self.feedback.get_signals()
        proposals = detector.detect(signals)
        self.audit.append("macro_detection", {"signals": len(signals), "proposals": len(proposals)})
        return proposals

    def get_macro_proposals(self) -> list[dict]:
        """Get pending macro proposals for user review."""
        from assistant.learning import get_macro_store
        return get_macro_store().get_proposed_macros()

    def accept_macro(self, macro_id: str) -> bool:
        """Accept a proposed macro so it can be triggered by voice."""
        from assistant.learning import get_macro_store
        ok = get_macro_store().accept_macro(macro_id)
        if ok:
            self.audit.append("macro_accepted", {"macro_id": macro_id})
        return ok

    def _chat_fallback(self, transcript: str) -> str:
        """When no skill matches, use LLM for human-like conversation."""
        if self.llm_enabled:
            reply = llm.chat(transcript, self.chat_history)
            if reply:
                self.chat_history.append({"role": "user", "content": transcript})
                self.chat_history.append({"role": "assistant", "content": reply})
                # Keep history bounded
                if len(self.chat_history) > 20:
                    self.chat_history = self.chat_history[-20:]
                return reply
        return "I'm not sure how to help with that. You can ask me to open apps, do math, create files, or just chat."

    def _route(self, transcript: str, context: SkillContext):
        """Fast keyword check first; LLM only for ambiguous commands."""
        # Fast path: try keyword routing first for obvious commands
        matches = self.registry.route(transcript, context)
        if matches and matches[0][1] >= 0.85:
            return matches[0][0], matches[0][1]
        # Slow path: LLM for free-form / ambiguous commands
        if self.llm_enabled:
            descriptions = {s.name: s.description for s in self.registry.all()}
            descriptions["chat"] = "General conversation, questions, jokes, explanations, opinions, casual chat"
            intent = llm.classify(transcript, descriptions)
            if intent and intent.skill == "chat" and intent.confidence >= 0.5:
                # Route to conversation fallback
                return None, 0.0
            if intent and intent.skill != "none" and intent.skill != "chat" and intent.confidence >= 0.6:
                # Web search needs higher confidence — small LLM confuses knowledge Q&A with web search
                if intent.skill == "web_search" and intent.confidence < 0.85:
                    return None, 0.0  # let it fall through to chat
                for s in self.registry.all():
                    if s.name == intent.skill:
                        context.entities = dict(intent.entities)
                        return s, intent.confidence
        # Fallback: use whatever keyword match we had (even if weak)
        if matches:
            return matches[0]
        return None, 0.0

    @staticmethod
    def _respond(result: SkillResult) -> str:
        if result.status == "ok":
            reply = result.speak or "Done."
            if isinstance(result.output, list) and result.output:
                reply += "\n" + "\n".join(f"  - {item}" for item in result.output)
            return reply
        if result.status == "clarify":
            return result.clarification_question or "Can you give me more detail?"
        if result.status == "failed":
            return result.speak or f"That failed: {result.error}"
        return "Something unexpected happened."
