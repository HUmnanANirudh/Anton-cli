"""Tests for CodeIndexer and CodeRetriever integration."""

import tempfile
from pathlib import Path
from ai_cli.memory.chroma import ChromaMemory
from ai_cli.memory.embeddings import LocalEmbeddings
from ai_cli.memory.indexer import CodeIndexer
from ai_cli.memory.retriever import CodeRetriever


def test_index_and_retrieve_workspace():
    """Verify workspace file scanning, chunking, indexing, and semantic retrieval."""
    with tempfile.TemporaryDirectory() as tmp_workspace, tempfile.TemporaryDirectory() as tmp_chroma:
        workspace_path = Path(tmp_workspace)
        
        # Create dummy project files
        src_dir = workspace_path / "src"
        src_dir.mkdir(parents=True)
        
        calc_file = src_dir / "calculator.py"
        calc_file.write_text(
            "def multiply(x, y):\n"
            "    '''Multiply two numbers.'''\n"
            "    return x * y\n\n"
            "def divide(x, y):\n"
            "    '''Divide x by y safely.'''\n"
            "    if y == 0:\n"
            "        raise ValueError('Cannot divide by zero')\n"
            "    return x / y\n",
            encoding="utf-8",
        )

        ignored_dir = workspace_path / "node_modules"
        ignored_dir.mkdir(parents=True)
        (ignored_dir / "index.js").write_text("console.log('ignored');")

        # Initialize memory & embeddings
        embeddings = LocalEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        memory = ChromaMemory(persist_dir=tmp_chroma)
        indexer = CodeIndexer(chroma_memory=memory, embeddings=embeddings, chunk_size_lines=10)
        retriever = CodeRetriever(chroma_memory=memory, embeddings=embeddings)

        # 1. First index run
        stats = indexer.index_workspace(workspace_path)
        assert stats["indexed_files"] == 1
        assert stats["skipped_files"] == 0
        assert stats["total_chunks_added"] >= 1

        # 2. Second index run without changes (incremental hash check)
        stats2 = indexer.index_workspace(workspace_path)
        assert stats2["indexed_files"] == 0
        assert stats2["skipped_files"] == 1

        # 3. Retrieve relevant chunk
        results = retriever.search("how to divide numbers safely", n_results=2)
        assert len(results) > 0
        assert "calculator.py" in results[0].file_path
        assert "divide" in results[0].content

        # 4. Formatted LLM context
        context = retriever.format_context_for_llm("multiplication logic")
        assert "calculator.py" in context
        assert "multiply" in context
