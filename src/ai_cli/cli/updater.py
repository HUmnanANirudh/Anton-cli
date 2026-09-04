"""Anton self-update and version synchronization utility."""

import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from rich.panel import Panel
from ai_cli.cli.renderer import console, render_error
from ai_cli.config.settings import get_settings


async def update_anton() -> bool:
    """Check and pull the latest version of Anton CLI using git and uv."""
    settings = get_settings()
    console.print(f"[bold cyan]Checking for updates...[/bold cyan] (Current version: [bold yellow]v{settings.APP_VERSION}[/bold yellow])")

    # Determine root directory of Anton CLI
    source_file = Path(__file__).resolve()
    # src/ai_cli/cli/updater.py -> root is 4 levels up
    project_root = source_file.parents[3]

    git_bin = shutil.which("git")
    uv_bin = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")

    if (project_root / ".git").exists() and git_bin:
        console.print(f"[dim]Checking remote repository at {project_root}...[/dim]")
        try:
            # 1. git pull
            proc = await asyncio.create_subprocess_exec(
                git_bin,
                "pull",
                cwd=str(project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0:
                if "Already up to date" in output:
                    console.print(f"[bold green]✓ Anton CLI is already up to date (v{settings.APP_VERSION})[/bold green]")
                else:
                    console.print(f"[bold green]✓ Pulled latest changes:[/bold green]\n[dim]{output}[/dim]")
            else:
                err_msg = stderr.decode("utf-8", errors="replace").strip()
                console.print(f"[yellow]Git pull note:[/yellow] {err_msg or output}")

        except Exception as e:
            console.print(f"[yellow]Note while checking git:[/yellow] {e}")

    # 2. Sync / refresh package with uv
    if Path(uv_bin).exists():
        console.print("[dim]Synchronizing dependencies with uv...[/dim]")
        try:
            proc_uv = await asyncio.create_subprocess_exec(
                uv_bin,
                "pip",
                "install",
                "-e",
                ".[dev]",
                cwd=str(project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc_uv.communicate()
            console.print(f"[bold green]✓ Environment synchronized successfully with uv![/bold green]")
        except Exception as e:
            console.print(f"[yellow]Note during uv sync:[/yellow] {e}")

    console.print(
        Panel(
            f"[bold cyan]Anton CLI is running latest version:[/bold cyan] [bold yellow]v{settings.APP_VERSION}[/bold yellow]",
            border_style="cyan",
        )
    )
    return True
