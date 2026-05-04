from __future__ import annotations

from app.core.evaluation.metrics import (
    average_confidence_score,
    false_negative_rate,
    false_positive_rate,
    report_completeness_score,
    vulnerability_detection_accuracy,
)


def test_evaluation_metrics() -> None:
    assert vulnerability_detection_accuracy(8, 10) == 0.8
    assert false_positive_rate(2, 10) == 0.2
    assert false_negative_rate(1, 10) == 0.1
    assert average_confidence_score([0.5, 1.0]) == 0.75


def test_report_completeness_score_detects_required_sections() -> None:
    report = """
# Automated Code Review & Security Report
## 1. Executive Summary
## 2. Risk Score
## 3. Security Findings
## 4. Clean Code Findings
## 5. Suggested Safe Patch
## 6. RAG Sources
## 7. Monitoring Summary
## 8. Agent Trace
"""
    assert report_completeness_score([report]) == 1.0

