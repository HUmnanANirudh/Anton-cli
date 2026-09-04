"""Interactive REPL application loop with Gemini CLI aesthetic for Anton."""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Tuple
from langchain_core.messages import HumanMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle
from ai_cli.agent.graph import create_agent_graph
from ai_cli.cli.renderer import (
    console,
    render_banner,
    render_diff,
    render_doctor_report,
    render_error,
    render_eval_summary,
    render_markdown,
    render_tool_call,
)
from ai_cli.cli.suggestions import CLI_STYLE, SLASH_COMMANDS, SlashCommandCompleter
from ai_cli.cli.updater import update_anton
from ai_cli.config.settings import get_settings
from ai_cli.evaluations.benchmark import BenchmarkRunner
from ai_cli.memory.chroma import ChromaMemory
from ai_cli.memory.embeddings import get_embeddings
from ai_cli.memory.indexer import CodeIndexer
from ai_cli.memory.retriever import CodeRetriever
from ai_cli.tools.web.search import search_web


def get_short_path() -> str:
    """Get concise representation of current directory."""
    cwd = Path.cwd()
    home = Path.home()
    try:
        rel = cwd.relative_to(home)
        return f"~/{rel}"
    except ValueError:
        return str(cwd)


def get_prompt_tokens() -> List[Tuple[str, str]]:
    """Build formatted multi-part prompt for Prompt Toolkit."""
    dir_name = get_short_path()
    return [
        ("class:prompt.star", "✦ "),
        ("class:prompt.name", "Anton "),
        ("class:prompt.dir", f"[{dir_name}] "),
        ("class:prompt.arrow", "❯ "),
    ]


def get_bottom_toolbar() -> FormattedText:
    """Build bottom toolbar displaying status and shortcuts."""
    settings = get_settings()
    model_name = settings.GROQ_MODEL.split("-")[0] + "-70b" if "70b" in settings.GROQ_MODEL else settings.GROQ_MODEL
    
    return FormattedText([
        ("class:bottom-toolbar.badge", " ✦ Anton "),
        ("class:bottom-toolbar.text", " | Model: "),
        ("class:bottom-toolbar.model", f"{model_name} "),
        ("class:bottom-toolbar.text", "| Type "),
        ("class:bottom-toolbar.key", " / "),
        ("class:bottom-toolbar.text", "for commands | "),
        ("class:bottom-toolbar.key", " Tab "),
        ("class:bottom-toolbar.text", "complete | "),
        ("class:bottom-toolbar.key", " Ctrl+C "),
        ("class:bottom-toolbar.text", "exit "),
    ])


