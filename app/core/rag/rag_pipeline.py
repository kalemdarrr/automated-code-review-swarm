"""End-to-end RAG query pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import Settings, get_settings
from app.core.rag.retriever import Retriever
from app.core.rag.vector_store import RetrievedChunk
from app.utils.text_utils import truncate_text


@dataclass(slots=True)
class RAGResult:
    retrieved_context: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    low_confidence: bool = True


class RAGPipeline:
    """Builds review-oriented RAG queries and formats retrieved evidence."""

    def __init__(self, retriever: Retriever, settings: Settings | None = None) -> None:
        self.retriever = retriever
        self.settings = settings or get_settings()

    def run(
        self,
        user_code: str,
        review_objective: str,
        language: str = "python",
        top_k: int | None = None,
        category: str | None = None,
    ) -> RAGResult:
        query = self._build_query(user_code, review_objective, language)
        chunks = self.retriever.retrieve(
            query=query,
            top_k=top_k or self.settings.default_top_k,
            category=category,
        )
        return self._format_result(chunks)

    def _build_query(self, user_code: str, review_objective: str, language: str) -> str:
        code_excerpt = truncate_text(user_code, 2200)
        return (
            f"Code review objective: {review_objective}. Language: {language}. "
            "Find relevant Clean Code, SOLID, OWASP, secure coding, Python, and PyTorch guidance. "
            f"Code excerpt: {code_excerpt}"
        )

    def _format_result(self, chunks: list[RetrievedChunk]) -> RAGResult:
        if not chunks:
            return RAGResult(
                retrieved_context="No RAG context was retrieved. Knowledge base confidence is low for this specific claim.",
                sources=[],
                confidence_score=0.0,
                low_confidence=True,
            )

        context_blocks: list[str] = []
        sources: list[dict[str, Any]] = []
        for index, chunk in enumerate(chunks, start=1):
            snippet = truncate_text(chunk.text, 700)
            category = chunk.metadata.get("category", "general")
            context_blocks.append(
                f"[Source {index}] source={chunk.source}; category={category}; score={chunk.score}\n{snippet}"
            )
            sources.append(
                {
                    "source": chunk.source,
                    "category": category,
                    "relevance_score": chunk.score,
                    "snippet": snippet,
                    "metadata": chunk.metadata,
                }
            )

        average_score = sum(chunk.score for chunk in chunks) / len(chunks)
        low_confidence = average_score < self.settings.rag_low_confidence_threshold
        if low_confidence:
            context_blocks.append("Knowledge base confidence is low for this specific claim.")

        return RAGResult(
            retrieved_context="\n\n".join(context_blocks),
            sources=sources,
            confidence_score=round(average_score, 4),
            low_confidence=low_confidence,
        )

