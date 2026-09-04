"""Tests for FastEmbed local embeddings."""

from ai_cli.memory.embeddings import LocalEmbeddings


def test_embed_documents_and_query():
    """Verify local embedding generation dimensionality and consistency."""
    embeddings = LocalEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    
    docs = ["def hello(): return 'world'", "class UserProfile: pass"]
    doc_vectors = embeddings.embed_documents(docs)
    
    assert len(doc_vectors) == 2
    assert len(doc_vectors[0]) == 384  # BAAI/bge-small-en-v1.5 produces 384-dim vectors
    assert len(doc_vectors[1]) == 384

    query = "function definition"
    query_vector = embeddings.embed_query(query)
    assert len(query_vector) == 384
    assert isinstance(query_vector[0], float)


def test_embed_empty_documents():
    """Verify handling of empty list."""
    embeddings = LocalEmbeddings()
    assert embeddings.embed_documents([]) == []
