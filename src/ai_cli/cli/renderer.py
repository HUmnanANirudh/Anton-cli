"""Rich terminal UI renderer with Gemini CLI aesthetic and session manager for Anton."""

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

console = Console()


def render_banner(sessions: Optional[List[SessionInfo]] = None) -> None:
    """Render the Gemini CLI pixel-art logo, getting started tips, and recent sessions."""
    settings = get_settings()

    # 1. Pixel Art Logo (> ANTON) with gradient colors
    logo_segments = [
        ("  █  ", "bold #38bdf8"),
        ("  ▄█████▄   ", "#38bdf8"),
        ("███▄   ██  ", "#60a5fa"),
        ("█████████   ", "#818cf8"),
        ("▄██████▄   ", "#a855f7"),
        ("███▄   ██ \n", "#ec4899"),

        (" ▄██ ", "bold #38bdf8"),
        (" ███   ███  ", "#38bdf8"),
        ("████▄  ██     ", "#60a5fa"),
        ("███     ", "#818cf8"),
        ("███    ███  ", "#a855f7"),
        ("████▄  ██ \n", "#ec4899"),

        ("▀███ ", "bold #38bdf8"),
        (" █████████  ", "#38bdf8"),
        ("██ ███ ██     ", "#60a5fa"),
        ("███     ", "#818cf8"),
        ("███    ███  ", "#a855f7"),
        ("██ ███ ██ \n", "#ec4899"),

        (" ▀██ ", "bold #38bdf8"),
        (" ███   ███  ", "#38bdf8"),
        ("██  ▀████     ", "#60a5fa"),
        ("███     ", "#818cf8"),
        ("███    ███  ", "#a855f7"),
        ("██  ▀████ \n", "#ec4899"),

        ("  ▀  ", "bold #38bdf8"),
        (" ███   ███  ", "#38bdf8"),
        ("██    ███     ", "#60a5fa"),
        ("███      ", "#818cf8"),
        ("▀██████▀   ", "#a855f7"),
        ("██    ███ \n", "#ec4899"),
    ]

    logo_text = Text()
    for text, style in logo_segments:
        logo_text.append(text, style=style)

    console.print()
    console.print(logo_text)

    # 2. Tips for getting started (matching Gemini CLI format)
    tips_text = Text()
    tips_text.append("Tips for getting started:\n", style="bold white")
    tips_text.append("1. Ask questions, edit files, or run commands.\n", style="dim")
    tips_text.append("2. Be specific for the best results.\n", style="dim")
    tips_text.append("3. Type ", style="dim")
    tips_text.append("/", style="bold cyan")
    tips_text.append(" for slash commands (", style="dim")
    tips_text.append("/help", style="bold cyan")
    tips_text.append(", ", style="dim")
    tips_text.append("/index", style="bold cyan")
    tips_text.append(", ", style="dim")
    tips_text.append("/search", style="bold cyan")
    tips_text.append(", ", style="dim")
    tips_text.append("/eval", style="bold cyan")
    tips_text.append(").\n", style="dim")

    console.print(tips_text)

    # 3. Previous Sessions List (if any exist)
    if sessions:
        sessions_header = Text("Previous Conversations:\n", style="bold #a855f7")
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
        console.print("[dim]Type a session number to resume (e.g. 1), or type your prompt directly:[/dim]\n")


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
