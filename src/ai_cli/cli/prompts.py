"""Interactive user confirmation and approval prompts."""

from rich.prompt import Confirm
from ai_cli.cli.renderer import console, render_diff


def confirm_shell_command(command: str) -> bool:
    """Prompt user to approve running a shell command."""
    console.print(f"\n[bold yellow]Anton wants to run the following shell command:[/bold yellow]")
    console.print(f"  [bold white on black] $ {command} [/bold white on black]\n")
    return Confirm.ask("[bold cyan]Allow execution?[/bold cyan]", default=False)


def confirm_file_modification(file_path: str, diff_or_info: str) -> bool:
    """Prompt user to approve writing or patching a file with diff preview."""
    console.print(f"\n[bold yellow]Anton wants to modify file:[/bold yellow] [bold cyan]{file_path}[/bold cyan]")
    if diff_or_info.strip():
        render_diff(diff_or_info, title=f"Diff Preview: {file_path}")
    return Confirm.ask("[bold cyan]Apply changes to file?[/bold cyan]", default=False)
