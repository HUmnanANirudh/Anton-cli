"""Interactive REPL application loop with clean Gemini UI, no bottom bar, and model switching."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from langchain_core.messages import BaseMessage, HumanMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle
from ai_cli.agent.graph import create_agent_graph
from ai_cli.cli.renderer import (
    console,
    extract_thoughts_and_response,
    render_banner,
    render_diff,
    render_doctor_report,
    render_error,
    render_eval_summary,
    render_markdown,
    render_models_table,
    render_response_box,
    render_thinking,
    render_tool_call,
    render_user_input,
)
from ai_cli.cli.suggestions import CLI_STYLE, SLASH_COMMANDS, SlashCommandCompleter
from ai_cli.cli.updater import update_anton
from ai_cli.config.settings import get_settings
from ai_cli.evaluations.benchmark import BenchmarkRunner
from ai_cli.memory.chroma import ChromaMemory
from ai_cli.memory.embeddings import get_embeddings
from ai_cli.memory.indexer import CodeIndexer
from ai_cli.memory.retriever import CodeRetriever
from ai_cli.memory.sessions import SessionManager
from ai_cli.providers.factory import ProviderFactory
from ai_cli.providers.groq import SUPPORTED_GROQ_MODELS
from ai_cli.tools.filesystem import (
    change_working_dir,
    get_current_working_dir,
    get_system_context,
)
from ai_cli.tools.web.search import search_web


class ReplContext:
    """Holds active REPL session state, current model, and history."""

    def __init__(self, initial_model: Optional[str] = None):
        settings = get_settings()
        self.session_mgr = SessionManager()
        self.session_id: str = self.session_mgr.create_session_id()
        self.session_title: str = "New Conversation"
        self.messages: List[BaseMessage] = []
        self.workspace_path: str = str(Path.cwd())
        self.initial_turn: bool = True
        self.current_model: str = initial_model or settings.GROQ_MODEL
        self.agent: Optional[Any] = None

    def initialize_agent(self) -> None:
        """Initialize or rebuild the LangGraph agent with the active model."""
        settings = get_settings()
        if not settings.GROQ_API_KEY:
            self.agent = None
            return

        try:
            provider = ProviderFactory.get_provider("groq")
            chat_model = provider.get_chat_model(model_name=self.current_model)
            self.agent = create_agent_graph(model=chat_model)
        except Exception as e:
            console.print(f"[yellow]Note initializing agent ({self.current_model}): {e}[/yellow]")
            self.agent = None


def get_prompt_tokens() -> List[Tuple[str, str]]:
    """Build clean prompt formatted like Gemini CLI (> )."""
    return [
        ("class:prompt.chevron", "> "),
    ]


async def handle_slash_command(command_str: str, ctx: ReplContext) -> bool:
    """
    Handle slash commands and direct CLI shortcuts in REPL.
    Returns True if execution should continue, False if REPL should exit.
    """
    parts = command_str.strip().split(maxsplit=1)
    raw_cmd = parts[0].lower()
    cmd = "/" + raw_cmd.lstrip("/")
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ["/exit", "/quit", "/q", "/:q", "/:wq", "/bye", "/goodbye"]:
        console.print("[white]✦ Goodbye![/white]")
        return False

    if cmd == "/clear":
        os.system("clear" if os.name != "nt" else "cls")
        sessions = ctx.session_mgr.list_sessions()
        render_banner(sessions)
        return True

    if cmd in ["/model", "/models"]:
        if not arg.strip():
            render_models_table(current_model=ctx.current_model)
            return True

        target_arg = arg.strip()
        selected_model = None

        # Check if number passed (e.g. /model 2)
        if target_arg.isdigit():
            idx = int(target_arg) - 1
            if 0 <= idx < len(SUPPORTED_GROQ_MODELS):
                selected_model = SUPPORTED_GROQ_MODELS[idx]["id"]
        else:
            # Check by model ID match
            for m in SUPPORTED_GROQ_MODELS:
                if target_arg.lower() in m["id"].lower():
                    selected_model = m["id"]
                    break
            if not selected_model:
                selected_model = target_arg

        if selected_model:
            ctx.current_model = selected_model
            ctx.initialize_agent()
            console.print(f"[bold green]✓ Switched active model to:[/bold green] [bold cyan]{ctx.current_model}[/bold cyan]\n")
        else:
            console.print(f"[red]Could not find model matching '{arg}'. Type /model to see available models.[/red]")
        return True

    if cmd == "/pwd":
        console.print(f"[bold white]✦ Current Directory:[/bold white] [bold cyan]{get_current_working_dir()}[/bold cyan]")
        return True

    if cmd == "/cd":
        if not arg.strip():
            console.print("[red]Usage: /cd <directory_path>[/red]")
            return True
        result = change_working_dir(arg.strip())
        ctx.workspace_path = get_current_working_dir()
        if result.startswith("Error") or result.startswith("Failed"):
            console.print(f"[red]{result}[/red]")
        else:
            console.print(f"[bold green]✓[/bold green] [bold white]{result}[/bold white]")
        return True

    if cmd == "/whoami":
        console.print("[bold white]✦ System Environment Context:[/bold white]")
        console.print(f"[dim]{get_system_context()}[/dim]\n")
        return True

    if cmd == "/new":
        ctx.session_id = ctx.session_mgr.create_session_id()
        ctx.session_title = "New Conversation"
        ctx.messages = []
        ctx.initial_turn = True
        console.print(f"[bold green]✦ Started new conversation session ({ctx.session_id})[/bold green]")
        return True

    if cmd == "/end":
        if ctx.messages:
            ctx.session_mgr.save_session(
                session_id=ctx.session_id,
                messages=ctx.messages,
                workspace_path=ctx.workspace_path,
            )
        old_id = ctx.session_id
        ctx.session_id = ctx.session_mgr.create_session_id()
        ctx.session_title = "New Conversation"
        ctx.messages = []
        ctx.initial_turn = True
        console.print(f"[bold green]✦ Ended conversation session ({old_id}).[/bold green]")
        console.print(f"[bold cyan]✦ Ready for new conversation ({ctx.session_id}).[/bold cyan]\n")
        return True

    if cmd in ["/sessions", "/history"]:
        sessions = ctx.session_mgr.list_sessions(limit=10)
        if not sessions:
            console.print("[dim]No previous conversations found.[/dim]")
            return True

        from rich.table import Table
        table = Table(title="✦ Previous Conversations", box=None)
        table.add_column("#", style="bold cyan", width=4)
        table.add_column("Title", style="bold white")
        table.add_column("Messages", style="dim", justify="center")
        table.add_column("Last Active", style="dim")

        for i, s in enumerate(sessions, 1):
            is_current = " (current)" if s.session_id == ctx.session_id else ""
            table.add_row(f"[{i}]", f"{s.title}{is_current}", str(s.message_count), s.updated_at or s.created_at)

        console.print(table)
        console.print("[dim]Type /session <number> to switch into any previous conversation.[/dim]\n")
        return True

    if cmd == "/session":
        if not arg.isdigit():
            console.print("[red]Usage: /session <number>[/red]")
            return True
        idx = int(arg) - 1
        sessions = ctx.session_mgr.list_sessions()
        if 0 <= idx < len(sessions):
            target = sessions[idx]
            data = ctx.session_mgr.load_session(target.session_id)
            if data:
                ctx.session_id = data["session_id"]
                ctx.session_title = data["title"]
                ctx.messages = data["messages"]
                ctx.initial_turn = False
                console.print(f"[bold green]✦ Resumed conversation:[/bold green] [bold cyan]\"{ctx.session_title}\"[/bold cyan] ({len(ctx.messages)} messages)")
            else:
                render_error(f"Failed to load session {target.session_id}")
        else:
            console.print(f"[red]Invalid session number '{arg}'. Type /sessions to see available conversations.[/red]")
        return True

    if cmd == "/delete":
        if not arg.strip():
            console.print("[red]Usage: /delete <number>[/red]")
            return True
        if not arg.strip().isdigit():
            console.print("[red]Please specify the session number to delete. (e.g. /delete 1)[/red]")
            return True
        idx = int(arg.strip()) - 1
        sessions = ctx.session_mgr.list_sessions()
        if 0 <= idx < len(sessions):
            target = sessions[idx]
            deleted = ctx.session_mgr.delete_session(target.session_id)
            if deleted:
                console.print(f"[bold green]✓ Deleted session [{idx + 1}]:[/bold green] [bold white]\"{target.title}\"[/bold white]")
                if target.session_id == ctx.session_id:
                    ctx.session_id = ctx.session_mgr.create_session_id()
                    ctx.session_title = "New Conversation"
                    ctx.messages = []
                    ctx.initial_turn = True
                    console.print("[dim]Switched to a fresh new conversation.[/dim]")
            else:
                console.print(f"[red]Failed to delete session {target.session_id}.[/red]")
        else:
            console.print(f"[red]Invalid session number '{arg}'. Type /sessions to list conversations.[/red]")
        return True

    if cmd == "/help":
        console.print("\n[bold white]✦ Available Slash Commands:[/bold white]\n")
        from rich.table import Table
        table = Table(box=None, show_header=False)
        table.add_column("Command", style="bold cyan", width=14)
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
            current_model=ctx.current_model,
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
            agent = ctx.agent or create_agent_graph()
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


async def run_interactive_session(model_name: Optional[str] = None) -> None:
    """Launch the interactive REPL session with all-white Gemini logo and model switching."""
    ctx = ReplContext(initial_model=model_name)
    ctx.initialize_agent()

    sessions = ctx.session_mgr.list_sessions()
    render_banner(sessions)

    # Clean prompt session without bottom toolbar
    session: PromptSession = PromptSession(
        history=InMemoryHistory(),
        completer=SlashCommandCompleter(),
        complete_while_typing=True,
        complete_style=CompleteStyle.COLUMN,
        style=CLI_STYLE,
    )

    while True:
        try:
            user_input = await session.prompt_async(get_prompt_tokens)
            clean_input = user_input.strip()
            if not clean_input:
                continue

            # Check if user entered a number to select a session on initial turn
            if ctx.initial_turn and clean_input.isdigit() and sessions:
                idx = int(clean_input) - 1
                if 0 <= idx < len(sessions):
                    target = sessions[idx]
                    data = ctx.session_mgr.load_session(target.session_id)
                    if data:
                        ctx.session_id = data["session_id"]
                        ctx.session_title = data["title"]
                        ctx.messages = data["messages"]
                        ctx.initial_turn = False
                        console.print(f"[bold green]✦ Resumed conversation:[/bold green] [bold cyan]\"{ctx.session_title}\"[/bold cyan] ({len(ctx.messages)} messages)")
                        continue
            
            ctx.initial_turn = False

            # Direct exit/quit checking (natural language or direct command)
            lower_input = clean_input.lower().strip().rstrip("!.;")
            if lower_input in [
                "exit", "quit", "q", ":q", ":wq", "bye", "goodbye",
                "exit session", "quit session", "exit the session", "quit the session",
                "close", "close session"
            ]:
                console.print("[white]✦ Goodbye![/white]")
                break

            if lower_input in ["end session", "end the session", "stop session", "finish session"]:
                await handle_slash_command("/end", ctx)
                continue

            # Handle slash commands or direct CLI utility commands
            if clean_input.startswith("/") or lower_input in [
                "pwd", "clear", "cls", "whoami", "help", "doctor", "new", "end",
                "sessions", "history", "models", "model", "eval", "update"
            ] or lower_input.startswith("cd ") or lower_input.startswith("delete "):
                should_continue = await handle_slash_command(clean_input, ctx)
                if not should_continue:
                    break
                continue

            # Execute agent query
            if ctx.agent:
                config = {"configurable": {"thread_id": ctx.session_id}}
                ctx.messages.append(HumanMessage(content=clean_input))

                # Render user input in styled box
                render_user_input(clean_input)

                state = {
                    "messages": ctx.messages,
                    "workspace_path": ctx.workspace_path,
                    "pending_tool_call": None,
                    "approval_granted": None,
                    "input_sanitized": False,
                    "guardrail_flagged": False,
                    "guardrail_reasons": [],
                    "retrieved_context": None,
                }

                displayed_thoughts = set()

                try:
                    with console.status(f"[bold cyan]✦ Thinking ({ctx.current_model})...[/bold cyan]", spinner="dots") as status:
                        async for event in ctx.agent.astream(state, config=config, stream_mode="updates"):
                            for node_name, node_output in event.items():
                                if node_name == "reasoning":
                                    msgs = node_output.get("messages", [])
                                    for msg in msgs:
                                        if getattr(msg, "tool_calls", None):
                                            for call in msg.tool_calls:
                                                status.stop()
                                                render_tool_call(call["name"], call.get("args", {}))
                                                status.start()
                                        raw_content = str(getattr(msg, "content", "") or "")
                                        reasoning_content = msg.additional_kwargs.get("reasoning_content") if hasattr(msg, "additional_kwargs") and msg.additional_kwargs else ""
                                        thoughts, _ = extract_thoughts_and_response(raw_content)
                                        all_thoughts = ((thoughts or "") + ("\n" + str(reasoning_content) if reasoning_content else "")).strip()
                                        if all_thoughts and all_thoughts not in displayed_thoughts:
                                            displayed_thoughts.add(all_thoughts)
                                            status.stop()
                                            render_thinking(all_thoughts)
                                            status.start()
                                elif node_name == "tools":
                                    msgs = node_output.get("messages", [])
                                    for msg in msgs:
                                        status.stop()
                                        render_tool_call("Tool Result", result=str(msg.content))
                                        status.start()

                    state_snapshot = await ctx.agent.aget_state(config)
                    if state_snapshot and state_snapshot.values and "messages" in state_snapshot.values:
                        ctx.messages = state_snapshot.values["messages"]

                except Exception:
                    with console.status(f"[bold cyan]✦ Thinking ({ctx.current_model})...[/bold cyan]", spinner="dots"):
                        result_state = await ctx.agent.ainvoke(state, config=config)
                        ctx.messages = result_state.get("messages", ctx.messages)

                last_msg = ctx.messages[-1]
                raw_last_content = str(last_msg.content)
                thoughts, final_response = extract_thoughts_and_response(raw_last_content)
                if thoughts and thoughts not in displayed_thoughts:
                    render_thinking(thoughts)

                # Render final AI response in clean box
                render_response_box(final_response or raw_last_content, model_name=ctx.current_model)

                # Keep workspace_path synced in case agent called change_directory_tool
                ctx.workspace_path = get_current_working_dir()

                # Persist session to disk
                ctx.session_mgr.save_session(
                    session_id=ctx.session_id,
                    messages=ctx.messages,
                    workspace_path=ctx.workspace_path,
                )

            else:
                console.print(
                    "\n[bold yellow]⚠️ Groq API key is not configured.[/bold yellow]\n"
                    "Add your [bold]GROQ_API_KEY[/bold] in [bold cyan].env[/bold cyan] or run [bold cyan]/doctor[/bold cyan] for setup instructions.\n"
                    "You can still use slash commands like [bold cyan]/help[/bold cyan], [bold cyan]/model[/bold cyan], [bold cyan]/index[/bold cyan], [bold cyan]/search[/bold cyan], and [bold cyan]/vsearch[/bold cyan].\n"
                )

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]✦ Session ended. Goodbye![/dim]")
            break
        except Exception as e:
            render_error(str(e))
