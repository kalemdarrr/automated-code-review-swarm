"""Final output safety guard."""

from __future__ import annotations

from typing import Any

from app.core.monitoring.command_safety_filter import CommandSafetyFilter
from app.core.monitoring.hallucination_checker import HallucinationChecker
from app.core.monitoring.risk_score import compute_risk_score, risk_category
from app.domain.entities.risk_report import RiskReport


class OutputGuard:
    """Validates agent outputs and final reports before returning them."""

    def __init__(
        self,
        command_filter: CommandSafetyFilter | None = None,
        hallucination_checker: HallucinationChecker | None = None,
    ) -> None:
        self.command_filter = command_filter or CommandSafetyFilter()
        self.hallucination_checker = hallucination_checker or HallucinationChecker()

    def validate(
        self,
        text: str,
        security_findings: list[dict[str, Any]],
        clean_code_findings: list[dict[str, Any]],
        rag_sources: list[dict[str, Any]],
        rag_confidence: float,
    ) -> RiskReport:
        command_result = self.command_filter.scan(text)
        hallucination_result = self.hallucination_checker.check_findings(
            findings=[*security_findings, *clean_code_findings],
            rag_sources=rag_sources,
            rag_confidence=rag_confidence,
        )
        security_hallucination_result = self.hallucination_checker.check_findings(
            findings=security_findings,
            rag_sources=rag_sources,
            rag_confidence=rag_confidence,
        )
        score = compute_risk_score(
            security_findings=security_findings,
            clean_code_findings=clean_code_findings,
            unsupported_claims=security_hallucination_result.unsupported_claims,
            dangerous_commands=command_result.dangerous_commands,
        )
        approved = score < 85 and command_result.safe
        safer_alternative = None
        if command_result.dangerous_commands:
            safer_alternative = (
                "Review the proposed patch manually, create backups, and replace destructive shell commands "
                "with scoped, reversible changes."
            )
        return RiskReport(
            approved=approved,
            risk_score=score,
            risk_category=risk_category(score),
            blocked_items=command_result.dangerous_commands,
            warnings=command_result.warnings,
            unsupported_claims=hallucination_result.unsupported_claims,
            safer_alternative=safer_alternative,
            metadata={"rag_adjusted_confidence": hallucination_result.adjusted_confidence},
        )
