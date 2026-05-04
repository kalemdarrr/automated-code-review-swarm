"""Risk monitor agent."""

from __future__ import annotations

from typing import Any

from app.core.agents.base_agent import BaseAgent
from app.core.monitoring.output_guard import OutputGuard


class RiskMonitorAgent(BaseAgent):
    def __init__(self, output_guard: OutputGuard | None = None, **kwargs: Any) -> None:
        super().__init__(
            name="RiskMonitorAgent",
            role="Validate agent outputs, unsupported claims, and dangerous suggestions.",
            system_prompt="Monitor outputs for hallucination, unsafe remediation, and risk.",
            **kwargs,
        )
        self.output_guard = output_guard or OutputGuard()

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        risk_report = self.output_guard.validate(
            text=str(input_data.get("text", "")),
            security_findings=input_data.get("security_findings", []),
            clean_code_findings=input_data.get("clean_code_findings", []),
            rag_sources=input_data.get("rag_sources", []),
            rag_confidence=float(input_data.get("rag_confidence", 0.0) or 0.0),
        )
        return risk_report.as_dict()

