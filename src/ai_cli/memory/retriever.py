"""Vector retriever for codebase and document semantic search."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from ai_cli.memory.chroma import ChromaMemory
from ai_cli.memory.embeddings import LocalEmbeddings, get_embeddings


class SearchResult(BaseModel):
    """Structured search result from vector store."""

    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    distance: float
    score: float


class CodeRetriever:
    """Retrieves relevant code chunks and context from ChromaDB vector store."""

    def __init__(
        self,
        chroma_memory: Optional[ChromaMemory] = None,
        embeddings: Optional[LocalEmbeddings] = None,
    ):
        self.memory = chroma_memory or ChromaMemory()
        self.embeddings = embeddings or get_embeddings()

    def search(
        self,
        query: str,
        n_results: int = 5,
        collection_name: str = ChromaMemory.DEFAULT_COLLECTION,
        file_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search ChromaDB for relevant code snippets."""
        if not query.strip():
            return []

        query_emb = self.embeddings.embed_query(query)
        where_clause: Optional[Dict[str, Any]] = None
        if file_filter:
            where_clause = {"file_path": file_filter}

        raw_results = self.memory.query(
            collection_name=collection_name,
            query_embedding=query_emb,
            n_results=n_results,
            where=where_clause,
        )

        results: List[SearchResult] = []
        if not raw_results or not raw_results.get("ids") or not raw_results["ids"][0]:
            return results

        ids = raw_results["ids"][0]
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        for i in range(len(ids)):
            meta = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else 1.0
            # Cosine similarity score = 1.0 - distance
            score = max(0.0, 1.0 - dist)

            results.append(
                SearchResult(
                    chunk_id=ids[i],
                    file_path=meta.get("file_path", "unknown"),
                    start_line=int(meta.get("start_line", 1)),
                    end_line=int(meta.get("end_line", 1)),
                    content=documents[i] if i < len(documents) else "",
                    distance=float(dist),
                    score=float(score),
                )
            )

        return results

    def format_context_for_llm(
        self,
        query: str,
        n_results: int = 4,
        collection_name: str = ChromaMemory.DEFAULT_COLLECTION,
    ) -> str:
        """Retrieve and format search results as context string for LLM prompts."""
        results = self.search(query=query, n_results=n_results, collection_name=collection_name)
        if not results:
            return "No relevant code context found in vector database."

        formatted_chunks = []
        for i, res in enumerate(results, 1):
            formatted_chunks.append(
                f"### Result {i} (Score: {res.score:.2f}) - `{res.file_path}` (Lines {res.start_line}-{res.end_line}):\n"
                f"```\n{res.content}\n```"
            )

        return "\n\n".join(formatted_chunks)
