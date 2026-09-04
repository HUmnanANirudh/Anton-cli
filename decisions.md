# Anton CLI - Architectural & Design Decisions

## Decision Index
- **ADR-001**: [CLI Interface & Interaction Paradigm] -> **Hybrid REPL + One-shot Subcommand support**
- **ADR-002**: [Agent Orchestration Engine] -> **LangGraph StateGraph with Tool-Calling & Human-in-the-loop Interruption**
- **ADR-003**: [LLM Provider] -> **Groq API as Primary Provider (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`)**
- **ADR-004**: [Web Search Engine] -> **Google Custom Search API (`GOOGLE_API_KEY`, `GOOGLE_CSE_ID`)**
- **ADR-005**: [Local Vector Store] -> **ChromaDB located at `data/chroma/` with fast local embeddings (FastEmbed / sentence-transformers)**
- **ADR-006**: [Guardrails & Prompt Defense] -> **3-Tier Guardrails (Input, Output canary/leak defense, Execution safety barriers)**
- **ADR-007**: [Evaluation Framework] -> **Multi-Agent Evaluation via Groq (Judge Agent, Safety Auditor, Code Quality Evaluator)**
- **ADR-008**: [Incremental Delivery] -> **Step-by-step implementation, stopping after each step for testing and evaluation**

---

### Key ADR Summaries

#### ADR-003: Groq LLM Provider
- Chosen for near-instant token generation speeds, making terminal interactions snappy and multi-agent evaluation rounds fast and cost-effective.

#### ADR-004: Google Custom Search
- Directly interfaces with Google CSE to provide accurate, live web search results as specified in user requirements.

#### ADR-007: Multi-Agent Evaluation System
- Uses Groq to concurrently launch multiple evaluator agents:
  1. *Judge Agent*: Verifies task completion.
  2. *Safety/Guardrail Auditor*: Red-teams agent outputs for prompt leakage and injection vulnerabilities.
  3. *Code & Patch Evaluator*: Validates syntax and AST diff integrity.
