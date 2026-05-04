"""Evaluation API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EvaluationRunResponse(BaseModel):
    total_examples: int
    detected_vulnerabilities: int
    missed_vulnerabilities: int
    false_positives: int
    rag_relevance_average: float
    latency_average: float
    final_score: float
    metrics: dict[str, Any]

