"""Slash command suggestions, autocomplete, and prompt-toolkit styles for Anton CLI."""

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style

SLASH_COMMANDS = {
    "/help": "Show all available slash commands & guide",
    "/pwd": "Print current working directory",
    "/cd": "Change working directory (/cd ~/Desktop or /cd ..)",
    "/whoami": "Show current user, OS & environment info",
    "/model": "Switch or list supported Groq models (/model <num/id>)",
    "/new": "Start a fresh new conversation session",
    "/end": "End current conversation session and start fresh",
    "/sessions": "List & resume previous conversations (/session <num>)",
    "/delete": "Delete sessions (/delete 1 2 3... or /delete all)",
    "/index": "Index current workspace into ChromaDB vector store",
    "/search": "Search the live web via Tavily API (/search query)",
    "/vsearch": "Query local ChromaDB code vector store (/vsearch query)",
    "/eval": "Run multi-agent evaluation benchmark on Groq",
    "/doctor": "Check API keys, ChromaDB status & environment",
    "/update": "Check & pull latest Anton CLI version with uv",
    "/clear": "Clear the terminal screen",
    "/exit": "Exit Anton CLI session",
    "/quit": "Exit Anton CLI session",
}

# Clean modern theme for Prompt Toolkit (all-white prompt, sleek completion menu)
CLI_STYLE = Style.from_dict(
    {
        # Prompt styling (clean white)
        "prompt.chevron": "bold #ffffff",
        # Dropdown Completion Menu
        "completion-menu": "bg:#1e1e2e #cdd6f4",
        "completion-menu.completion": "bg:#181825 #cdd6f4",
        "completion-menu.completion.current": "bold bg:#3b82f6 #ffffff",
        "completion-menu.meta": "bg:#11111b #9399b2",
        "completion-menu.meta.current": "bold bg:#2563eb #f1f5f9",
        "completion-menu.multi-column-meta": "bg:#11111b #9399b2",
        # Scrollbar
        "scrollbar.background": "bg:#181825",
        "scrollbar.button": "bg:#38bdf8",
    }
)


class SlashCommandCompleter(Completer):
    """Autocompleter that immediately suggests slash commands when typing '/'."""

    def get_completions(self, document: Document, complete_event):
        text_before_cursor = document.text_before_cursor

        # If user types "/" or a command starting with "/"
        if text_before_cursor.startswith("/"):
            word = text_before_cursor.split()[0] if text_before_cursor.split() else "/"
            for cmd, desc in SLASH_COMMANDS.items():
                if cmd.startswith(word.lower()):
                    yield Completion(
                        cmd,
                        start_position=-len(word),
                        display=cmd,
                        display_meta=desc,
                    )
