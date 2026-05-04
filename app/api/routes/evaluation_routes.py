"""Evaluation API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.schemas.evaluation_schema import EvaluationRunResponse
from app.dependencies import get_evaluation_service
from app.domain.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation(service: EvaluationService = Depends(get_evaluation_service)) -> EvaluationRunResponse:
    return EvaluationRunResponse(**service.run())

