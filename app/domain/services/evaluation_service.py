"""Application service for benchmark evaluation."""

from __future__ import annotations

from typing import Any

from app.core.evaluation.evaluator import Evaluator


class EvaluationService:
    def __init__(self, evaluator: Evaluator) -> None:
        self.evaluator = evaluator

    def run(self) -> dict[str, Any]:
        return self.evaluator.run()

