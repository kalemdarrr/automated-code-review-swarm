"""Multi-agent review swarm orchestration."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable

from app.core.agents.code_reviewer_agent import CodeReviewerAgent
from app.core.agents.rag_research_agent import RAGResearchAgent
from app.core.agents.risk_monitor_agent import RiskMonitorAgent
from app.core.agents.security_auditor_agent import SecurityAuditorAgent
from app.core.agents.senior_developer_agent import SeniorDeveloperAgent
from app.core.monitoring.audit_logger import AuditLogger
from app.core.orchestration.agent_state import AgentState
from app.domain.entities.agent_finding import AgentFinding
from app.domain.entities.code_review_result import CodeReviewResult
from app.domain.entities.risk_report import RiskReport
from app.domain.entities.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """Coordinates RAG, specialized agents, monitoring, and final synthesis."""

    def __init__(
        self,
        rag_agent: RAGResearchAgent,
        code_reviewer_agent: CodeReviewerAgent,
        security_auditor_agent: SecurityAuditorAgent,
        risk_monitor_agent: RiskMonitorAgent,
        senior_developer_agent: SeniorDeveloperAgent,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.rag_agent = rag_agent
        self.code_reviewer_agent = code_reviewer_agent
        self.security_auditor_agent = security_auditor_agent
        self.risk_monitor_agent = risk_monitor_agent
        self.senior_developer_agent = senior_developer_agent
        self.audit_logger = audit_logger or AuditLogger()

    def run_review(
        self,
        code: str,
        language: str = "python",
        review_depth: str = "standard",
        include_security: bool = True,
        include_clean_code: bool = True,
        include_rag_sources: bool = True,
    ) -> CodeReviewResult:
        state = AgentState(
            code=code,
            language=language,
            review_depth=review_depth,
            include_security=include_security,
            include_clean_code=include_clean_code,
            include_rag_sources=include_rag_sources,
        )
        self._log_event("review_started", state, {"submitted_language": language})

        self._run_rag(state)
        if include_clean_code:
            self._run_code_review(state)
        if include_security:
            self._run_security_audit(state)
        self._run_intermediate_monitor(state)
        self._run_senior_synthesis(state)
        self._run_final_monitor_and_refresh(state)

        result = self._to_result(state)
        self._log_event(
            "review_completed",
            state,
            {
                "risk_score": result.risk_report.risk_score,
                "retrieved_sources": [source.get("source") for source in state.rag_sources],
                "final_decision": result.risk_report.approved,
            },
        )
        return result

    def _run_rag(self, state: AgentState) -> None:
        top_k = 8 if state.review_depth == "deep" else 5

        def action() -> dict[str, Any]:
            return self.rag_agent.run(
                {
                    "code": state.code,
                    "language": state.language,
                    "review_objective": "security, clean code, SOLID, performance, and architecture review",
                    "top_k": top_k,
                }
            )

        result = self._step(state, self.rag_agent.name, action)
        if result:
            state.rag_context = str(result.get("retrieved_context", ""))
            state.rag_sources = list(result.get("sources", []))
            state.rag_confidence = float(result.get("confidence_score", 0.0) or 0.0)
        else:
            state.rag_context = "No RAG context was retrieved. Knowledge base confidence is low for this specific claim."
            state.rag_confidence = 0.0
            state.evaluation_notes.append("RAG retrieval failed; review continued with local agent analysis.")

    def _run_code_review(self, state: AgentState) -> None:
        result = self._step(
            state,
            self.code_reviewer_agent.name,
            lambda: self.code_reviewer_agent.run(
                {
                    "code": state.code,
                    "language": state.language,
                    "rag_context": state.rag_context,
                    "rag_sources": state.rag_sources,
                }
            ),
        )
        if result:
            state.clean_code_findings = list(result.get("findings", []))
            state.evaluation_notes.extend(str(warning) for warning in result.get("warnings", []))

    def _run_security_audit(self, state: AgentState) -> None:
        result = self._step(
            state,
            self.security_auditor_agent.name,
            lambda: self.security_auditor_agent.run(
                {
                    "code": state.code,
                    "language": state.language,
                    "rag_context": state.rag_context,
                    "rag_sources": state.rag_sources,
                }
            ),
        )
        if result:
            state.security_findings = list(result.get("findings", []))
            state.evaluation_notes.extend(str(warning) for warning in result.get("warnings", []))

    def _run_intermediate_monitor(self, state: AgentState) -> None:
        payload_text = json.dumps(
            {
                "security_findings": state.security_findings,
                "clean_code_findings": state.clean_code_findings,
            },
            ensure_ascii=True,
        )
        result = self._step(
            state,
            self.risk_monitor_agent.name,
            lambda: self.risk_monitor_agent.run(
                {
                    "text": payload_text,
                    "security_findings": state.security_findings,
                    "clean_code_findings": state.clean_code_findings,
                    "rag_sources": state.rag_sources,
                    "rag_confidence": state.rag_confidence,
                }
            ),
        )
        state.risk_result = result or self._default_risk()

    def _run_senior_synthesis(self, state: AgentState) -> None:
        result = self._step(
            state,
            self.senior_developer_agent.name,
            lambda: self.senior_developer_agent.run(
                {
                    "security_findings": state.security_findings,
                    "clean_code_findings": state.clean_code_findings,
                    "risk_report": state.risk_result,
                    "agent_trace": state.agent_trace,
                    "rag_sources": state.rag_sources if state.include_rag_sources else [],
                    "rag_confidence": state.rag_confidence,
                    "language": state.language,
                }
            ),
        )
        if result:
            state.final_report = str(result.get("final_report", ""))
            state.security_findings = list(result.get("security_findings", state.security_findings))
            state.clean_code_findings = list(result.get("clean_code_findings", state.clean_code_findings))

    def _run_final_monitor_and_refresh(self, state: AgentState) -> None:
        final_risk = self._step(
            state,
            f"{self.risk_monitor_agent.name}:final",
            lambda: self.risk_monitor_agent.run(
                {
                    "text": state.final_report,
                    "security_findings": state.security_findings,
                    "clean_code_findings": state.clean_code_findings,
                    "rag_sources": state.rag_sources,
                    "rag_confidence": state.rag_confidence,
                }
            ),
        )
        if final_risk:
            state.risk_result = final_risk

        refreshed = self.senior_developer_agent.run(
            {
                "security_findings": state.security_findings,
                "clean_code_findings": state.clean_code_findings,
                "risk_report": state.risk_result,
                "agent_trace": state.agent_trace,
                "rag_sources": state.rag_sources if state.include_rag_sources else [],
                "rag_confidence": state.rag_confidence,
                "language": state.language,
            }
        )
        state.final_report = str(refreshed.get("final_report", state.final_report))

    def _step(
        self,
        state: AgentState,
        agent_name: str,
        action: Callable[[], dict[str, Any]],
    ) -> dict[str, Any] | None:
        started = time.perf_counter()
        try:
            result = action()
            latency_ms = (time.perf_counter() - started) * 1000
            state.agent_trace.append(
                {
                    "agent": agent_name,
                    "status": "completed",
                    "message": "Step completed successfully.",
                    "latency_ms": round(latency_ms, 2),
                }
            )
            return result
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            logger.warning("%s failed: %s", agent_name, exc)
            state.agent_trace.append(
                {
                    "agent": agent_name,
                    "status": "failed",
                    "message": str(exc),
                    "latency_ms": round(latency_ms, 2),
                }
            )
            state.evaluation_notes.append(f"{agent_name} failed: {exc}")
            return None

    def _to_result(self, state: AgentState) -> CodeReviewResult:
        risk_report = RiskReport(
            approved=bool(state.risk_result.get("approved", True)),
            risk_score=int(state.risk_result.get("risk_score", 0)),
            risk_category=str(state.risk_result.get("risk_category", "LOW")),
            blocked_items=list(state.risk_result.get("blocked_items", [])),
            warnings=list(state.risk_result.get("warnings", [])),
            unsupported_claims=list(state.risk_result.get("unsupported_claims", [])),
            safer_alternative=state.risk_result.get("safer_alternative"),
            metadata=dict(state.risk_result.get("metadata", {})),
        )
        return CodeReviewResult(
            final_report=state.final_report,
            agent_trace=state.agent_trace,
            risk_report=risk_report,
            rag_sources=state.rag_sources if state.include_rag_sources else [],
            security_findings=[_vulnerability_from_dict(item) for item in state.security_findings],
            clean_code_findings=[_finding_from_dict(item) for item in state.clean_code_findings],
            evaluation_notes=state.evaluation_notes,
        )

    @staticmethod
    def _default_risk() -> dict[str, Any]:
        return {
            "approved": True,
            "risk_score": 0,
            "risk_category": "LOW",
            "blocked_items": [],
            "warnings": [],
            "unsupported_claims": [],
            "safer_alternative": None,
            "metadata": {},
        }

    def _log_event(self, event_name: str, state: AgentState, data: dict[str, Any]) -> None:
        self.audit_logger.log(
            {
                "event": event_name,
                "submitted_language": state.language,
                "agent_steps": state.agent_trace,
                "retrieved_sources": [source.get("source") for source in state.rag_sources],
                **data,
            }
        )


def _vulnerability_from_dict(item: dict[str, Any]) -> Vulnerability:
    return Vulnerability(
        vulnerability_name=str(item.get("vulnerability_name", "Potential vulnerability")),
        owasp_category=item.get("owasp_category"),
        severity=str(item.get("severity", "MEDIUM")).upper(),
        vulnerable_code=item.get("vulnerable_code"),
        explanation=str(item.get("explanation", "")),
        secure_fix=str(item.get("secure_fix", "Use safe APIs.")),
        confidence_score=float(item.get("confidence_score", 0.5) or 0.5),
        source_support=list(item.get("source_support", [])),
        metadata=dict(item.get("metadata", {})),
    )


def _finding_from_dict(item: dict[str, Any]) -> AgentFinding:
    return AgentFinding(
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
