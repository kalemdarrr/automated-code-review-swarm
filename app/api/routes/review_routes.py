"""Code review API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.schemas.review_schema import ReviewRequest, ReviewResponse
from app.dependencies import get_review_service
from app.domain.services.review_service import ReviewService

router = APIRouter(tags=["review"])


@router.post("/review", response_model=ReviewResponse)
def review_code(
    request: ReviewRequest,
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    result = service.review_code(
        code=request.code,
        language=request.language,
        review_depth=request.review_depth,
        include_security=request.include_security,
        include_clean_code=request.include_clean_code,
        include_rag_sources=request.include_rag_sources,
    )
    payload = result.as_dict()
    return ReviewResponse(
        final_report=payload["final_report"],
        agent_trace=payload["agent_trace"],
        risk_score=payload["risk_score"],
        rag_sources=payload["rag_sources"],
        evaluation_notes=payload["evaluation_notes"],
        security_findings=payload["security_findings"],
        clean_code_findings=payload["clean_code_findings"],
    )

