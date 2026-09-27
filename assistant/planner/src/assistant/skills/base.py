"""Skill protocol and core types (see docs/SKILLS.md)."""

from __future__ import annotations

from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

RiskLevel = Literal["safe", "low", "medium", "high"]

RISK_ORDER: dict[str, int] = {"safe": 0, "low": 1, "medium": 2, "high": 3}


class SkillContext(BaseModel):
    user_intent: str
    entities: dict[str, Any] = {}
    risk_level: RiskLevel = "safe"
    session: dict[str, Any] = {}


class SkillResult(BaseModel):
    status: Literal["ok", "needs_approval", "failed", "clarify"]
    output: Any | None = None
    speak: str | None = None  # short sentence for TTS/print
    requires_approval: bool = False
    approval_preview: str | None = None
    rollback_plan: dict[str, Any] | None = None
    clarification_question: str | None = None
    error: str | None = None


@runtime_checkable
class Skill(Protocol):
    name: str
    description: str
    risk_default: RiskLevel

    def can_handle(self, intent: str, context: SkillContext) -> float:
        """Confidence [0,1]; must be fast and side-effect free."""
        ...

    def execute(self, context: SkillContext) -> SkillResult:
        """Idempotent; mutations only when risk is safe/low or
        context.session.get('approved') is True."""
        ...


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def all(self) -> list[Skill]:
        return list(self._skills.values())

    def route(self, intent: str, context: SkillContext) -> list[tuple[Skill, float]]:
        """Return skills scored >= 0.3, best first."""
        scored = [
            (s, s.can_handle(intent, context)) for s in self._skills.values()
        ]
        matches = [(s, c) for s, c in scored if c >= 0.3]
        matches.sort(key=lambda t: t[1], reverse=True)
        return matches
