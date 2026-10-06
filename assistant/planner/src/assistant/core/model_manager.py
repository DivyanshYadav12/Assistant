"""Adaptive model manager - routes tasks to appropriate models.

Architecture:
- Tier 1 (Fast): qwen2.5:1.5b-instruct - Simple commands, routing
- Tier 2 (Smart): llama3.1:8b-instruct - Conversation, coding, knowledge
- Tier 3 (Cloud): OpenAI GPT-4o/Claude 3.5 - Complex reasoning (with approval)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from enum import Enum
from typing import Any

import structlog

log = structlog.get_logger()

OLLAMA_URL = os.environ.get("AETHER_OLLAMA_URL", "http://127.0.0.1:11434")
FAST_MODEL = os.environ.get("AETHER_FAST_MODEL", "qwen2.5:1.5b-instruct")
SMART_MODEL = os.environ.get("AETHER_SMART_MODEL", "llama3:8b")
CLOUD_API_KEY = os.environ.get("AETHER_CLOUD_API_KEY", "")  # Optional
CLOUD_PROVIDER = os.environ.get("AETHER_CLOUD_PROVIDER", "openai")  # openai or anthropic


class TaskComplexity(Enum):
    LOW = "low"      # Simple commands, routing
    MEDIUM = "medium"  # Conversation, coding, knowledge
    HIGH = "high"    # Complex reasoning, requires approval


class ModelTier(Enum):
    FAST = "fast"    # 1.5B model
    SMART = "smart"  # 8B model
    CLOUD = "cloud"  # API-based


class ModelManager:
    """Manages adaptive model selection based on task complexity."""
    
    def __init__(self) -> None:
        self.session_stats = {
            "fast_queries": 0,
            "smart_queries": 0,
            "cloud_queries": 0,
        }
    
    def classify_complexity(self, transcript: str, skill: str | None = None) -> TaskComplexity:
        """Determine task complexity based on transcript and skill."""
        transcript_lower = transcript.lower()
        
        # High complexity indicators
        high_complexity_keywords = [
            "explain how", "why does", "analyze", "compare", "implement",
            "design", "architecture", "algorithm", "complex", "optimize",
            "debug", "refactor", "write a function", "create a class",
        ]
        
        # Medium complexity indicators
        medium_complexity_keywords = [
            "what is", "how do", "tell me about", "explain", "describe",
            "code", "python", "javascript", "help me with", "knowledge",
            "conversation", "chat", "discuss",
        ]
        
        # Skill-based complexity
        high_complexity_skills = ["chat", "coding", "analysis"]
        medium_complexity_skills = ["web_search", "hive", "math"]
        
        # Check for high complexity
        if any(kw in transcript_lower for kw in high_complexity_keywords):
            return TaskComplexity.HIGH
        if skill in high_complexity_skills:
            return TaskComplexity.HIGH
        
        # Check for medium complexity
        if any(kw in transcript_lower for kw in medium_complexity_keywords):
            return TaskComplexity.MEDIUM
        if skill in medium_complexity_skills:
            return TaskComplexity.MEDIUM
        
        # Default to low (simple commands)
        return TaskComplexity.LOW
    
    def select_model(self, complexity: TaskComplexity, require_approval: bool = False) -> ModelTier:
        """Select appropriate model based on complexity and approval requirements."""
        if complexity == TaskComplexity.HIGH:
            if CLOUD_API_KEY and require_approval:
                return ModelTier.CLOUD
            return ModelTier.SMART
        
        if complexity == TaskComplexity.MEDIUM:
            return ModelTier.SMART
        
        return ModelTier.FAST
    
    def query_fast(self, prompt: str, system: str = "") -> str | None:
        """Query the fast model (Tier 1)."""
        self.session_stats["fast_queries"] += 1
        return self._query_ollama(FAST_MODEL, prompt, system, temperature=0.1, max_tokens=200)
    
    def query_smart(self, prompt: str, system: str = "", temperature: float = 0.7) -> str | None:
        """Query the smart model (Tier 2)."""
        self.session_stats["smart_queries"] += 1
        return self._query_ollama(SMART_MODEL, prompt, system, temperature=temperature, max_tokens=500)
    
    def query_cloud(self, prompt: str, system: str = "") -> str | None:
        """Query cloud API (Tier 3) - requires approval."""
        if not CLOUD_API_KEY:
            log.warning("cloud_api_not_configured")
            return None
        
        self.session_stats["cloud_queries"] += 1
        
        if CLOUD_PROVIDER == "openai":
            return self._query_openai(prompt, system)
        elif CLOUD_PROVIDER == "anthropic":
            return self._query_anthropic(prompt, system)
        else:
            log.warning("unknown_cloud_provider", provider=CLOUD_PROVIDER)
            return None
    
    def _query_ollama(self, model: str, prompt: str, system: str, temperature: float, max_tokens: int) -> str | None:
        """Query Ollama API."""
        payload = {
            "model": model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
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
            log.info("ollama_query", model=model, reply_len=len(reply))
            return reply
        except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e:
            log.warning("ollama_query_failed", model=model, error=str(e))
            return None
    
    def _query_openai(self, prompt: str, system: str) -> str | None:
        """Query OpenAI API."""
        try:
            import openai
            
            client = openai.OpenAI(api_key=CLOUD_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()
            log.info("openai_query", reply_len=len(reply))
            return reply
        except ImportError:
            log.warning("openai_not_installed")
            return None
        except Exception as e:
            log.warning("openai_query_failed", error=str(e))
            return None
    
    def _query_anthropic(self, prompt: str, system: str) -> str | None:
        """Query Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=CLOUD_API_KEY)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            reply = response.content[0].text.strip()
            log.info("anthropic_query", reply_len=len(reply))
            return reply
        except ImportError:
            log.warning("anthropic_not_installed")
            return None
        except Exception as e:
            log.warning("anthropic_query_failed", error=str(e))
            return None
    
    def get_stats(self) -> dict[str, Any]:
        """Get session statistics."""
        return self.session_stats.copy()


# Singleton
_manager: ModelManager | None = None


def get_manager() -> ModelManager:
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager
