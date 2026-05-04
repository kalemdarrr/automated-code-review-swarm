"""RAG retrieval facade."""

from __future__ import annotations

from app.core.rag.vector_store import ChromaVectorStore, RetrievedChunk


class Retriever:
    def __init__(self, vector_store: ChromaVectorStore) -> None:
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = 5, category: str | None = None) -> list[RetrievedChunk]:
        return self.vector_store.query(query=query, top_k=top_k, category=category)

