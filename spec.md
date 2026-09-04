# Anton CLI (`ai-cli`) - Technical Specification

## 1. Overview & Goals
Anton (`ai-cli`) is a high-performance, autonomous CLI coding and reasoning assistant powered by LangGraph, ChromaDB local vector storage, Groq API as the primary LLM engine (for ultra-fast multi-agent reasoning and evaluation), Google Custom Search for web retrieval, robust guardrails against prompt leakage, and a multi-agent evaluation framework.

## 2. Target Project Architecture & Directory Structure
```
ai-cli/
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── README.md
│
├── data/
│   └── chroma/                 # Local ChromaDB persistent storage
│
├── src/
│   └── ai_cli/
│       ├── __init__.py
│       ├── main.py             # CLI entry point
│       │
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── app.py          # Interactive CLI (prompt_toolkit / REPL)
│       │   ├── renderer.py     # Markdown / syntax highlighting / streaming
│       │   ├── prompts.py      # Approval & confirmation UI dialogs
│       │   └── suggestions.py  # Auto-suggestions & slash command autocompletion
│       │
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── graph.py        # LangGraph StateGraph & workflow execution
│       │   ├── state.py        # AgentState definition
│       │   ├── nodes.py        # Graph nodes (reasoning, tool routing, checkpointing)
│       │   └── prompts.py      # Modular agent prompts & system instructions
│       │
│       ├── guardrails/
│       │   ├── __init__.py
│       │   ├── input_guard.py  # Prompt injection, secret leakage, malicious intent detection
│       │   ├── output_guard.py # System prompt protection, canary tokens, sensitive data filtering
│       │   └── execution_guard.py # Dangerous command & file path safety fences
│       │
│       ├── evaluations/
│       │   ├── __init__.py
│       │   ├── multi_agent_eval.py # Multi-agent evaluation orchestrator (Judge, Safety, Code)
│       │   ├── benchmark.py    # Standard benchmark runner
│       │   ├── evaluators.py   # Metrics (Safety, Tool Selection, Code Quality)
│       │   └── test_cases.json # Golden dataset for regression testing
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── filesystem/
│       │   │   ├── read.py
│       │   │   ├── write.py
│       │   │   ├── tree.py
│       │   │   ├── grep.py
│       │   │   └── patch.py     # Unified diff / smart patching
│       │   │
│       │   ├── shell/
│       │   │   ├── execute.py   # Async subprocess execution
│       │   │   └── safety.py    # Command blacklist / risky pattern checks
│       │   │
│       │   └── web/
│       │       ├── search.py    # Google Custom Search API integration
│       │       └── retrieval.py # URL scraping & markdown extraction
│       │
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── embeddings.py   # Local FastEmbed embeddings (HuggingFace/FastEmbed)
│       │   ├── chroma.py       # Persistent ChromaDB client & collection management
│       │   ├── indexer.py      # Code chunking (language-aware) & indexing
│       │   └── retriever.py    # Semantic code retriever
│       │
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── factory.py      # LLM provider factory
│       │   ├── groq.py         # Groq provider (Primary / Default)
│       │   └── base.py         # Base LLM provider interface
│       │
│       ├── workspace/
│       │   ├── __init__.py
│       │   ├── discovery.py    # Project structure & language detection
│       │   └── index.py        # Workspace context manager
│       │
│       └── config/
│           ├── __init__.py
│           └── settings.py     # Pydantic Settings & environment config
│
└── tests/
    ├── test_tools/
    ├── test_agent/
    ├── test_guardrails/
    ├── test_memory/
    └── test_evaluations/
```

## 3. Key Specifications

### 3.1 LLM Engine: Groq API
- High-speed inference using Groq models (e.g. `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`).
- Multi-agent evaluation: Multiple concurrent evaluation agents (Judge, Guardrail Auditor, Code Syntax Validator) run on Groq to evaluate agent outputs rapidly.

### 3.2 Web Search: Google Custom Search API
- Direct Google Custom Search integration using `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` (`cx`).
- Automatic snippet extraction, URL ranking, and retrieval tool for deeper page reading.

### 3.3 Vector Database: Local ChromaDB
- Local storage under `data/chroma/`.
- Local embeddings via FastEmbed (`all-MiniLM-L6-v2` or `bge-small-en-v1.5`) for fast, offline indexing with zero API cost.

### 3.4 Guardrails
- **Input Guard**: Sanitizes input, prevents prompt injection, detects secret strings.
- **Output Guard**: Strict system prompt defense (canary tokens, pattern matching against instruction leakage), redacting sensitive tokens.
- **Execution Guard**: Interactive approval before any file writes or shell command executions.

### 3.5 Multi-Agent Evaluations
- Automated test runner that executes test cases against:
  1. *Judge Agent*: Evaluates task fulfillment and reasoning correctness.
  2. *Safety/Guardrail Auditor Agent*: Tests prompt leakage resistance and red-teaming vectors.
  3. *Code & Patch Evaluator Agent*: Evaluates code syntax, diff correctness, and formatting.

## 4. Step-by-Step Implementation Strategy
Each step is built, verified with unit tests, and paused for evaluation before continuing:
- **Step 1**: Project Scaffolding, `pyproject.toml`, Settings & Configuration.
- **Step 2**: Local ChromaDB Vector Store & Codebase Indexer.
- **Step 3**: Core Tools Layer (Filesystem, Shell runner, Google Search).
- **Step 4**: Guardrails Subsystem (Input, Output prompt-leak defense, Execution boundaries).
- **Step 5**: Groq LLM Provider & Factory.
- **Step 6**: LangGraph Agent Core (State, Nodes, Routing, Human Approval Checkpoints).
- **Step 7**: Multi-Agent Evaluation Framework & Benchmark Suite.
- **Step 8**: Interactive CLI & Terminal UI (Rich REPL, syntax highlighting, diff viewer, auto-suggestions).
