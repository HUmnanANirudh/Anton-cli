"""Unit tests for SessionManager and conversation history persistence."""

import tempfile
from pathlib import Path
from langchain_core.messages import AIMessage, HumanMessage
from ai_cli.memory.sessions import SessionManager


def test_session_lifecycle():
    """Verify session creation, saving, loading, listing, and deletion."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = SessionManager(sessions_dir=tmp_dir)

        s_id = mgr.create_session_id()
        messages = [
            HumanMessage(content="Explain LangGraph agent loops"),
            AIMessage(content="LangGraph uses stateful cyclic graphs..."),
        ]

        # 1. Save session
        mgr.save_session(
            session_id=s_id,
            messages=messages,
            workspace_path="/test/workspace",
        )

        # 2. List sessions
        sessions = mgr.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_id == s_id
        assert "Explain LangGraph" in sessions[0].title
        assert sessions[0].message_count == 2

        # 3. Load session
        loaded = mgr.load_session(s_id)
        assert loaded is not None
        assert loaded["session_id"] == s_id
        assert len(loaded["messages"]) == 2
        assert isinstance(loaded["messages"][0], HumanMessage)
        assert loaded["messages"][0].content == "Explain LangGraph agent loops"

        # 4. Delete session
        deleted = mgr.delete_session(s_id)
        assert deleted is True
        assert len(mgr.list_sessions()) == 0
