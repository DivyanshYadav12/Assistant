"""Aether Dashboard - FastAPI Backend

Provides REST API and WebSocket for the web dashboard.
Runs on port 8001 (separate from planner on 48100).
"""

from __future__ import annotations

import json
import os
import sys
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import structlog

# Import Aether systems
from assistant.audit import get_log
from assistant.memory import get_store
from assistant.learning import get_preferences as get_learning_preferences

log = structlog.get_logger()

# Configuration
DATA_DIR = Path(os.environ.get("AETHER_DATA_DIR", "planner/data"))
DASHBOARD_PORT = 8001  # Frontend expects port 8001

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Global variable for frontend dist path
_frontend_dist = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    log.info("dashboard_startup", port=DASHBOARD_PORT)
    print(f"Aether Dashboard API running on http://localhost:{DASHBOARD_PORT}")
    yield
    log.info("dashboard_shutdown")

# Initialize FastAPI app
app = FastAPI(
    title="Aether Dashboard API",
    description="REST API and WebSocket for Aether voice assistant dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware (for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the React frontend
# The frontend build is at: D:\hive\assistant\dashboard\frontend\dist
# When running from planner, cwd is D:\hive\assistant\planner
# So we need to go up two levels to hive, then to assistant/dashboard/frontend/dist
possible_locations = [
    Path.cwd().parent.parent / "assistant" / "dashboard" / "frontend" / "dist",
    Path.cwd().parent / "assistant" / "dashboard" / "frontend" / "dist",
    Path(__file__).parent.parent.parent.parent.parent.parent / "assistant" / "dashboard" / "frontend" / "dist",
]

print(f"Current working directory: {Path.cwd()}")
print(f"First location to try: {possible_locations[0]}")
print(f"First location exists: {possible_locations[0].exists()}")

for location in possible_locations:
    if location.exists():
        _frontend_dist = location
        print(f"Found frontend at: {_frontend_dist}")
        break

# Static files mount will be done after API routes to avoid conflicts
# This is handled after all API routes are defined

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        log.info("websocket_connected", connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        log.info("websocket_disconnected", connections=len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                log.error("websocket_send_failed", error=str(e))
                self.disconnect(connection)

manager = ConnectionManager()

# Pydantic models
class SystemStatus(BaseModel):
    planner_running: bool
    wake_word_running: bool
    ollama_running: bool
    hive_running: bool
    cpu_usage: float
    memory_usage: float
    disk_usage: float

class CommandHistoryItem(BaseModel):
    id: str
    timestamp: str
    command: str
    skill: str
    success: bool
    risk_level: str
    approval_required: bool
    approval_given: bool
    execution_time_ms: int

class UserPreferences(BaseModel):
    theme: str = "light"  # light, dark, auto
    ui_density: str = "comfortable"  # compact, comfortable, spacious
    notifications_enabled: bool = True
    sound_enabled: bool = True
    language: str = "en"
    sidebar_collapsed: bool = False
    conversation_timeout: float = 10.0  # seconds

class Configuration(BaseModel):
    wake_word_enabled: bool = True
    hotkey_enabled: bool = False
    hotkey_combination: str = "win+alt+a"
    ollama_url: str = "http://127.0.0.1:11434"
    llm_model: str = "qwen2.5:1.5b-instruct"
    risk_threshold: str = "medium"  # low, medium, high
    conversation_timeout: float = 10.0  # seconds to wait for follow-up

class RuleItem(BaseModel):
    id: str
    scope: str
    rule: str
    confidence: float
    source: str
    hard: bool
    created_at: str
    last_updated: str

# API Routes
# Note: Root route "/" is handled by static files mount at the end of this file

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/status")
async def get_system_status() -> SystemStatus:
    """Get current system status."""
    # Check if planner is running by trying to connect
    planner_running = False
    try:
        import socket
        with socket.create_connection(("127.0.0.1", 48100), timeout=1):
            planner_running = True
    except Exception:
        pass

    # Check Ollama
    ollama_running = False
    try:
        import socket
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
            ollama_running = True
    except Exception:
        pass

    # Check Hive
    hive_running = False
    try:
        import socket
        with socket.create_connection(("127.0.0.1", 8000), timeout=1):
            hive_running = True
    except Exception:
        pass

    # Get system resources
    cpu_usage = _get_cpu_usage()
    memory_usage = _get_memory_usage()
    disk_usage = _get_disk_usage()

    return SystemStatus(
        planner_running=planner_running,
        wake_word_running=planner_running,  # Assume same as planner for now
        ollama_running=ollama_running,
        hive_running=hive_running,
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
    )


def _get_cpu_usage() -> float:
    """Get CPU usage percentage."""
    try:
        import psutil
        return psutil.cpu_percent()
    except Exception:
        return 0.0


def _get_memory_usage() -> float:
    """Get memory usage percentage."""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except Exception:
        return 0.0


def _get_disk_usage() -> float:
    """Get disk usage percentage."""
    try:
        import psutil
        # Use the root of the current drive on Windows
        return psutil.disk_usage("C:\\").percent
    except Exception:
        return 0.0

@app.get("/api/commands")
async def get_command_history(limit: int = 50, offset: int = 0) -> list[CommandHistoryItem]:
    """Get command history from audit log."""
    try:
        audit_log = get_log()
        # Get recent audit entries using the correct method name
        entries = audit_log.recent(n=limit)
        
        commands = []
        for entry in entries:
            # Parse audit entry to extract command info
            if entry.get("event") == "action":
                data = entry.get("data", {})
                commands.append(CommandHistoryItem(
                    id=str(entry.get("seq", "")),
                    timestamp=datetime.fromtimestamp(entry.get("timestamp", 0) / 1000).isoformat(),
                    command=data.get("intent", data.get("transcript", "")),
                    skill=data.get("skill", ""),
                    success=data.get("outcome") == "ok",
                    risk_level=data.get("risk", "unknown"),
                    approval_required=data.get("approved") is not None,
                    approval_given=data.get("approved", False),
                    execution_time_ms=0,  # TODO: track execution time
                ))
        return commands
    except Exception as e:
        log.error("get_command_history_failed", error=str(e))
        return []


@app.get("/api/commands/{command_id}")
async def get_command_detail(command_id: str) -> dict[str, Any]:
    """Get specific command details."""
    try:
        audit_log = get_log()
        # Search for the entry by sequence number
        entries = audit_log.recent(n=1000)  # Get more entries to search
        for entry in entries:
            if str(entry.get("seq")) == command_id:
                return entry
        return {"error": "Command not found"}
    except Exception as e:
        log.error("get_command_detail_failed", error=str(e))
        return {"error": str(e)}


@app.get("/api/memory/stats")
async def get_memory_stats() -> dict[str, Any]:
    """Get memory statistics."""
    try:
        memory_store = get_store()
        # Get memory statistics using the MemoryStore API
        stats = {
            "total_memories": memory_store.count(),
            "total_conversations": memory_store.count("conversation"),
            "total_actions": memory_store.count("action"),
            "total_preferences": memory_store.count("preference"),
        }
        return stats
    except Exception as e:
        log.error("get_memory_stats_failed", error=str(e))
        return {"error": str(e)}


@app.get("/api/memories")
async def get_memories(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Get recent memories."""
    try:
        memory_store = get_store()
        all_memories = memory_store.export_all()
        # Apply pagination
        memories = all_memories[offset:offset + limit]
        return memories
    except Exception as e:
        log.error("get_memories_failed", error=str(e))
        return []


@app.get("/api/rules")
async def get_rules() -> list[RuleItem]:
    """Get all user rules (Tier 0 preferences)."""
    try:
        preferences = get_learning_preferences()
        all_prefs = preferences.get_all()
        
        rules = []
        for pref in all_prefs:
            if pref["source"] == "user":
                rules.append(RuleItem(
                    id=pref["id"],
                    scope=pref["scope"],
                    rule=pref["rule"],
                    confidence=pref["confidence"],
                    source=pref["source"],
                    hard=bool(pref["hard"]),
                    created_at=datetime.fromtimestamp(pref["created_at"] / 1000).isoformat(),
                    last_updated=datetime.fromtimestamp(pref["last_updated"] / 1000).isoformat(),
                ))
        return rules
    except Exception as e:
        log.error("get_rules_failed", error=str(e))
        return []


@app.post("/api/rules")
async def create_rule(rule: dict[str, Any]) -> RuleItem:
    """Create a new user rule."""
    try:
        preferences = get_learning_preferences()
        pid = preferences.add_rule(
            scope=rule.get("scope", "global"),
            rule=rule["rule"],
            hard=rule.get("hard", True),
        )
        # Return the created rule
        all_prefs = preferences.get_all()
        for pref in all_prefs:
            if pref["id"] == pid:
                return RuleItem(
                    id=pref["id"],
                    scope=pref["scope"],
                    rule=pref["rule"],
                    confidence=pref["confidence"],
                    source=pref["source"],
                    hard=bool(pref["hard"]),
                    created_at=datetime.fromtimestamp(pref["created_at"] / 1000).isoformat(),
                    last_updated=datetime.fromtimestamp(pref["last_updated"] / 1000).isoformat(),
                )
        return {"error": "Failed to create rule"}
    except Exception as e:
        log.error("create_rule_failed", error=str(e))
        return {"error": str(e)}


@app.delete("/api/rules/{rule_id}")
async def delete_rule(rule_id: str) -> dict[str, Any]:
    """Delete a user rule."""
    try:
        preferences = get_learning_preferences()
        success = preferences.forget(rule_id)
        return {"success": success}
    except Exception as e:
        log.error("delete_rule_failed", error=str(e))
        return {"error": str(e)}


@app.get("/api/preferences")
async def get_user_preferences() -> UserPreferences:
    """Get user preferences."""
    prefs_file = DATA_DIR / "preferences.json"
    if prefs_file.exists():
        with open(prefs_file) as f:
            return UserPreferences(**json.load(f))
    return UserPreferences()

@app.put("/api/preferences")
async def update_user_preferences(preferences: UserPreferences) -> UserPreferences:
    """Update user preferences."""
    prefs_file = DATA_DIR / "preferences.json"
    with open(prefs_file, "w") as f:
        json.dump(preferences.model_dump(), f, indent=2)
    return preferences

@app.get("/api/config")
async def get_configuration() -> Configuration:
    """Get system configuration."""
    # TODO: Integrate with actual configuration
    return Configuration()

@app.put("/api/config")
async def update_configuration(config: Configuration) -> Configuration:
    """Update system configuration."""
    # TODO: Integrate with actual configuration updates
    return config

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now, will handle real commands later
            await manager.broadcast({"type": "echo", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mount static files for the React frontend AFTER all API routes
# This ensures API routes take precedence over static files
# StaticFiles with html=True will handle SPA routing automatically
print(f"About to mount static files. _frontend_dist = {_frontend_dist}")
if _frontend_dist:
    print(f"Mounting static files from: {_frontend_dist}")
    print(f"Directory exists: {_frontend_dist.exists()}")
    print(f"index.html exists: {(_frontend_dist / 'index.html').exists()}")
    print(f"assets directory exists: {(_frontend_dist / 'assets').exists()}")
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
    print("Static files mounted successfully")
else:
    print("Warning: Frontend build not found")
    print("Tried locations:")
    for loc in possible_locations:
        print(f"  - {loc}")
    print("Run: cd assistant/dashboard/frontend && npm run build")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=DASHBOARD_PORT)
