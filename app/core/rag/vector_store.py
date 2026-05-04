"""ChromaDB vector store integration."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.rag.chunker import DocumentChunk
from app.core.rag.embedding_model import EmbeddingModel
from app.utils.file_utils import ensure_directory

logger = logging.getLogger(__name__)


class VectorStoreUnavailable(RuntimeError):
    """Raised when ChromaDB is unavailable."""


@dataclass(slots=True)
class RetrievedChunk:
    text: str
    source: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class ChromaVectorStore:
    """Persistent ChromaDB-backed vector store."""

    def __init__(self, persist_path: Path, collection_name: str, embedding_model: EmbeddingModel) -> None:
        self.persist_path = ensure_directory(persist_path)
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self._client: Any | None = None
        self._collection: Any | None = None
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        try:
            self._ensure_collection()
            return True
        except Exception as exc:
            logger.warning("Vector store is unavailable: %s", exc)
            return False

    def add_documents(self, chunks: list[DocumentChunk]) -> int:
        if not chunks:
            return 0
        collection = self._ensure_collection()
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_model.embed(texts)
        ids = [self._chunk_id(chunk, index) for index, chunk in enumerate(chunks)]
        metadatas = [_sanitize_metadata(chunk.metadata) for chunk in chunks]

        if hasattr(collection, "upsert"):
            collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        else:
            collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        self._persist_if_supported()
        return len(chunks)

    def query(self, query: str, top_k: int = 5, category: str | None = None) -> list[RetrievedChunk]:
        collection = self._ensure_collection()
        query_embedding = self.embedding_model.embed([query])[0]
        where = {"category": category} if category else None
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        retrieved: list[RetrievedChunk] = []
        for text, metadata, distance in zip(documents, metadatas, distances, strict=False):
            score = 1.0 / (1.0 + float(distance or 0.0))
            metadata = metadata or {}
            retrieved.append(
                RetrievedChunk(
                    text=text,
                    source=str(metadata.get("source", "unknown")),
                    score=round(score, 4),
                    metadata=dict(metadata),
                )
            )
        return retrieved

    def count(self) -> int:
        try:
            return int(self._ensure_collection().count())
        except Exception:
            return 0

    def categories(self) -> list[str]:
        try:
            collection = self._ensure_collection()
            result = collection.get(include=["metadatas"], limit=100000)
        except Exception:
            return []
        categories = {
            metadata.get("category")
            for metadata in result.get("metadatas", [])
            if isinstance(metadata, dict) and metadata.get("category")
        }
        return sorted(str(category) for category in categories)

    def _ensure_collection(self) -> Any:
        if self._collection is not None:
            return self._collection
        with self._lock:
            if self._collection is not None:
                return self._collection

            try:
                import chromadb
            except ImportError as exc:
                raise VectorStoreUnavailable(
                    "ChromaDB is not installed. Install chromadb from requirements.txt."
                ) from exc

            # Chroma can throw intermittent KeyError during concurrent initialization.
            # We initialize under a lock and retry once.
            last_error: Exception | None = None
            for _ in range(2):
                try:
                    client = chromadb.PersistentClient(path=str(self.persist_path))
                    collection = client.get_or_create_collection(
                        name=self.collection_name,
                        metadata={"hnsw:space": "cosine"},
                    )
                    self._client = client
                    self._collection = collection
                    return self._collection
                except KeyError as exc:
                    last_error = exc
                    self._client = None
                    self._collection = None

            raise VectorStoreUnavailable(f"ChromaDB initialization failed: {last_error}")

    def _persist_if_supported(self) -> None:
        if self._client is not None and hasattr(self._client, "persist"):
            self._client.persist()

    @staticmethod
    def _chunk_id(chunk: DocumentChunk, fallback_index: int) -> str:
        source = str(chunk.metadata.get("source", "unknown")).replace("/", "_")
        index = chunk.metadata.get("chunk_index", fallback_index)
        page = chunk.metadata.get("page", "none")
        return f"{source}:{page}:{index}"


def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    sanitized: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        else:
            sanitized[key] = str(value)
    return sanitized
