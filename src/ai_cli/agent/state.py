"""Agent state definition for LangGraph workflow."""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """LangGraph agent state across reasoning and execution loops."""

    # Chat history with automatic message reducer
    messages: Annotated[List[BaseMessage], add_messages]

    # Workspace directory context
    workspace_path: str

    # Pending human-in-the-loop approval details
    pending_tool_call: Optional[Dict[str, Any]]
    approval_granted: Optional[bool]

    # Guardrails and safety metadata
    input_sanitized: bool
    guardrail_flagged: bool
    guardrail_reasons: List[str]

    # Contextual knowledge from vector store or search
    retrieved_context: Optional[str]
