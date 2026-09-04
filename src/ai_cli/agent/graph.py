"""LangGraph state graph definition and compilation for Anton agent."""

from typing import Literal, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from ai_cli.agent.nodes import (
    create_reasoning_node,
    input_guard_node,
    output_guard_node,
    tool_execution_node,
)
from ai_cli.agent.state import AgentState
from ai_cli.providers.factory import ProviderFactory


def route_after_input_guard(state: AgentState) -> Literal["reasoning", "output_guard"]:
    """Route to output_guard immediately if input guardrail flagged a violation."""
    if state.get("guardrail_flagged"):
        return "output_guard"
    return "reasoning"


def route_after_reasoning(state: AgentState) -> Literal["tools", "output_guard"]:
    """Route to tool execution if the model made tool calls, else proceed to output guard."""
    messages = state.get("messages", [])
    if not messages:
        return "output_guard"

    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return "output_guard"


def create_agent_graph(
    model: Optional[BaseChatModel] = None,
    checkpointer: Optional[MemorySaver] = None,
):
    """
    Build and compile the Anton LangGraph Agent workflow.
    """
    if model is None:
        provider = ProviderFactory.get_provider("groq")
        model = provider.get_chat_model()

    workflow = StateGraph(AgentState)

    # 1. Register Nodes
    workflow.add_node("input_guard", input_guard_node)
    workflow.add_node("reasoning", create_reasoning_node(model))
    workflow.add_node("tools", tool_execution_node)
    workflow.add_node("output_guard", output_guard_node)

    # 2. Configure Edges and Routing
    workflow.set_entry_point("input_guard")

    workflow.add_conditional_edges(
        "input_guard",
        route_after_input_guard,
        {
            "reasoning": "reasoning",
            "output_guard": "output_guard",
        },
    )

    workflow.add_conditional_edges(
        "reasoning",
        route_after_reasoning,
        {
            "tools": "tools",
            "output_guard": "output_guard",
        },
    )

    # From tools, loop back to reasoning for subsequent actions / final answer
    workflow.add_edge("tools", "reasoning")

    # From output guard, terminate the turn
    workflow.add_edge("output_guard", END)

    memory = checkpointer or MemorySaver()
    return workflow.compile(checkpointer=memory)
