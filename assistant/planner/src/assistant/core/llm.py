"""Local LLM intent classification via Ollama (http://localhost:11434).

The LLM picks the best skill and extracts entities from free-form phrasing.
If Ollama is unreachable or answers garbage, the caller falls back to
keyword routing — the assistant never breaks because the LLM is down.

Now uses adaptive model selection for better conversation quality.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import structlog
from pydantic import BaseModel, ValidationError

log = structlog.get_logger()

OLLAMA_URL = os.environ.get("AETHER_OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("AETHER_LLM_MODEL", "qwen2.5:1.5b-instruct")
SMART_MODEL = os.environ.get("AETHER_SMART_MODEL", "llama3:8b")
CLASSIFY_TIMEOUT = int(os.environ.get("AETHER_LLM_CLASSIFY_TIMEOUT", "45"))
CHAT_TIMEOUT = int(os.environ.get("AETHER_LLM_CHAT_TIMEOUT", "60"))


class IntentResult(BaseModel):
    skill: str
    confidence: float
    entities: dict[str, str] = {}
    clarification: str | None = None


_SYSTEM_PROMPT = """You are the intent router of a desktop voice assistant.
Given a user request, pick exactly ONE skill and extract entities.

Available skills:
{skills}

Rules:
- Reply with ONLY a JSON object, no other text.
- Schema: {{"skill": "<name>", "confidence": 0.0-1.0, "entities": {{...}}, "clarification": null}}
- If no skill fits, use skill "none" with low confidence.
- If the request is ambiguous, set "clarification" to ONE short question.
- Entity keys: app, filename, location, content, query, search_term (only those that apply).
- IMPORTANT: Use "code_generation" for requests about programs, functions, algorithms, or code.
- IMPORTANT: Use "type_text" only for literal text/notes, NOT for code.

Examples:
"could you jot down milk and eggs somewhere" -> {{"skill": "type_text", "confidence": 0.85, "entities": {{"content": "milk and eggs"}}, "clarification": null}}
"write a program to add two numbers" -> {{"skill": "code_generation", "confidence": 0.92, "entities": {{"task": "add two numbers"}}, "clarification": null}}
"write a function to calculate factorial" -> {{"skill": "code_generation", "confidence": 0.9, "entities": {{"task": "calculate factorial"}}, "clarification": null}}
"generate python code for a loop" -> {{"skill": "code_generation", "confidence": 0.9, "entities": {{"task": "loop"}}, "clarification": null}}
"get rid of that old report doc on my desktop" -> {{"skill": "file_ops", "confidence": 0.9, "entities": {{"filename": "report.docx", "location": "desktop"}}, "clarification": null}}
"whats the weather like" -> {{"skill": "web_search", "confidence": 0.8, "entities": {{"query": "weather"}}, "clarification": null}}
"check my inbox" -> {{"skill": "hive", "confidence": 0.9, "entities": {{}}, "clarification": null}}
"schedule a meeting with John tomorrow at 3pm" -> {{"skill": "hive", "confidence": 0.9, "entities": {{}}, "clarification": null}}
"what is the capital of france" -> {{"skill": "chat", "confidence": 0.85, "entities": {{}}, "clarification": null}}
"tell me a joke" -> {{"skill": "chat", "confidence": 0.9, "entities": {{}}, "clarification": null}}
"""


def is_available() -> bool:
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
        return any(m["name"].startswith(MODEL.split(":")[0]) for m in data.get("models", []))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return False


def classify(transcript: str, skill_descriptions: dict[str, str]) -> IntentResult | None:
    """Ask the local LLM to route. Returns None on any failure (caller falls back)."""
    skills_block = "\n".join(f"- {name}: {desc}" for name, desc in skill_descriptions.items())
    payload = {
        "model": MODEL,
        "system": _SYSTEM_PROMPT.format(skills=skills_block),
        "prompt": transcript,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for consistent classification
            "num_predict": 200,  # Small output for speed
            "num_ctx": 1024,  # Small context for speed
            "top_k": 10,  # Limited sampling for speed
        },
    }
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=CLASSIFY_TIMEOUT) as resp:  # Increased from 30s to 45s
            body = json.loads(resp.read())
        raw = json.loads(body["response"])
        if raw.get("entities") is None:
            raw["entities"] = {}
        result = IntentResult.model_validate(raw)
        log.info("llm_intent", skill=result.skill, confidence=result.confidence,
                 entities=result.entities)
        return result
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError,
            ValidationError) as e:
        log.warning("llm_classify_failed", error=str(e))
        return None


_CHAT_SYSTEM = """You are Aether, a friendly and intelligent desktop assistant.
You talk like a human — warm, concise, and helpful. Keep replies short (1-3 sentences).
You can answer general knowledge questions, give opinions, tell jokes, explain concepts,
and have casual conversation. You are not robotic — use natural language.

If the user asks you to DO something (open an app, create a file, do math), say you
can't do that directly and suggest they phrase it as a command.

You know the current time: {current_time}
"""


def chat(user_message: str, history: list[dict] | None = None) -> str | None:
    """Generate a human-like conversational response via Ollama.

    Uses the smart model (8B) for better conversation quality.
    Falls back to fast model (1.5B) if smart model unavailable.

    Args:
        user_message: What the user said.
        history: List of {"role": "user"/"assistant", "content": "..."} dicts
                 for conversation context (last 6 turns max).

    Returns: The assistant's reply text, or None on failure.
    """
    from datetime import datetime

    now = datetime.now().strftime("%I:%M %p, %B %d")
    system = _CHAT_SYSTEM.format(current_time=now)

    # Build conversation context from history
    context_parts = []
    if history:
        for turn in history[-6:]:  # last 6 turns for context
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role == "user":
                context_parts.append(f"User: {content}")
            else:
                context_parts.append(f"Aether: {content}")
    context_parts.append(f"User: {user_message}")

    prompt = "\n".join(context_parts)

    # Try smart model first for better conversation quality
    model_to_use = SMART_MODEL
    payload = {
        "model": model_to_use,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.6,  # Lower for faster, more deterministic responses
            "num_predict": 300,  # Reduced from 500 for faster generation
            "num_ctx": 2048,  # Reduced context window for faster processing
            "top_k": 20,  # Limit to top tokens for faster sampling
            "top_p": 0.9,  # Nucleus sampling for faster generation
        },
    }
    
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=CHAT_TIMEOUT) as resp:  # Increased from 30s to 60s
            body = json.loads(resp.read())
        reply = body["response"].strip()
        # Strip any "Aether:" prefix the model might add
        if reply.lower().startswith("aether:"):
            reply = reply[7:].strip()
        log.info("llm_chat", model=model_to_use, reply_len=len(reply))
        return reply
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e:
        log.warning("llm_chat_failed_smart", model=model_to_use, error=str(e))
        # Fallback to fast model
        log.info("llm_chat_fallback", model=MODEL)
        payload["model"] = MODEL
        payload["options"] = {
            "temperature": 0.6,
            "num_predict": 200,  # Reduced for faster fallback
            "num_ctx": 1024,  # Smaller context for speed
            "top_k": 10,
        }
        try:
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/generate",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read())
            reply = body["response"].strip()
            if reply.lower().startswith("aether:"):
                reply = reply[7:].strip()
            log.info("llm_chat", model=MODEL, reply_len=len(reply))
            return reply
        except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e2:
            log.warning("llm_chat_failed_fallback", error=str(e2))
            return None
