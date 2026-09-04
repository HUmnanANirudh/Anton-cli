"""Rich terminal UI renderer with all-white Gemini logo and model selector for Anton."""

from pathlib import Path
from typing import Any, Dict, List, Optional
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
    """Render the all-white Gemini-style pixel-art logo (> ANTON), tips, and recent sessions."""
    settings = get_settings()

    # 1. Pixel Art Logo (> ANTON) in pure clean white
    logo_ascii = """
  █    ▄█████▄   ███▄   ██  █████████   ▄██████▄   ███▄   ██ 
 ▄██  ███   ███  ████▄  ██     ███     ███    ███  ████▄  ██ 
▀███  █████████  ██ ███ ██     ███     ███    ███  ██ ███ ██ 
 ▀██  ███   ███  ██  ▀████     ███     ███    ███  ██  ▀████ 
  ▀   ███   ███  ██    ███     ███      ▀██████▀   ██    ███ 
"""

    console.print(f"[bold white]{logo_ascii}[/bold white]")

    # 2. Tips for getting started (matching Gemini CLI format)
    tips_text = Text()
    tips_text.append("Tips for getting started:\n", style="bold white")
    tips_text.append("1. Ask questions, edit files, or run commands.\n", style="dim")
    tips_text.append("2. Be specific for the best results.\n", style="dim")
    tips_text.append("3. Type ", style="dim")
    tips_text.append("/", style="bold white")
    tips_text.append(" for slash commands (", style="dim")
    tips_text.append("/help", style="bold white")
    tips_text.append(", ", style="dim")
    tips_text.append("/model", style="bold white")
    tips_text.append(", ", style="dim")
    tips_text.append("/index", style="bold white")
    tips_text.append(", ", style="dim")
    tips_text.append("/search", style="bold white")
    tips_text.append(", ", style="dim")
    tips_text.append("/eval", style="bold white")
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


def render_markdown(content: str) -> None:
    """Render markdown response to terminal."""
    console.print()
    console.print(Markdown(content))
    console.print()


def render_tool_call(name: str, args: Dict[str, Any]) -> None:
    """Render visual notification when a tool is invoked."""
    summary = ", ".join(f"{k}={repr(v)[:40]}" for k, v in args.items())
    console.print(f"[dim]⚙ [bold white]{name}[/bold white] [dim]({summary})[/dim][/dim]")


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
