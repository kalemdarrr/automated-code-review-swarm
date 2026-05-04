"""Mutable state passed through the review swarm."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentState:
    code: str
    language: str
    review_depth: str
    include_security: bool
    include_clean_code: bool
    include_rag_sources: bool
    rag_context: str = ""
    rag_sources: list[dict[str, Any]] = field(default_factory=list)
    rag_confidence: float = 0.0
    security_findings: list[dict[str, Any]] = field(default_factory=list)
    clean_code_findings: list[dict[str, Any]] = field(default_factory=list)
    risk_result: dict[str, Any] = field(default_factory=dict)
    final_report: str = ""
    agent_trace: list[dict[str, Any]] = field(default_factory=list)
    evaluation_notes: list[str] = field(default_factory=list)

