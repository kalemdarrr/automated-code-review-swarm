"""Application service for code review requests."""

from __future__ import annotations

from app.core.orchestration.swarm_orchestrator import SwarmOrchestrator
from app.domain.entities.code_review_result import CodeReviewResult


class ReviewService:
    def __init__(self, orchestrator: SwarmOrchestrator) -> None:
        self.orchestrator = orchestrator

    def review_code(
        self,
        code: str,
        language: str,
        review_depth: str,
        include_security: bool,
        include_clean_code: bool,
        include_rag_sources: bool = True,
    ) -> CodeReviewResult:
        return self.orchestrator.run_review(
            code=code,
            language=language,
            review_depth=review_depth,
            include_security=include_security,
            include_clean_code=include_clean_code,
            include_rag_sources=include_rag_sources,
        )

