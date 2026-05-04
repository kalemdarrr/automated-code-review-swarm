from __future__ import annotations

from app.core.agents.code_reviewer_agent import CodeReviewerAgent
from app.core.agents.rag_research_agent import RAGResearchAgent
from app.core.agents.risk_monitor_agent import RiskMonitorAgent
from app.core.agents.security_auditor_agent import SecurityAuditorAgent
from app.core.agents.senior_developer_agent import SeniorDeveloperAgent
from app.core.orchestration.swarm_orchestrator import SwarmOrchestrator
from app.core.rag.rag_pipeline import RAGResult


class FakeRAGPipeline:
    def run(self, user_code: str, review_objective: str, language: str, top_k: int | None = None, category=None):
        return RAGResult(
            retrieved_context="[Source 1] OWASP says use parameterized SQL.",
            sources=[
                {
                    "source": "owasp.md",
                    "category": "owasp",
                    "relevance_score": 0.9,
                    "snippet": "SQL injection requires parameterized queries.",
                }
            ],
            confidence_score=0.9,
            low_confidence=False,
        )


class FakeAuditLogger:
    def log(self, event):
        self.last_event = event


def test_swarm_orchestrator_returns_final_report() -> None:
    orchestrator = SwarmOrchestrator(
        rag_agent=RAGResearchAgent(rag_pipeline=FakeRAGPipeline()),
        code_reviewer_agent=CodeReviewerAgent(),
        security_auditor_agent=SecurityAuditorAgent(),
        risk_monitor_agent=RiskMonitorAgent(),
        senior_developer_agent=SeniorDeveloperAgent(),
        audit_logger=FakeAuditLogger(),
    )

    result = orchestrator.run_review(
        code='password = "secret123"\nconn.execute(f"SELECT * FROM users WHERE id={user_id}")',
        language="python",
    )

    assert "Automated Code Review & Security Report" in result.final_report
    assert result.security_findings
    assert any(item["agent"] == "SecurityAuditorAgent" for item in result.agent_trace)
