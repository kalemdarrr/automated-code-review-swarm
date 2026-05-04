"""Risk score computation."""

from __future__ import annotations

from typing import Any


SEVERITY_WEIGHTS = {
    "info": 4,
    "low": 12,
    "medium": 26,
    "high": 44,
    "critical": 60,
}


def severity_weight(severity: str | None) -> int:
    return SEVERITY_WEIGHTS.get(str(severity or "low").strip().lower(), 12)


def risk_category(score: int) -> str:
    if score >= 85:
        return "CRITICAL"
    if score >= 65:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def compute_risk_score(
    security_findings: list[dict[str, Any]],
    clean_code_findings: list[dict[str, Any]],
    unsupported_claims: list[str],
    dangerous_commands: list[str],
    patch_risk: int = 0,
) -> int:
    score = 0
    for finding in security_findings:
        confidence = float(finding.get("confidence_score", 0.5) or 0.5)
        score += int(severity_weight(finding.get("severity")) * min(max(confidence, 0.0), 1.0))
    for finding in clean_code_findings:
        confidence = float(finding.get("confidence_score", 0.5) or 0.5)
        score += int(severity_weight(finding.get("severity")) * 0.2 * min(max(confidence, 0.0), 1.0))

    score += min(12, len(unsupported_claims) * 2)
    score += min(35, len(dangerous_commands) * 12)
    score += max(0, min(20, patch_risk))

    # Do not over-penalize clean-code-only reports without security risk.
    if not security_findings and not dangerous_commands:
        score = min(score, 28)

    return max(0, min(100, score))
