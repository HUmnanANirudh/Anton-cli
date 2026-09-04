"""Local embedding model integration using FastEmbed."""

from functools import lru_cache
from typing import List
from fastembed import TextEmbedding
from ai_cli.config.settings import get_settings


class LocalEmbeddings:
    """Wrapper around FastEmbed for high-performance, offline local embeddings."""

    def __init__(self, model_name: str | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model: TextEmbedding | None = None

    @property
    def model(self) -> TextEmbedding:
        """Lazy load the FastEmbed model."""
        if self._model is None:
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Compute embeddings for a list of document strings."""
        if not documents:
            return []
        embeddings = list(self.model.embed(documents))
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> List[float]:
        """Compute embedding for a single search query."""
        embeddings = list(self.model.embed([query]))
        return embeddings[0].tolist()


@lru_cache(maxsize=1)
def get_embeddings() -> LocalEmbeddings:
    """Singleton getter for local embeddings."""
    return LocalEmbeddings()
