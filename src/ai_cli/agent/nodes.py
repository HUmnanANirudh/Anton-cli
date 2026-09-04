"""LangGraph nodes and tool bindings for Anton agent workflow."""

import json
from typing import Any, Dict, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from ai_cli.agent.prompts import ANTON_SYSTEM_PROMPT
from ai_cli.agent.state import AgentState
from ai_cli.guardrails import evaluate_input, evaluate_output
from ai_cli.memory.chroma import ChromaMemory
from ai_cli.memory.embeddings import get_embeddings
from ai_cli.memory.retriever import CodeRetriever
from ai_cli.tools.filesystem import (
    build_tree,
    grep_codebase,
    patch_file,
    read_file,
    write_file,
)
from ai_cli.tools.shell import execute_shell_command
from ai_cli.tools.web import fetch_page_content, search_web


# ---------------------------------------------------------------------------
# Structured LangChain Tools
# ---------------------------------------------------------------------------

@tool
def read_file_tool(file_path: str, start_line: int = 1, end_line: int = 1000) -> str:
    """Read contents of a file with line numbers. Use to inspect code before modifying."""
    res = read_file(file_path, start_line=start_line, end_line=end_line)
    if res.error:
        return f"Error: {res.error}"
    return f"File: {res.file_path} (Lines {res.start_line}-{res.end_line} of {res.total_lines}):\n{res.content}"


@tool
def write_file_tool(file_path: str, content: str, overwrite: bool = True) -> str:
    """Create a new file or overwrite an existing file with complete content."""
    res = write_file(file_path, content, overwrite=overwrite)
    if res.error:
        return f"Error: {res.error}"
    status = "Created" if res.created else "Overwritten"
    return f"{status} {res.file_path} ({res.bytes_written} bytes)."


@tool
def patch_file_tool(file_path: str, target_content: str, replacement_content: str) -> str:
    """Replace a specific exact block of text in a file with replacement content."""
    res = patch_file(file_path, target_content, replacement_content)
    if not res.success:
        return f"Patch failed: {res.error}"
    return f"Successfully patched {res.file_path}.\nDiff:\n{res.diff}"


@tool
def build_tree_tool(root_dir: str = ".", max_depth: int = 3) -> str:
    """Show the visual folder structure and file tree of the project workspace."""
    return build_tree(root_dir=root_dir, max_depth=max_depth)


@tool
def grep_codebase_tool(query: str, is_regex: bool = False, case_sensitive: bool = False) -> str:
    """Search for a string or regex pattern across files in the codebase."""
    res = grep_codebase(query, is_regex=is_regex, case_sensitive=case_sensitive)
    if res.error:
        return f"Error: {res.error}"
    if res.total_matches == 0:
        return f"No matches found for '{query}'."
    lines = [f"{m.file_path}:{m.line_number} -> {m.line_content}" for m in res.matches]
    return f"Found {res.total_matches} matches:\n" + "\n".join(lines)


@tool
async def execute_shell_tool(command: str, timeout_seconds: int = 60) -> str:
    """Execute a shell/terminal command (e.g. pytest, git, python script)."""
    res = await execute_shell_command(command, timeout_seconds=timeout_seconds)
    if res.blocked:
        return f"Command BLOCKED by security policy: {res.error}"
    if res.timed_out:
        return f"Command TIMED OUT: {res.error}"
    out = []
    if res.stdout.strip():
        out.append(f"STDOUT:\n{res.stdout.strip()}")
    if res.stderr.strip():
        out.append(f"STDERR:\n{res.stderr.strip()}")
    out.append(f"(Exit Code: {res.exit_code})")
    return "\n\n".join(out)


@tool
async def search_web_tool(query: str, max_results: int = 5) -> str:
    """Search the live web using Tavily or Google Search for documentation and external answers."""
    res = await search_web(query, max_results=max_results)
    if res.error:
        return f"Search failed: {res.error}"
    if not res.results:
        return f"No search results found for '{query}'."
    lines = []
    for i, item in enumerate(res.results, 1):
        lines.append(f"{i}. **{item.title}** ({item.url})\n   {item.snippet}")
    return "\n\n".join(lines)


