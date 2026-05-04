from __future__ import annotations

import importlib.util

import pytest

from app.core.rag.chunker import TokenChunker
from app.core.rag.document_loader import KnowledgeDocument
from app.core.rag.embedding_model import HashingEmbeddingModel
from app.core.rag.retriever import Retriever
from app.core.rag.vector_store import ChromaVectorStore


def test_chunker_preserves_metadata_and_overlap() -> None:
    document = KnowledgeDocument(
        text=" ".join(f"token{i}" for i in range(30)),
        metadata={"source": "demo.md", "category": "clean_code"},
    )
    chunks = TokenChunker(chunk_size=10, overlap=2).chunk_document(document)

    assert len(chunks) == 4
    assert chunks[0].metadata["category"] == "clean_code"
    assert chunks[1].metadata["token_start"] == 8


def test_retriever_delegates_to_vector_store() -> None:
    class FakeStore:
        def query(self, query: str, top_k: int, category: str | None = None):
            return [{"query": query, "top_k": top_k, "category": category}]

    result = Retriever(FakeStore()).retrieve("sql injection", top_k=3, category="owasp")

    assert result == [{"query": "sql injection", "top_k": 3, "category": "owasp"}]


@pytest.mark.skipif(importlib.util.find_spec("chromadb") is None, reason="chromadb is not installed")
def test_chromadb_index_and_query(tmp_path) -> None:
    store = ChromaVectorStore(tmp_path, "test_collection", HashingEmbeddingModel())
    chunks = TokenChunker(chunk_size=20, overlap=2).chunk_documents(
        [
            KnowledgeDocument(
                text="SQL injection requires parameterized queries and bound variables.",
                metadata={"source": "owasp.md", "category": "owasp"},
            )
        ]
    )

    assert store.add_documents(chunks) == 1
    results = store.query("parameterized SQL injection", top_k=1)

    assert results
    assert results[0].metadata["category"] == "owasp"

