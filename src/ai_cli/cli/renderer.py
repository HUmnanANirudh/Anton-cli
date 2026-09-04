"""Rich terminal UI renderer with Gemini CLI aesthetic for Anton."""

from pathlib import Path
from typing import Any, Dict, Optional
from rich.align import Align
from rich.box import DOUBLE_EDGE, HEAVY, ROUNDED, SIMPLE
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from ai_cli.config.settings import get_settings

console = Console()


def render_banner() -> None:
    """Render a modern Gemini-inspired header banner."""
    settings = get_settings()

    # Title with stylized gradient-like styling
    title_text = Text()
    title_text.append("✦ ", style="bold bright_cyan")
    title_text.append("ANTON", style="bold bright_white")
    title_text.append(f" v{settings.APP_VERSION}", style="bold cyan")
    title_text.append("  •  ", style="dim")
    title_text.append("Autonomous AI Coding Agent", style="dim italic")

    # Badges row
    status_row = Text()
    
    # Model status
    if settings.GROQ_API_KEY:
        status_row.append(" ⚡ Groq: ", style="dim")
        status_row.append(f"{settings.GROQ_MODEL} ", style="bold green")
    else:
        status_row.append(" ⚡ Groq: ", style="dim")
        status_row.append("No API Key ", style="bold yellow")

    # Search status
    if settings.TAVILY_API_KEY:
        status_row.append(" 🔍 Search: ", style="dim")
        status_row.append("Tavily Active ", style="bold bright_blue")
    else:
        status_row.append(" 🔍 Search: ", style="dim")
        status_row.append("Offline ", style="dim")

    # Vector store status
    status_row.append(" 💾 ChromaDB: ", style="dim")
    status_row.append(f"{settings.CHROMA_PERSIST_DIR}", style="bold magenta")

    # Shortcuts row
    help_row = Text("\nType ", style="dim")
    help_row.append("/", style="bold bright_cyan")
    help_row.append(" for slash commands (", style="dim")
    help_row.append("/help", style="bold cyan")
    help_row.append(", ", style="dim")
    help_row.append("/index", style="bold cyan")
    help_row.append(", ", style="dim")
    help_row.append("/search", style="bold cyan")
    help_row.append(", ", style="dim")
    help_row.append("/eval", style="bold cyan")
    help_row.append(") • Press ", style="dim")
    help_row.append("Tab", style="bold white")
    help_row.append(" to autocomplete • ", style="dim")
    help_row.append("Ctrl+C", style="bold white")
    help_row.append(" to exit", style="dim")

    content = Text()
    content.append(status_row)
    content.append(help_row)

    panel = Panel(
        content,
        title=title_text,
        title_align="left",
        border_style="bright_blue",
        box=ROUNDED,
        padding=(0, 1),
    )
    console.print(panel)


def render_markdown(content: str) -> None:
    """Render markdown response to terminal."""
    console.print()
    console.print(Markdown(content))
    console.print()


def render_tool_call(name: str, args: Dict[str, Any]) -> None:
    """Render visual notification when a tool is invoked."""
    summary = ", ".join(f"{k}={repr(v)[:40]}" for k, v in args.items())
    console.print(f"[dim]⚙ [bold bright_cyan]{name}[/bold bright_cyan] [dim]({summary})[/dim][/dim]")


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
) -> None:
    """Render system diagnostics check in a table."""
    table = Table(title="✦ Anton Diagnostic Health Check", box=ROUNDED)
    table.add_column("Component", style="bold cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    table.add_row(
        "Groq LLM Engine",
        "[bold green]READY[/bold green]" if groq_ok else "[bold yellow]NOT CONFIGURED[/bold yellow]",
        "Set GROQ_API_KEY in .env" if not groq_ok else "llama-3.3-70b-versatile active",
    )
    table.add_row(
        "Tavily Search API",
        "[bold green]READY[/bold green]" if tavily_ok else "[bold yellow]NOT CONFIGURED[/bold yellow]",
        "Set TAVILY_API_KEY in .env for web search" if not tavily_ok else "Live web retrieval enabled",
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
