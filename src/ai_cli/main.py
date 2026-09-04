"""Main CLI entrypoint for Anton."""

import argparse
import asyncio
import sys
from pathlib import Path
from langchain_core.messages import HumanMessage
from ai_cli.agent.graph import create_agent_graph
from ai_cli.cli.app import run_interactive_session
from ai_cli.cli.renderer import (
    console,
    extract_thoughts_and_response,
    render_banner,
    render_error,
    render_eval_summary,
    render_markdown,
    render_response_box,
    render_thinking,
    render_tool_call,
    render_user_input,
)
from ai_cli.cli.updater import update_anton
from ai_cli.config.settings import get_settings
from ai_cli.evaluations.benchmark import BenchmarkRunner
from ai_cli.memory.chroma import ChromaMemory
from ai_cli.memory.embeddings import get_embeddings
from ai_cli.memory.indexer import CodeIndexer
from ai_cli.tools.web.search import search_web


def build_parser() -> argparse.ArgumentParser:
    """Configure CLI argument parser."""
    settings = get_settings()
    parser = argparse.ArgumentParser(
        prog="anton",
        description="Anton CLI - Autonomous Coding Assistant & Multi-Agent Evaluator",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="One-off prompt to execute. If omitted, launches interactive REPL.",
    )
    parser.add_argument(
        "--index",
        nargs="?",
        const=".",
        default=None,
        metavar="DIR",
        help="Index workspace directory into ChromaDB vector store.",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        metavar="QUERY",
        help="Perform a web search and display results.",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Run the multi-agent evaluation benchmark suite.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Check and update Anton CLI to the latest version.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        metavar="MODEL",
        help="Specify Groq model (e.g. llama-3.3-70b-versatile, llama-3.1-8b-instant, openai/gpt-oss-120b).",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version and exit.",
    )
    return parser


async def run_one_shot(prompt: str) -> None:
    """Execute a single prompt and print boxed output with thinking."""
    try:
        agent = create_agent_graph()
    except Exception as e:
        render_error(f"Failed to initialize agent: {e}")
        return

    render_user_input(prompt)
    config = {"configurable": {"thread_id": "oneshot-session"}}
    state = {
        "messages": [HumanMessage(content=prompt)],
        "workspace_path": str(Path.cwd()),
        "pending_tool_call": None,
        "approval_granted": None,
        "input_sanitized": False,
        "guardrail_flagged": False,
        "guardrail_reasons": [],
        "retrieved_context": None,
    }

    displayed_thoughts = set()
    try:
        with console.status("[bold cyan]✦ Thinking...[/bold cyan]", spinner="dots") as status:
            async for event in agent.astream(state, config=config, stream_mode="updates"):
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

        state_snapshot = await agent.aget_state(config)
        messages = state_snapshot.values["messages"] if state_snapshot and state_snapshot.values else []
    except Exception:
        with console.status("[bold cyan]✦ Thinking...[/bold cyan]", spinner="dots"):
            result_state = await agent.ainvoke(state, config=config)
            messages = result_state.get("messages", [])

    if messages:
        last_msg = messages[-1]
        raw_last = str(last_msg.content)
        thoughts, final_response = extract_thoughts_and_response(raw_last)
        if thoughts and thoughts not in displayed_thoughts:
            render_thinking(thoughts)
        render_response_box(final_response or raw_last)


async def async_main() -> None:
    """Async dispatch entry."""
    settings = get_settings()
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        sys.exit(0)

    if args.update:
        await update_anton()
        return

    if args.eval:
        console.print("[yellow]Running Multi-Agent Evaluation Benchmark Suite on Groq...[/yellow]")
        try:
            agent = create_agent_graph()
        except Exception:
            agent = None
        runner = BenchmarkRunner(agent_graph=agent)
        summary = await runner.run_all()
        render_eval_summary(summary)
        return

    if args.index:
        console.print(f"[yellow]Indexing workspace at '{args.index}' into ChromaDB...[/yellow]")
        memory = ChromaMemory()
        embeddings = get_embeddings()
        indexer = CodeIndexer(chroma_memory=memory, embeddings=embeddings)
        stats = indexer.index_workspace(args.index)
        console.print(
            f"[bold green]Indexing Complete![/bold green] "
            f"Indexed: {stats['indexed_files']} files ({stats['total_chunks_added']} chunks), "
            f"Skipped (unchanged): {stats['skipped_files']} files."
        )
        return

    if args.search:
        console.print(f"[yellow]Searching web for '{args.search}'...[/yellow]")
        res = await search_web(args.search)
        if res.error:
            render_error(res.error)
        elif not res.results:
            console.print(f"[dim]No search results found for '{args.search}'.[/dim]")
        else:
            for i, r in enumerate(res.results, 1):
                console.print(f"[bold cyan]{i}. {r.title}[/bold cyan] [dim]({r.url})[/dim]")
                console.print(f"   {r.snippet}\n")
        return

    if args.query:
        await run_one_shot(args.query)
        return

    # Default to interactive REPL
    await run_interactive_session(model_name=args.model)


def main() -> None:
    """CLI synchronous wrapper."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nSession terminated.")
        sys.exit(0)


if __name__ == "__main__":
    main()
