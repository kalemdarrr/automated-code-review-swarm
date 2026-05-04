"""RAG research agent."""

from __future__ import annotations

from typing import Any

from app.core.agents.base_agent import BaseAgent
from app.core.rag.rag_pipeline import RAGPipeline


class RAGResearchAgent(BaseAgent):
    def __init__(self, rag_pipeline: RAGPipeline, **kwargs: Any) -> None:
        super().__init__(
            name="RAGResearchAgent",
            role="Retrieve relevant knowledge base context and citations.",
            system_prompt="Retrieve relevant sources from the local vector database.",
            **kwargs,
        )
        self.rag_pipeline = rag_pipeline

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        result = self.rag_pipeline.run(
            user_code=str(input_data.get("code", "")),
            review_objective=str(input_data.get("review_objective", "code review and security audit")),
            language=str(input_data.get("language", "python")),
            top_k=input_data.get("top_k"),
        )
        return {
            "retrieved_context": result.retrieved_context,
            "sources": result.sources,
            "confidence_score": result.confidence_score,
            "low_confidence": result.low_confidence,
        }

