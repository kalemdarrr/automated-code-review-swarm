"""Final code review result entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.entities.agent_finding import AgentFinding
from app.domain.entities.risk_report import RiskReport
from app.domain.entities.vulnerability import Vulnerability


@dataclass(slots=True)
class CodeReviewResult:
    final_report: str
    agent_trace: list[dict[str, Any]]
    risk_report: RiskReport
    rag_sources: list[dict[str, Any]] = field(default_factory=list)
    security_findings: list[Vulnerability] = field(default_factory=list)
    clean_code_findings: list[AgentFinding] = field(default_factory=list)
    evaluation_notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "final_report": self.final_report,
            "agent_trace": self.agent_trace,
            "risk_score": self.risk_report.risk_score,
            "risk_report": self.risk_report.as_dict(),
            "rag_sources": self.rag_sources,
            "security_findings": [finding.as_dict() for finding in self.security_findings],
            "clean_code_findings": [finding.as_dict() for finding in self.clean_code_findings],
            "evaluation_notes": self.evaluation_notes,
        }

