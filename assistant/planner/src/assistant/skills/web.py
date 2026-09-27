"""Web search skill — opens the default browser with a search query."""

from __future__ import annotations

import re
import webbrowser

from assistant.skills.base import SkillContext, SkillResult


class WebSearchSkill:
    name = "web_search"
    description = "Search the web in the default browser"
    risk_default = "low"

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        if any(v in text for v in ("search for", "search", "google", "look up")):
            # avoid stealing file searches
            if "file" in text:
                return 0.0
            return 0.85
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        query = self._extract_query(context.user_intent)
        if not query:
            return SkillResult(
                status="clarify", clarification_question="What should I search for?"
            )
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return SkillResult(status="ok", output=url, speak=f"Searching for {query}.")

    @staticmethod
    def _extract_query(intent: str) -> str | None:
        m = re.search(
            r"(?:search for|search|google|look up)\s+(.*)", intent, re.IGNORECASE
        )
        if not m:
            return None
        query = m.group(1).strip(" ?.")
        query = re.sub(r"^(the web for|for)\s+", "", query, flags=re.IGNORECASE)
        query = re.sub(r"\s+(in|on)\s+(chrome|edge|the browser)$", "", query, flags=re.IGNORECASE)
        return query or None
