# Anton (`ai-cli`)

Autonomous, high-performance CLI coding and reasoning assistant powered by LangGraph, Groq API, Google Custom Search, and a local ChromaDB vector store.

## Features
- **Ultra-Fast LLM Reasoning**: Powered by Groq (`llama-3.3-70b-versatile`).
- **Local ChromaDB Vector Search**: Semantic search over project code and documentation with FastEmbed.
- **Full File & Shell Tooling**: Read, write, smart patch/diff, search, and safe command execution.
- **Web Search**: Google Custom Search integration.
- **Robust Guardrails**: Multi-layer defense against prompt injection, system prompt leakage, and unsafe execution.
- **Multi-Agent Evaluations**: Automated multi-agent validation (Judge, Safety Auditor, Code Quality Evaluator).
- **Rich Terminal UI**: Syntax highlighting, diff viewing, auto-suggestions, and approval flows.

## Quick Start
```bash
# Install dependencies
pip install -e ".[dev]"

# Set environment variables
cp .env.example .env

# Run Anton
anton
```
