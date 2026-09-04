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
- **Self-Update**: Built-in `--update` command to synchronize and pull the latest release.

## Quick Start & Installation
This project uses **`uv`** for all package management and running commands.

### 1. Setup
```bash
# 1. Copy and configure API keys
cp .env.example .env
# Edit .env with your GROQ_API_KEY and TAVILY_API_KEY

# 2. Enable global 'anton' command
./install.sh
```

### 2. Usage
```bash
# Run Anton CLI from anywhere in your terminal
anton

# Pull latest version & update
anton --update

# Index your workspace into local vector DB
anton --index .

# Run the multi-agent evaluation benchmark
anton --eval

# Show version
anton --version
```

### 3. Running Tests
```bash
uv run pytest
```
