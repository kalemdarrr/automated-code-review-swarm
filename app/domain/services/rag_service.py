"""Application service for RAG ingestion and status."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.core.rag.chunker import TokenChunker
from app.core.rag.document_loader import DocumentLoader
from app.core.rag.vector_store import ChromaVectorStore


@dataclass(slots=True)
class RAGIngestSummary:
    indexed_documents: int
    indexed_chunks: int
    categories: list[str]


class RAGService:
    def __init__(self, settings: Settings, vector_store: ChromaVectorStore) -> None:
        self.settings = settings
        self.vector_store = vector_store

    def ingest(self) -> RAGIngestSummary:
        documents = DocumentLoader(self.settings.knowledge_base_raw_path).load()
        chunks = TokenChunker().chunk_documents(documents)
        indexed_chunks = self.vector_store.add_documents(chunks)
        return RAGIngestSummary(
            indexed_documents=len(documents),
            indexed_chunks=indexed_chunks,
            categories=self.vector_store.categories(),
        )

    def status(self) -> dict[str, object]:
        return {
            "vector_db_available": self.vector_store.available,
            "indexed_documents": self.vector_store.count(),
            "categories": self.vector_store.categories(),
            "collection_name": self.settings.chroma_collection_name,
        }

