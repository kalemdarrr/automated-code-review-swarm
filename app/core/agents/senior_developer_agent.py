"""Senior developer synthesis agent."""

from __future__ import annotations

from typing import Any

from app.core.agents.base_agent import BaseAgent
from app.core.reporting.report_builder import ReportBuilder
from app.domain.entities.agent_finding import AgentFinding
from app.domain.entities.risk_report import RiskReport
from app.domain.entities.vulnerability import Vulnerability


class SeniorDeveloperAgent(BaseAgent):
    def __init__(self, report_builder: ReportBuilder | None = None, **kwargs: Any) -> None:
        super().__init__(
            name="SeniorDeveloperAgent",
            role="Deduplicate, prioritize, and produce the final professional report.",
            system_prompt=(
                "You are a principal engineer creating a concise professional code review and security report. "
                "Preserve citations and monitoring warnings."
            ),
            **kwargs,
        )
        self.report_builder = report_builder or ReportBuilder()

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        security_findings = self._parse_security(input_data.get("security_findings", []))
        clean_code_findings = self._parse_clean_code(input_data.get("clean_code_findings", []))
        risk_report = self._parse_risk(input_data.get("risk_report", {}))
        agent_trace = input_data.get("agent_trace", [])
        rag_sources = input_data.get("rag_sources", [])
        language = str(input_data.get("language", "python"))
        rag_confidence = float(input_data.get("rag_confidence", 0.0) or 0.0)

        security_findings = self._dedupe_security(security_findings)
        clean_code_findings = self._dedupe_clean(clean_code_findings)
        report = self.report_builder.build(
            language=language,
            security_findings=security_findings,
            clean_code_findings=clean_code_findings,
            rag_sources=rag_sources,
            monitoring_summary=risk_report,
            agent_trace=agent_trace,
            rag_confidence=rag_confidence,
        )
        return {
            "executive_summary": "Final report generated with prioritized security and clean-code findings.",
            "prioritized_findings": [finding.as_dict() for finding in [*security_findings, *clean_code_findings]],
            "security_findings": [finding.as_dict() for finding in security_findings],
            "clean_code_findings": [finding.as_dict() for finding in clean_code_findings],
            "suggested_refactorings": [finding.suggested_fix for finding in clean_code_findings],
            "safe_patch_suggestions": [finding.secure_fix for finding in security_findings],
            "rag_sources": rag_sources,
            "monitoring_summary": risk_report.as_dict(),
            "final_score": max(0, 100 - risk_report.risk_score),
            "final_report": report,
        }

    @staticmethod
    def _parse_security(items: list[dict[str, Any]]) -> list[Vulnerability]:
        return [
            Vulnerability(
                vulnerability_name=str(item.get("vulnerability_name", "Potential vulnerability")),
                owasp_category=item.get("owasp_category"),
                severity=str(item.get("severity", "MEDIUM")).upper(),
                vulnerable_code=item.get("vulnerable_code"),
                explanation=str(item.get("explanation", "")),
                secure_fix=str(item.get("secure_fix", "Use safe, validated APIs.")),
                confidence_score=float(item.get("confidence_score", 0.5) or 0.5),
                source_support=list(item.get("source_support", [])),
                metadata=dict(item.get("metadata", {})),
            )
            for item in items
        ]

    @staticmethod
    def _parse_clean_code(items: list[dict[str, Any]]) -> list[AgentFinding]:
        return [
            AgentFinding(
                title=str(item.get("title", "Maintainability issue")),
                severity=str(item.get("severity", "MEDIUM")).upper(),
                explanation=str(item.get("explanation", "")),
                suggested_fix=str(item.get("suggested_fix", "Refactor into smaller units.")),
                confidence_score=float(item.get("confidence_score", 0.5) or 0.5),
                agent_name=str(item.get("agent_name", "CodeReviewerAgent")),
                evidence=item.get("evidence"),
                source_support=list(item.get("source_support", [])),
                metadata=dict(item.get("metadata", {})),
            )
            for item in items
        ]

    @staticmethod
    def _parse_risk(payload: dict[str, Any]) -> RiskReport:
        return RiskReport(
            approved=bool(payload.get("approved", True)),
            risk_score=int(payload.get("risk_score", 0)),
            risk_category=str(payload.get("risk_category", "LOW")),
            blocked_items=list(payload.get("blocked_items", [])),
            warnings=list(payload.get("warnings", [])),
            unsupported_claims=list(payload.get("unsupported_claims", [])),
            safer_alternative=payload.get("safer_alternative"),
            metadata=dict(payload.get("metadata", {})),
        )

    @staticmethod
    def _dedupe_security(findings: list[Vulnerability]) -> list[Vulnerability]:
        deduped: dict[str, Vulnerability] = {}
        for finding in findings:
            key = f"{finding.vulnerability_name.lower()}::{finding.vulnerable_code or ''}"
            existing = deduped.get(key)
            if existing is None or finding.confidence_score > existing.confidence_score:
                deduped[key] = finding
        return sorted(deduped.values(), key=lambda item: _severity_rank(item.severity), reverse=True)

    @staticmethod
    def _dedupe_clean(findings: list[AgentFinding]) -> list[AgentFinding]:
        deduped: dict[str, AgentFinding] = {}
        for finding in findings:
            existing = deduped.get(finding.title.lower())
            if existing is None or finding.confidence_score > existing.confidence_score:
                deduped[finding.title.lower()] = finding
        return sorted(deduped.values(), key=lambda item: _severity_rank(item.severity), reverse=True)


def _severity_rank(severity: str) -> int:
    return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}.get(severity.upper(), 1)

