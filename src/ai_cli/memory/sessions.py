"""Persistent session management and conversation history."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    messages_from_dict,
    messages_to_dict,
)
from pydantic import BaseModel
from ai_cli.config.settings import get_settings


class SessionInfo(BaseModel):
    """Metadata for a saved chat session."""

    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    workspace_path: str


class SessionManager:
    """Manages saving, loading, listing, and resuming Anton chat sessions."""

    def __init__(self, sessions_dir: Optional[Path | str] = None):
        settings = get_settings()
        if sessions_dir:
            self.sessions_dir = Path(sessions_dir)
        else:
            self.sessions_dir = settings.BASE_DIR / "data" / "sessions"

        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def list_sessions(self, limit: int = 10) -> List[SessionInfo]:
        """List past sessions ordered by most recently updated."""
        sessions: List[SessionInfo] = []
        for file in self.sessions_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                sessions.append(
                    SessionInfo(
                        session_id=data.get("session_id", file.stem),
                        title=data.get("title", "Untitled Session"),
                        created_at=data.get("created_at", ""),
                        updated_at=data.get("updated_at", ""),
                        message_count=len(data.get("messages", [])),
                        workspace_path=data.get("workspace_path", ""),
                    )
                )
            except Exception:
                continue

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at or s.created_at, reverse=True)
        return sessions[:limit]

    def create_session_id(self) -> str:
        """Generate a human-readable timestamped session ID."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{ts}"

    def save_session(
        self,
        session_id: str,
        messages: List[BaseMessage],
        workspace_path: str,
        custom_title: Optional[str] = None,
    ) -> None:
        """Persist session messages and metadata to disk."""
        if not messages:
            return

        file_path = self._get_session_file(session_id)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Determine title from first human message if not provided
        title = custom_title
        if not title:
            first_human = next((m for m in messages if isinstance(m, HumanMessage)), None)
            if first_human:
                text = str(first_human.content).strip()
                title = (text[:45] + "...") if len(text) > 45 else text
            else:
                title = "New Conversation"

        created_at = now_str
        if file_path.exists():
            try:
                old_data = json.loads(file_path.read_text(encoding="utf-8"))
                created_at = old_data.get("created_at", now_str)
                if not custom_title:
                    title = old_data.get("title", title)
            except Exception:
                pass

        serialized_messages = messages_to_dict(messages)
        payload = {
            "session_id": session_id,
            "title": title,
            "created_at": created_at,
            "updated_at": now_str,
            "workspace_path": workspace_path,
            "messages": serialized_messages,
        }

        file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session messages and metadata by ID."""
        file_path = self._get_session_file(session_id)
        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            raw_messages = data.get("messages", [])
            messages = messages_from_dict(raw_messages)
            return {
                "session_id": data.get("session_id", session_id),
                "title": data.get("title", "Untitled Session"),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "workspace_path": data.get("workspace_path", ""),
                "messages": messages,
            }
        except Exception:
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session file."""
        file_path = self._get_session_file(session_id)
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception:
                return False
        return False
