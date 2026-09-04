"""Slash command suggestions and autocompletion for interactive REPL."""

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

SLASH_COMMANDS = {
    "/help": "Show available slash commands and usage guide",
    "/index": "Index current workspace codebase into ChromaDB vector store",
    "/search": "Directly search the web via Tavily / Google Search (e.g. /search query)",
    "/vsearch": "Directly query local ChromaDB vector database (e.g. /vsearch symbol)",
    "/eval": "Run the multi-agent evaluation benchmark suite",
    "/update": "Check and update Anton CLI to the latest version",
    "/clear": "Clear the terminal screen",
    "/exit": "Exit Anton CLI",
    "/quit": "Exit Anton CLI",
}


class SlashCommandCompleter(Completer):
    """Autocompleter for slash commands."""

    def get_completions(self, document: Document, complete_event):
        text_before_cursor = document.text_before_cursor
        if text_before_cursor.startswith("/"):
            word = text_before_cursor.split()[0]
            for cmd, desc in SLASH_COMMANDS.items():
                if cmd.startswith(word):
                    yield Completion(
                        cmd,
                        start_position=-len(word),
                        display=cmd,
                        display_meta=desc,
                    )
