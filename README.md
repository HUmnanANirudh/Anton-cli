# Anton (`ai-cli`)

Autonomous, high-performance CLI coding and reasoning assistant powered by LangGraph, Groq API, Tavily / Google Search, and a local ChromaDB vector store.

## Features
- **Ultra-Fast LLM Reasoning**: Powered by Groq (`llama-3.3-70b-versatile`).
- **Local ChromaDB Vector Search**: Semantic search over project code and documentation with FastEmbed.
- **Full File & Shell Tooling**: Read, write, smart patch/diff, search, and safe command execution.
- **Web Search**: Tavily Search integration with Google Custom Search fallback.
- **Robust Guardrails**: Multi-layer defense against prompt injection, system prompt leakage, and unsafe execution.
- **Multi-Agent Evaluations**: Automated multi-agent validation (Judge, Safety Auditor, Code Quality Evaluator).
- **Rich Terminal UI**: Syntax highlighting, diff viewing, auto-suggestions, and approval flows.

## Requirements & Package Management
This project uses **`uv`** for all package management, virtual environments, and running commands. Do not use raw `pip`.

### Setup with `uv`
```bash
# 1. Create a virtual environment with uv
uv venv

# 2. Install dependencies with uv
uv pip install -e ".[dev]"

# 3. Set environment variables
cp .env.example .env
# Edit .env with your GROQ_API_KEY and TAVILY_API_KEY

# 4. Run Anton CLI with uv
uv run anton
```

### Running Tests with `uv`
```bash
uv run pytest
```
