"""Unit tests for CLI components and slash command handling."""

import pytest
from unittest.mock import AsyncMock, patch
from prompt_toolkit.document import Document
from ai_cli.cli.app import handle_slash_command
from ai_cli.cli.renderer import render_banner
from ai_cli.cli.suggestions import SlashCommandCompleter
from ai_cli.main import build_parser


def test_cli_parser_arguments():
    """Verify argument parser configurations."""
    parser = build_parser()

    # Default interactive
    args0 = parser.parse_args([])
    assert args0.query is None
    assert args0.eval is False
    assert args0.index is None
    assert args0.update is False

    # Query one-shot
    args1 = parser.parse_args(["write a flask app"])
    assert args1.query == "write a flask app"

    # Flags
    args2 = parser.parse_args(["--eval"])
    assert args2.eval is True

    args3 = parser.parse_args(["--index", "src"])
    assert args3.index == "src"

    args4 = parser.parse_args(["--update"])
    assert args4.update is True


def test_slash_command_completer():
    """Verify autocompletion suggestions for slash commands."""
    completer = SlashCommandCompleter()
    doc = Document("/up", 3)
    completions = list(completer.get_completions(doc, None))
    
    assert len(completions) == 1
    assert completions[0].text == "/update"


@pytest.mark.asyncio
async def test_handle_slash_commands():
    """Verify slash command execution."""
    # /help should return True (continue loop)
    cont_help = await handle_slash_command("/help")
    assert cont_help is True

    # /exit should return False (exit loop)
    cont_exit = await handle_slash_command("/exit")
    assert cont_exit is False

    # /update should return True
    with patch("ai_cli.cli.app.update_anton", new_callable=AsyncMock) as mock_up:
        mock_up.return_value = True
        cont_update = await handle_slash_command("/update")
        assert cont_update is True
        mock_up.assert_called_once()
