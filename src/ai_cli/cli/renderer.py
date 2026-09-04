"""Rich terminal UI renderer with all-white Gemini logo and model selector for Anton."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from rich.align import Align
from rich.box import DOUBLE_EDGE, HEAVY, ROUNDED, SIMPLE
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from ai_cli.config.settings import get_settings
from ai_cli.memory.sessions import SessionInfo
from ai_cli.providers.groq import SUPPORTED_GROQ_MODELS

console = Console()


def render_banner(sessions: Optional[List[SessionInfo]] = None) -> None:
    """Render the circuit-style pixel logo (ANTON + AI coding agent), tips, and recent sessions."""
    settings = get_settings()

    # 1. Official ASCII Art Logo (> ANTON + AI coding agent)
    logo_ascii = """
     █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ██╗
    ██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗  ██║
    ███████║██╔██╗ ██║   ██║   ██║   ██║██╔██╗ ██║
    ██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╗██║
    ██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚████║
    ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝

    AI coding agent
"""

    console.print(f"[bold white]{logo_ascii}[/bold white]")

    # 2. Clean Tips for getting started
    tips_text = Text()
    tips_text.append("Tips for getting started:\n", style="bold white")
    tips_text.append("1. Ask questions, edit files, navigate directories, or run commands.\n", style="dim")
    tips_text.append("2. Anton searches the web and inspects code autonomously when needed.\n", style="dim")
    tips_text.append("3. Type ", style="dim")
    tips_text.append("/", style="bold white")
    tips_text.append(" for slash commands (", style="dim")
    tips_text.append("/help", style="bold white")
    tips_text.append(", ", style="dim")
    tips_text.append("/model", style="bold white")
    tips_text.append(", ", style="dim")
    tips_text.append("/sessions", style="bold white")
    tips_text.append(", ", style="dim")
    tips_text.append("/delete", style="bold white")
    tips_text.append(").\n", style="dim")

    console.print(tips_text)

    # 3. Previous Sessions List (if any exist)
    if sessions:
        sessions_header = Text("Previous Conversations:\n", style="bold white")
        console.print(sessions_header)
        for i, s in enumerate(sessions[:5], 1):
            s_line = Text()
            s_line.append(f"  [{i}] ", style="bold cyan")
            s_line.append(f"{s.title} ", style="bold white")
            s_line.append(f"({s.message_count} msgs • {s.updated_at or s.created_at})", style="dim")
            console.print(s_line)
        
        new_line = Text()
        new_line.append("  [N] ", style="bold green")
        new_line.append("✦ Start a New Conversation ", style="bold green")
        new_line.append("(Default - press Enter or type your prompt)\n", style="dim")
        console.print(new_line)


def render_collapsed_banner(current_model: str, session_title: Optional[str] = None) -> None:
    """Render sleek, collapsed single-line banner header for ongoing conversation."""
    title_part = f" • \"{session_title}\"" if session_title and session_title != "New Conversation" else ""
    console.print(f"[bold white]✦ ANTON[/bold white] [dim]AI coding agent[/dim] [dim]({current_model}){title_part}[/dim]\n")


def render_models_table(current_model: str, models: Optional[List[Dict[str, str]]] = None) -> None:
    """Render a clean table of available Groq models with switch commands."""
    model_list = models or SUPPORTED_GROQ_MODELS
    table = Table(title="✦ Supported Groq Models", box=ROUNDED)
    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Model ID", style="bold white")
    table.add_column("Name", style="dim")
    table.add_column("Speed", justify="center", style="green")
    table.add_column("Context", justify="center", style="dim")
    table.add_column("Status", justify="center")

    for i, m in enumerate(model_list, 1):
        m_id = m["id"]
        is_active = m_id == current_model
        status = "[bold green]ACTIVE[/bold green]" if is_active else f"[dim]{m.get('type', '')}[/dim]"
        table.add_row(
            f"[{i}]",
            f"[bold cyan]{m_id}[/bold cyan]" if is_active else m_id,
            m.get("name", m_id),
            m.get("speed", "-"),
            m.get("context", "131k"),
            status,
        )

    console.print(table)
    console.print("[dim]Type [/dim][bold white]/model <number or ID>[/bold white][dim] to switch models (e.g. [/dim][bold cyan]/model 2[/bold cyan][dim] or [/dim][bold cyan]/model openai/gpt-oss-120b[/bold cyan][dim]).[/dim]\n")


import re

def extract_thoughts_and_response(content: str) -> Tuple[Optional[str], str]:
    """
    Extract <think>...</think> or reasoning tags from model content.
    Handles both closed and unclosed <think> blocks gracefully.
    Returns (thoughts, final_response).
    """
    if not content:
        return (None, "")

    # 1. Standard closed <think>...</think> pattern
    think_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)
    match = think_pattern.search(content)
    if match:
        thoughts = match.group(1).strip()
        response = think_pattern.sub("", content).strip()
        return (thoughts if thoughts else None, response)

    # 2. Unclosed <think>... pattern (if model hits max output token limit mid-thought)
    unclosed_pattern = re.compile(r"<think>(.*)", re.DOTALL | re.IGNORECASE)
    unclosed_match = unclosed_pattern.search(content)
    if unclosed_match:
        thoughts = unclosed_match.group(1).strip()
        # Anything before <think> was the response
        response = content[:unclosed_match.start()].strip()
        return (thoughts if thoughts else None, response)

    return (None, content.strip())


def render_user_input(content: str) -> None:
    """Render user query inside a sleek rounded box."""
    console.print()
    console.print(
        Panel(
            Text(content, style="bold white"),
            title="[bold cyan]✦ User[/bold cyan]",
            title_align="left",
            border_style="dim cyan",
            box=ROUNDED,
            padding=(0, 1),
        )
    )


def render_thinking(thoughts: str) -> None:
    """Render model reasoning/thinking process in a specialized yellow/dim box with loop protection."""
    if not thoughts or not thoughts.strip():
        return

    # Deduplicate repetitive thought loops
    raw_lines = thoughts.strip().split("\n")
    cleaned_lines = []
    prev_line = ""
    consecutive_repeats = 0
    truncated_loop = False

    for line in raw_lines:
        trimmed = line.strip()
        if trimmed == prev_line and trimmed:
            consecutive_repeats += 1
            if consecutive_repeats <= 2:
                cleaned_lines.append(line)
            elif not truncated_loop:
                cleaned_lines.append("... [repetitive reasoning loop truncated]")
                truncated_loop = True
        else:
            consecutive_repeats = 0
            prev_line = trimmed
            truncated_loop = False
            cleaned_lines.append(line)

    display_thoughts = "\n".join(cleaned_lines)

    console.print()
    console.print(
        Panel(
            Text(display_thoughts, style="italic #e2e8f0"),
            title="[bold yellow]✦ Thinking & Reasoning[/bold yellow]",
            title_align="left",
            border_style="yellow",
            box=ROUNDED,
            padding=(0, 1),
        )
    )


def render_tool_call(name: str, args: Optional[Dict[str, Any]] = None, result: Optional[str] = None) -> None:
    """Render visual notification when a tool is invoked or returns a result."""
    body = Text()
    body.append("⚙ Action: ", style="bold cyan")
    body.append(f"{name}\n", style="bold white")
    if args:
        summary = ", ".join(f"{k}={repr(v)[:80]}" for k, v in args.items())
        body.append("Arguments: ", style="dim")
        body.append(f"{summary}\n", style="dim")
    if result:
        preview = result[:250] + ("..." if len(result) > 250 else "")
        body.append("Result: ", style="dim green")
        body.append(f"{preview}", style="dim")

    console.print(
        Panel(
            body,
            title="[bold cyan]⚙ Tool Execution[/bold cyan]",
            title_align="left",
            border_style="dim cyan",
            box=ROUNDED,
            padding=(0, 1),
        )
    )


def render_response_box(content: str, model_name: str = "Anton") -> None:
    """Render the AI response in a clean, prominent rounded white box."""
    if not content.strip():
        return
    console.print()
    console.print(
        Panel(
            Markdown(content.strip()),
            title=f"[bold white]✦ Anton[/bold white] [dim]({model_name})[/dim]",
            title_align="left",
            border_style="bold white",
            box=ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()


def render_markdown(content: str) -> None:
    """Render markdown response to terminal inside response box."""
    render_response_box(content)


def render_diff(diff_content: str, title: str = "Proposed File Changes") -> None:
    """Render a colored unified diff block."""
    if not diff_content.strip():
        return
    syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=f"[bold green]✦ {title}[/bold green]", border_style="green", box=ROUNDED))


def render_error(message: str) -> None:
    """Render an error message panel."""
    console.print(Panel(f"[bold red]✕ Error:[/bold red] {message}", border_style="red", box=ROUNDED))


def render_doctor_report(
    groq_ok: bool,
    tavily_ok: bool,
    chroma_ok: bool,
    file_count: int,
    total_chunks: int,
    current_model: str,
) -> None:
    """Render system diagnostics check in a table."""
    table = Table(title="✦ Anton Diagnostic Health Check", box=ROUNDED)
    table.add_column("Component", style="bold cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    table.add_row(
        "Groq LLM Engine",
        "[bold green]READY[/bold green]" if groq_ok else "[bold yellow]NOT CONFIGURED[/bold yellow]",
        f"Active Model: {current_model}" if groq_ok else "Set GROQ_API_KEY in .env",
    )
    table.add_row(
        "Tavily Search API",
        "[bold green]READY[/bold green]" if tavily_ok else "[bold yellow]NOT CONFIGURED[/bold yellow]",
        "Live web retrieval enabled" if tavily_ok else "Set TAVILY_API_KEY in .env for web search",
    )
    table.add_row(
        "ChromaDB Vector Store",
        "[bold green]ONLINE[/bold green]" if chroma_ok else "[bold red]ERROR[/bold red]",
        f"Indexed {file_count} files ({total_chunks} chunks in data/chroma)",
    )
    table.add_row(
        "Local Embeddings",
        "[bold green]ONLINE[/bold green]",
        "FastEmbed (BAAI/bge-small-en-v1.5) 100% offline",
    )

    console.print(table)


def render_eval_summary(summary: Any) -> None:
    """Render multi-agent evaluation benchmark results in a rich table."""
    table = Table(title="✦ Multi-Agent Benchmark Results", box=ROUNDED)
    table.add_column("Test ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Committee Verdicts", style="dim")

    for res in summary.results:
        status = "[bold green]PASS[/bold green]" if res.evaluation.overall_passed else "[bold red]FAIL[/bold red]"
        score = f"{res.evaluation.overall_score}/100"
        short_summary = " | ".join(f"{v.agent_name}: {v.score}" for v in res.evaluation.verdicts)
        table.add_row(res.test_id, res.category, status, score, short_summary)

    console.print(table)
    console.print(
        f"[bold]Total Tests:[/bold] {summary.total_tests} | "
        f"[bold green]Passed:[/bold green] {summary.passed_tests} | "
        f"[bold red]Failed:[/bold red] {summary.failed_tests} | "
        f"[bold cyan]Pass Rate:[/bold cyan] {summary.pass_rate:.1f}% | "
        f"[bold yellow]Avg Score:[/bold yellow] {summary.average_score:.1f}/100"
    )
