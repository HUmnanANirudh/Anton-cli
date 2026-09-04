"""Shell command execution tool."""

import asyncio
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from ai_cli.config.settings import get_settings
from ai_cli.tools.shell.safety import RiskLevel, assess_command_safety


class ShellExecutionResult(BaseModel):
    """Result of running a shell command."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    blocked: bool = False
    error: Optional[str] = None


async def execute_shell_command(
    command: str,
    cwd: Optional[str | Path] = None,
    timeout_seconds: Optional[int] = None,
    force_run: bool = False,
) -> ShellExecutionResult:
    """Execute a shell command with security checks and timeout handling."""
    settings = get_settings()
    working_dir = Path(cwd) if cwd else settings.BASE_DIR
    timeout = timeout_seconds or settings.SHELL_TIMEOUT_SECONDS

    # Safety check
    if not force_run:
        assessment = assess_command_safety(command)
        if assessment.risk_level == RiskLevel.BLOCKED:
            return ShellExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr="",
                blocked=True,
                error=assessment.reason,
            )

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(working_dir),
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=float(timeout),
            )
            return ShellExecutionResult(
                command=command,
                exit_code=process.returncode or 0,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
            )
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            return ShellExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr="",
                timed_out=True,
                error=f"Command timed out after {timeout} seconds",
            )

    except Exception as e:
        return ShellExecutionResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr="",
            error=f"Failed to execute command: {e}",
        )
