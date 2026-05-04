"""Extrinsic evaluation metrics."""

from __future__ import annotations


def vulnerability_detection_accuracy(detected: int, expected: int) -> float:
    return _safe_divide(detected, expected)


def false_positive_rate(false_positives: int, total_predictions: int) -> float:
    return _safe_divide(false_positives, total_predictions)


def false_negative_rate(missed: int, expected: int) -> float:
    return _safe_divide(missed, expected)


def rag_relevance_score(scores: list[float]) -> float:
    return _average(scores)


def average_confidence_score(scores: list[float]) -> float:
    return _average(scores)


def average_latency(latencies: list[float]) -> float:
    return _average(latencies)


def report_completeness_score(reports: list[str]) -> float:
    required_sections = [
        "Executive Summary",
        "Risk Score",
        "Security Findings",
        "Clean Code Findings",
        "Suggested Safe Patch",
        "RAG Sources",
        "Monitoring Summary",
        "Agent Trace",
    ]
    if not reports:
        return 0.0
    scores = []
    for report in reports:
        present = sum(1 for section in required_sections if section.lower() in report.lower())
        scores.append(present / len(required_sections))
    return _average(scores)


def _safe_divide(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)

