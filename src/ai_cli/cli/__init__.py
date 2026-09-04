"""CLI package."""

from ai_cli.cli.app import handle_slash_command, run_interactive_session
from ai_cli.cli.prompts import confirm_file_modification, confirm_shell_command
from ai_cli.cli.renderer import (
    console,
    render_banner,
    render_diff,
    render_error,
    render_eval_summary,
    render_markdown,
    render_tool_call,
)
from ai_cli.cli.suggestions import SlashCommandCompleter

__all__ = [
    "run_interactive_session",
    "handle_slash_command",
    "console",
    "render_banner",
    "render_markdown",
    "render_tool_call",
    "render_diff",
    "render_error",
    "render_eval_summary",
    "confirm_shell_command",
    "confirm_file_modification",
    "SlashCommandCompleter",
]
