"""Rich terminal UI renderer for Anton CLI."""

from typing import Any, Dict
from rich.box import ROUNDED
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from ai_cli.config.settings import get_settings

console = Console()


def render_banner() -> None:
    """Render welcome banner and status."""
    settings = get_settings()
    banner_text = (
        f"[bold cyan]ANTON CLI[/bold cyan] [dim]v{settings.APP_VERSION}[/dim]\n"
        "[dim]High-Performance Autonomous Coding Assistant & Multi-Agent Evaluator[/dim]\n\n"
        "[dim]Type your prompt, or use slash commands like [bold]/help[/bold], [bold]/index[/bold], [bold]/eval[/bold], [bold]/clear[/bold][/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", box=ROUNDED))


def render_markdown(content: str) -> None:
    """Render markdown response to terminal."""
    console.print(Markdown(content))
    console.print()


def render_tool_call(name: str, args: Dict[str, Any]) -> None:
    """Render visual notification when a tool is invoked."""
    summary = ", ".join(f"{k}={repr(v)[:50]}" for k, v in args.items())
    console.print(f"[bold yellow]⚙ Executing Tool:[/bold yellow] [bold white]{name}[/bold white] [dim]({summary})[/dim]")


def render_diff(diff_content: str, title: str = "Proposed File Changes") -> None:
    """Render a colored unified diff block."""
    if not diff_content.strip():
        return
    syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=f"[bold green]{title}[/bold green]", border_style="green", box=ROUNDED))


def render_error(message: str) -> None:
    """Render an error message panel."""
    console.print(Panel(f"[bold red]Error:[/bold red] {message}", border_style="red", box=ROUNDED))


def render_eval_summary(summary: Any) -> None:
    """Render multi-agent evaluation benchmark results in a rich table."""
    table = Table(title="Multi-Agent Benchmark Results", box=ROUNDED)
    table.add_column("Test ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Verdicts Summary", style="dim")

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
