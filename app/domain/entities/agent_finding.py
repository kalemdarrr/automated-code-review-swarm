"""Shared finding entities produced by review agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentFinding:
    title: str
    severity: str
    explanation: str
    suggested_fix: str
    confidence_score: float
    agent_name: str
    evidence: str | None = None
    source_support: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "severity": self.severity,
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
            "confidence_score": self.confidence_score,
            "agent_name": self.agent_name,
            "evidence": self.evidence,
            "source_support": self.source_support,
            "metadata": self.metadata,
        }

