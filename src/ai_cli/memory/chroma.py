"""ChromaDB persistent client and collection management."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings
from ai_cli.config.settings import get_settings


class ChromaMemory:
    """Manages persistent ChromaDB vector store for Anton CLI."""

    DEFAULT_COLLECTION = "anton_codebase"

    def __init__(self, persist_dir: Optional[Path | str] = None):
        settings = get_settings()
        if persist_dir:
            self.persist_dir = Path(persist_dir)
        else:
            self.persist_dir = settings.chroma_full_path

        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, name: str = DEFAULT_COLLECTION) -> Collection:
        """Retrieve or initialize a ChromaDB collection with cosine distance."""
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Upsert vectors into the specified collection."""
        if not ids:
            return
        col = self.get_or_create_collection(collection_name)
        col.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform similarity search on the collection."""
        col = self.get_or_create_collection(collection_name)
        count = col.count()
        if count == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        actual_k = min(n_results, count)
        return col.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
            where=where,
        )

    def delete_by_file(self, collection_name: str, file_path: str) -> None:
        """Delete all chunks belonging to a specific file."""
        col = self.get_or_create_collection(collection_name)
        try:
            col.delete(where={"file_path": file_path})
        except Exception:
            pass

    def get_file_hashes(self, collection_name: str = DEFAULT_COLLECTION) -> Dict[str, str]:
        """Return a mapping of file_path -> content_hash for all indexed files."""
        col = self.get_or_create_collection(collection_name)
        results = col.get(include=["metadatas"])
        file_hashes: Dict[str, str] = {}
        if results and results.get("metadatas"):
            for meta in results["metadatas"]:
                if meta and "file_path" in meta and "file_hash" in meta:
                    file_hashes[meta["file_path"]] = meta["file_hash"]
        return file_hashes

    def reset_collection(self, collection_name: str = DEFAULT_COLLECTION) -> None:
        """Reset / clear a collection."""
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
