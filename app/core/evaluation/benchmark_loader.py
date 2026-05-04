"""Benchmark loading utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.evaluation.test_cases import BenchmarkCase, built_in_cases


class BenchmarkLoader:
    def __init__(self, benchmark_path: Path | None = None) -> None:
        self.benchmark_path = benchmark_path

    def load(self) -> list[BenchmarkCase]:
        if self.benchmark_path is None or not self.benchmark_path.exists():
            return built_in_cases()
        raw_cases = json.loads(self.benchmark_path.read_text(encoding="utf-8"))
        return [self._from_dict(item) for item in raw_cases]

    @staticmethod
    def _from_dict(item: dict[str, Any]) -> BenchmarkCase:
        return BenchmarkCase(
            case_id=str(item["case_id"]),
            language=str(item.get("language", "python")),
            code=str(item["code"]),
            expected_vulnerability=item.get("expected_vulnerability"),
            expected_severity=str(item.get("expected_severity", "MEDIUM")),
            expected_clean_code_issue=item.get("expected_clean_code_issue"),
        )

