"""Document chunking for RAG ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.rag.document_loader import KnowledgeDocument


@dataclass(slots=True)
class DocumentChunk:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TokenChunker:
    """Word-token chunker with overlap.

    This avoids a hard tokenizer dependency during ingestion while keeping
    chunk sizes close to the requested 700-1200 token academic range.
    """

    def __init__(self, chunk_size: int = 900, overlap: int = 150) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents: list[KnowledgeDocument]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for document in documents:
            chunks.extend(self.chunk_document(document))
        return chunks

    def chunk_document(self, document: KnowledgeDocument) -> list[DocumentChunk]:
        words = document.text.split()
        if not words:
            return []
        chunks: list[DocumentChunk] = []
        start = 0
        chunk_index = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            text = " ".join(words[start:end])
            chunks.append(
                DocumentChunk(
                    text=text,
                    metadata={
                        **document.metadata,
                        "chunk_index": chunk_index,
                        "token_start": start,
                        "token_end": end,
                    },
                )
            )
            if end == len(words):
                break
            start = max(0, end - self.overlap)
            chunk_index += 1
        return chunks

