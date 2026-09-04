"""Tests for ChromaDB memory manager."""

import tempfile
from pathlib import Path
from ai_cli.memory.chroma import ChromaMemory


def test_chroma_crud_operations():
    """Verify ChromaDB collection creation, upsert, query, and delete."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        memory = ChromaMemory(persist_dir=tmp_dir)
        col_name = "test_col"

        # 1. Upsert with orthogonal unit vectors
        ids = ["chunk1", "chunk2"]
        docs = ["def add(a, b): return a + b", "def subtract(a, b): return a - b"]
        
        vec1 = [1.0] + [0.0] * 383
        vec2 = [0.0, 1.0] + [0.0] * 382
        embeddings = [vec1, vec2]
        
        metadatas = [
            {"file_path": "math/ops.py", "start_line": 1, "end_line": 2, "file_hash": "hash1"},
            {"file_path": "math/ops.py", "start_line": 3, "end_line": 4, "file_hash": "hash1"},
        ]

        memory.upsert(
            collection_name=col_name,
            ids=ids,
            documents=docs,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        col = memory.get_or_create_collection(col_name)
        assert col.count() == 2

        # 2. Check file hashes
        hashes = memory.get_file_hashes(col_name)
        assert hashes.get("math/ops.py") == "hash1"

        # 3. Query closest to vec1
        query_emb = [1.0] + [0.0] * 383
        res = memory.query(collection_name=col_name, query_embedding=query_emb, n_results=1)
        assert len(res["ids"][0]) == 1
        assert res["ids"][0][0] == "chunk1"

        # 4. Delete by file
        memory.delete_by_file(collection_name=col_name, file_path="math/ops.py")
        assert memory.get_or_create_collection(col_name).count() == 0