async def handle_slash_command(command_str: str) -> bool:
    """
    Handle slash commands in REPL.
    Returns True if execution should continue, False if REPL should exit.
    """
    parts = command_str.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ["/exit", "/quit"]:
        console.print("[cyan]✦ Goodbye![/cyan]")
        return False

    if cmd == "/clear":
        os.system("clear" if os.name != "nt" else "cls")
        render_banner()
        return True

    if cmd == "/help":
        console.print("\n[bold cyan]✦ Available Slash Commands:[/bold cyan]\n")
        from rich.table import Table
        table = Table(box=None, show_header=False)
        table.add_column("Command", style="bold bright_cyan", width=14)
        table.add_column("Description", style="dim")
        for c, desc in SLASH_COMMANDS.items():
            table.add_row(c, desc)
        console.print(table)
        console.print()
        return True

    if cmd == "/doctor":
        settings = get_settings()
        memory = ChromaMemory()
        col = memory.get_or_create_collection()
        hashes = memory.get_file_hashes()
        render_doctor_report(
            groq_ok=bool(settings.GROQ_API_KEY),
            tavily_ok=bool(settings.TAVILY_API_KEY),
            chroma_ok=True,
            file_count=len(hashes),
            total_chunks=col.count(),
        )
        return True

    if cmd == "/index":
        target = arg.strip() or "."
        console.print(f"[yellow]Indexing workspace at '{target}' into ChromaDB...[/yellow]")
        memory = ChromaMemory()
        embeddings = get_embeddings()
        indexer = CodeIndexer(chroma_memory=memory, embeddings=embeddings)
        stats = indexer.index_workspace(target)
        console.print(
            f"[bold green]✓ Indexing Complete![/bold green] "
            f"Indexed: {stats['indexed_files']} files ({stats['total_chunks_added']} chunks), "
            f"Skipped (unchanged): {stats['skipped_files']} files."
        )
        return True

    if cmd == "/search":
        if not arg.strip():
            console.print("[red]Usage: /search <query>[/red]")
            return True
        console.print(f"[yellow]Searching web for '{arg}'...[/yellow]")
        res = await search_web(arg)
        if res.error:
            render_error(res.error)
        elif not res.results:
            console.print(f"[dim]No search results found for '{arg}'.[/dim]")
        else:
            for i, r in enumerate(res.results, 1):
                console.print(f"[bold cyan]{i}. {r.title}[/bold cyan] [dim]({r.url})[/dim]")
                console.print(f"   {r.snippet}\n")
        return True

    if cmd == "/vsearch":
        if not arg.strip():
            console.print("[red]Usage: /vsearch <query>[/red]")
            return True
        console.print(f"[yellow]Searching local ChromaDB for '{arg}'...[/yellow]")
        retriever = CodeRetriever(chroma_memory=ChromaMemory(), embeddings=get_embeddings())
        results = retriever.search(arg, n_results=4)
        if not results:
            console.print("[dim]No matching code chunks found in vector store. Run /index first.[/dim]")
        else:
            for i, r in enumerate(results, 1):
                console.print(f"[bold green]Result {i}[/bold green] [dim](Score: {r.score:.2f})[/dim] - [bold]{r.file_path}[/bold] (Lines {r.start_line}-{r.end_line}):")
                console.print(f"```\n{r.content}\n```\n")
        return True

    if cmd == "/eval":
        console.print("[yellow]Running Multi-Agent Evaluation Benchmark Suite on Groq...[/yellow]")
        try:
            agent = create_agent_graph()
        except Exception:
            agent = None
        runner = BenchmarkRunner(agent_graph=agent)
        summary = await runner.run_all()
        render_eval_summary(summary)
        return True

    if cmd == "/update":
        await update_anton()
        return True

    console.print(f"[red]Unknown slash command '{cmd}'. Type /help for available commands.[/red]")
    return True


async def run_interactive_session() -> None:
    """Launch the interactive REPL session with Gemini CLI UI."""
    render_banner()

    session: PromptSession = PromptSession(
        history=InMemoryHistory(),
        completer=SlashCommandCompleter(),
        complete_while_typing=True,
        complete_style=CompleteStyle.COLUMN,
        style=CLI_STYLE,
        bottom_toolbar=get_bottom_toolbar,
    )

    thread_id = f"session-{os.getpid()}"
    config = {"configurable": {"thread_id": thread_id}}

    agent = None
    settings = get_settings()
    if settings.GROQ_API_KEY:
        try:
            agent = create_agent_graph()
        except Exception as e:
            console.print(f"[yellow]Note initializing agent: {e}[/yellow]")
            agent = None

    while True:
        try:
            user_input = await session.prompt_async(get_prompt_tokens)
            clean_input = user_input.strip()
            if not clean_input:
                continue

            # Handle slash commands
            if clean_input.startswith("/"):
                should_continue = await handle_slash_command(clean_input)
                if not should_continue:
                    break
                continue

            # Execute agent query
            if agent:
                with console.status("[bold cyan]✦ Anton is thinking...[/bold cyan]", spinner="dots"):
                    state = {
                        "messages": [HumanMessage(content=clean_input)],
                        "workspace_path": str(Path.cwd()),
                        "pending_tool_call": None,
                        "approval_granted": None,
                        "input_sanitized": False,
                        "guardrail_flagged": False,
                        "guardrail_reasons": [],
                        "retrieved_context": None,
                    }
                    result_state = await agent.ainvoke(state, config=config)

                last_msg = result_state["messages"][-1]
                render_markdown(str(last_msg.content))
            else:
                console.print(
                    "\n[bold yellow]⚠️ Groq API key is not configured.[/bold yellow]\n"
                    "Add your [bold]GROQ_API_KEY[/bold] in [bold cyan].env[/bold cyan] or run [bold cyan]/doctor[/bold cyan] for setup instructions.\n"
                    "You can still use slash commands like [bold cyan]/help[/bold cyan], [bold cyan]/index[/bold cyan], [bold cyan]/search[/bold cyan], and [bold cyan]/vsearch[/bold cyan].\n"
                )

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]✦ Session ended. Goodbye![/dim]")
            break
        except Exception as e:
            render_error(str(e))
