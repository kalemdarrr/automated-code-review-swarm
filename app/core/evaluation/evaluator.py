"""End-to-end benchmark evaluator."""

from __future__ import annotations

import time
from typing import Any

from app.core.evaluation.benchmark_loader import BenchmarkLoader
from app.core.evaluation.metrics import (
    average_confidence_score,
    average_latency,
    false_negative_rate,
    false_positive_rate,
    rag_relevance_score,
    report_completeness_score,
    vulnerability_detection_accuracy,
)
from app.domain.services.review_service import ReviewService


class Evaluator:
    """Runs extrinsic task evaluation against benchmark snippets."""

    def __init__(self, review_service: ReviewService, benchmark_loader: BenchmarkLoader | None = None) -> None:
        self.review_service = review_service
        self.benchmark_loader = benchmark_loader or BenchmarkLoader()

    def run(self) -> dict[str, Any]:
        cases = self.benchmark_loader.load()
        detected = 0
        missed = 0
        expected_vulnerabilities = 0
        false_positives = 0
        total_security_predictions = 0
        rag_scores: list[float] = []
        confidences: list[float] = []
        latencies: list[float] = []
        reports: list[str] = []

        for case in cases:
            started = time.perf_counter()
            result = self.review_service.review_code(
                code=case.code,
                language=case.language,
                review_depth="standard",
                include_security=True,
                include_clean_code=True,
                include_rag_sources=True,
            )
            latencies.append(time.perf_counter() - started)
            reports.append(result.final_report)
            rag_scores.extend(float(source.get("relevance_score", 0.0) or 0.0) for source in result.rag_sources)
            confidences.extend(finding.confidence_score for finding in result.security_findings)
            confidences.extend(finding.confidence_score for finding in result.clean_code_findings)

            prediction_text = " ".join(
                [
                    finding.vulnerability_name + " " + finding.explanation
                    for finding in result.security_findings
                ]
            ).lower()
            total_security_predictions += len(result.security_findings)

            if case.expected_vulnerability:
                expected_vulnerabilities += 1
                if _matches(case.expected_vulnerability, prediction_text):
                    detected += 1
                    false_positives += max(0, len(result.security_findings) - 1)
                else:
                    missed += 1
                    false_positives += len(result.security_findings)
            else:
                false_positives += len(result.security_findings)

        accuracy = vulnerability_detection_accuracy(detected, expected_vulnerabilities)
        fp_rate = false_positive_rate(false_positives, max(total_security_predictions, 1))
        fn_rate = false_negative_rate(missed, expected_vulnerabilities)
        completeness = report_completeness_score(reports)
        relevance = rag_relevance_score(rag_scores)
        confidence = average_confidence_score(confidences)
        latency_avg = average_latency(latencies)
        final_score = round((accuracy * 0.42 + (1 - fp_rate) * 0.18 + (1 - fn_rate) * 0.18 + completeness * 0.14 + relevance * 0.08) * 100, 2)

        return {
            "total_examples": len(cases),
            "detected_vulnerabilities": detected,
            "missed_vulnerabilities": missed,
            "false_positives": false_positives,
            "rag_relevance_average": relevance,
            "latency_average": latency_avg,
            "final_score": final_score,
            "metrics": {
                "vulnerability_detection_accuracy": accuracy,
                "false_positive_rate": fp_rate,
                "false_negative_rate": fn_rate,
                "rag_relevance_score": relevance,
                "average_confidence_score": confidence,
                "average_latency": latency_avg,
                "report_completeness_score": completeness,
                "intrinsic_perplexity": "optional_placeholder_not_required_for_main_extrinsic_evaluation",
            },
        }


def _matches(expected: str, prediction_text: str) -> bool:
    aliases = {
        "hardcoded password": ["hardcoded secret", "password"],
        "hardcoded secret": ["hardcoded secret", "password", "secret"],
        "sql injection": ["sql injection", "injection"],
        "unsafe eval": ["unsafe eval", "eval"],
        "path traversal": ["path traversal"],
        "insecure subprocess": ["insecure subprocess", "subprocess", "shell execution"],
    }
    expected_lower = expected.lower()
    candidates = aliases.get(expected_lower, [expected_lower])
    return any(candidate in prediction_text for candidate in candidates)