@tool
async def fetch_page_tool(url: str) -> str:
    """Fetch and extract text content from a web page URL."""
    res = await fetch_page_content(url)
    if res.error:
        return f"Error fetching {url}: {res.error}"
    return f"Title: {res.title}\nURL: {res.url}\n\nContent:\n{res.text_content[:4000]}"


@tool
def semantic_search_codebase_tool(query: str, n_results: int = 4) -> str:
    """Search the local ChromaDB vector store for relevant code context across the project."""
    retriever = CodeRetriever(chroma_memory=ChromaMemory(), embeddings=get_embeddings())
    return retriever.format_context_for_llm(query=query, n_results=n_results)


ALL_TOOLS = [
    read_file_tool,
    write_file_tool,
    patch_file_tool,
    build_tree_tool,
    grep_codebase_tool,
    execute_shell_tool,
    search_web_tool,
    fetch_page_tool,
    semantic_search_codebase_tool,
]

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}


# ---------------------------------------------------------------------------
# LangGraph Workflow Nodes
# ---------------------------------------------------------------------------

def input_guard_node(state: AgentState) -> Dict[str, Any]:
    """Inspect and sanitize latest user input before sending to reasoning model."""
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, HumanMessage):
        return {}

    content = str(last_msg.content)
    guard_res = evaluate_input(content)

    if not guard_res.is_safe:
        return {
            "guardrail_flagged": True,
            "guardrail_reasons": guard_res.flagged_reasons,
            "messages": [
                AIMessage(
                    content=(
                        "I detected a request that conflicts with security or safety policies "
                        f"({', '.join(guard_res.flagged_reasons)}). "
                        "How can I assist you with your software development task?"
                    )
                )
            ],
        }

    # If sanitized, update the message content
    if guard_res.sanitized_text != content:
        sanitized_msg = HumanMessage(content=guard_res.sanitized_text)
        return {
            "guardrail_flagged": False,
            "guardrail_reasons": guard_res.flagged_reasons,
            "messages": [sanitized_msg],
        }

    return {
        "guardrail_flagged": False,
        "guardrail_reasons": [],
    }


def create_reasoning_node(model: Any):
    """Factory creating reasoning node with bound tools and system prompt."""
    model_with_tools = model.bind_tools(ALL_TOOLS)

    async def reasoning_node(state: AgentState) -> Dict[str, Any]:
        # Build prompt sequence: System Message + Conversation History
        system_msg = SystemMessage(content=ANTON_SYSTEM_PROMPT)
        history = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
        full_messages = [system_msg] + history

        response = await model_with_tools.ainvoke(full_messages)
        return {"messages": [response]}

    return reasoning_node


async def tool_execution_node(state: AgentState) -> Dict[str, Any]:
    """Execute tool calls requested by the model and format results as ToolMessages."""
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {}

    tool_messages: List[ToolMessage] = []

    for call in last_message.tool_calls:
        name = call["name"]
        args = call.get("args", {})
        call_id = call["id"]

        tool_func = TOOLS_BY_NAME.get(name)
        if not tool_func:
            tool_messages.append(
                ToolMessage(
                    content=f"Error: Unknown tool '{name}'.",
                    tool_call_id=call_id,
                )
            )
            continue

        try:
            if hasattr(tool_func, "ainvoke"):
                result = await tool_func.ainvoke(args)
            else:
                result = tool_func.invoke(args)

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call_id,
                )
            )
        except Exception as e:
            tool_messages.append(
                ToolMessage(
                    content=f"Tool execution failed: {e}",
                    tool_call_id=call_id,
                )
            )

    return {"messages": tool_messages}


def output_guard_node(state: AgentState) -> Dict[str, Any]:
    """Filter the final model output against system prompt leakage and live secrets."""
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage) or not last_msg.content:
        return {}

    raw_text = str(last_msg.content)
    guard_res = evaluate_output(raw_text)

    if not guard_res.is_safe or guard_res.sanitized_output != raw_text:
        return {
            "messages": [AIMessage(content=guard_res.sanitized_output)]
        }

    return {}
