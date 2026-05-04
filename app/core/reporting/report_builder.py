"""Final Markdown report builder."""

from __future__ import annotations

from typing import Any

from app.core.reporting.markdown_formatter import bullet_list, confidence, fenced_code
from app.domain.entities.agent_finding import AgentFinding
from app.domain.entities.risk_report import RiskReport
from app.domain.entities.vulnerability import Vulnerability


class ReportBuilder:
    """Builds report-ready Markdown output from structured agent results."""

    def build(
        self,
        language: str,
        security_findings: list[Vulnerability],
        clean_code_findings: list[AgentFinding],
        rag_sources: list[dict[str, Any]],
        monitoring_summary: RiskReport,
        agent_trace: list[dict[str, Any]],
        rag_confidence: float,
    ) -> str:
        return "\n\n".join(
            [
                "# Automated Code Review & Security Report",
                self._executive_summary(security_findings, clean_code_findings, monitoring_summary, rag_confidence),
                self._risk_score(monitoring_summary),
                self._security_findings(security_findings, language),
                self._clean_code_findings(clean_code_findings),
                self._safe_patch(security_findings, clean_code_findings, language),
                self._rag_sources(rag_sources),
                self._monitoring_summary(monitoring_summary),
                self._agent_trace(agent_trace),
            ]
        )

    def _executive_summary(
        self,
        security_findings: list[Vulnerability],
        clean_code_findings: list[AgentFinding],
        risk_report: RiskReport,
        rag_confidence: float,
    ) -> str:
        security_count = len(security_findings)
        clean_count = len(clean_code_findings)
        confidence_note = (
            "Knowledge base confidence is low for this specific claim."
            if rag_confidence < 0.32
            else "RAG support was available for the review context."
        )
        return (
            "## 1. Executive Summary\n"
            f"The swarm identified {security_count} security finding(s) and {clean_count} clean-code finding(s). "
            f"Overall monitored risk is {risk_report.risk_category} ({risk_report.risk_score}/100). "
            f"{confidence_note}"
        )

    @staticmethod
    def _risk_score(risk_report: RiskReport) -> str:
        return f"## 2. Risk Score\nScore: **{risk_report.risk_score}/100**\n\nCategory: **{risk_report.risk_category}**"

    @staticmethod
    def _security_findings(findings: list[Vulnerability], language: str) -> str:
        if not findings:
            return "## 3. Security Findings\nNo security vulnerabilities were detected with the current evidence."
        sections = ["## 3. Security Findings"]
        for index, finding in enumerate(findings, start=1):
            source_support = bullet_list(finding.source_support, "Knowledge base confidence is low for this specific claim.")
            sections.append(
                "\n".join(
                    [
                        f"### 3.{index} {finding.vulnerability_name}",
                        f"- Severity: {finding.severity}",
                        f"- OWASP category: {finding.owasp_category or 'Not mapped'}",
                        "- Problematic code:",
                        fenced_code(finding.vulnerable_code, language),
                        f"- Explanation: {finding.explanation}",
                        f"- Secure fix: {finding.secure_fix}",
                        f"- Confidence score: {confidence(finding.confidence_score)}",
                        "- RAG source support:",
                        source_support,
                    ]
                )
            )
        return "\n\n".join(sections)

    @staticmethod
    def _clean_code_findings(findings: list[AgentFinding]) -> str:
        if not findings:
            return "## 4. Clean Code Findings\nNo major clean-code issues were detected with the current evidence."
        sections = ["## 4. Clean Code Findings"]
        for index, finding in enumerate(findings, start=1):
            sections.append(
                "\n".join(
                    [
                        f"### 4.{index} {finding.title}",
                        f"- Severity: {finding.severity}",
                        f"- Problem: {finding.explanation}",
                        f"- Why it matters: {finding.metadata.get('why_it_matters', finding.explanation)}",
                        f"- Suggested refactor: {finding.suggested_fix}",
                        f"- Confidence score: {confidence(finding.confidence_score)}",
                    ]
                )
            )
        return "\n\n".join(sections)

    @staticmethod
    def _safe_patch(
        security_findings: list[Vulnerability],
        clean_code_findings: list[AgentFinding],
        language: str,
    ) -> str:
        suggestions = [finding.secure_fix for finding in security_findings]
        suggestions.extend(finding.suggested_fix for finding in clean_code_findings)
        if not suggestions:
            return "## 5. Suggested Safe Patch\nNo patch is required based on the current findings."
        lines = [
            "## 5. Suggested Safe Patch",
            "Review these suggestions manually before applying them. Patches may change behavior if validation, query construction, or error handling is modified.",
        ]
        for index, suggestion in enumerate(suggestions, start=1):
            lines.append(f"{index}. {suggestion}")
        lines.append(fenced_code("# Apply targeted code edits after tests pass. Do not execute submitted code.", language))
        return "\n".join(lines)

    @staticmethod
    def _rag_sources(sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "## 6. RAG Sources\nNo sources were retrieved. Knowledge base confidence is low for this specific claim."
        lines = ["## 6. RAG Sources"]
        for index, source in enumerate(sources, start=1):
            lines.extend(
                [
                    f"### Source {index}",
                    f"- Source name: {source.get('source', 'unknown')}",
                    f"- Category: {source.get('category', 'general')}",
                    f"- Relevance score: {source.get('relevance_score', 0)}",
                    f"- Short snippet: {source.get('snippet', '')}",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def _monitoring_summary(risk_report: RiskReport) -> str:
        return "\n".join(
            [
                "## 7. Monitoring Summary",
                "- Blocked outputs:",
                _indented_list(risk_report.blocked_items),
                "- Unsupported claims:",
                _indented_list(risk_report.unsupported_claims),
                "- Dangerous suggestions detected:",
                _indented_list(risk_report.warnings),
                f"- Final approval status: {risk_report.approved}",
            ]
        )

    @staticmethod
    def _agent_trace(trace: list[dict[str, Any]]) -> str:
        if not trace:
            return "## 8. Agent Trace\nNo agent trace was recorded."
        lines = ["## 8. Agent Trace"]
        for item in trace:
            latency = item.get("latency_ms")
            latency_text = f" ({latency:.1f} ms)" if isinstance(latency, (int, float)) else ""
            lines.append(f"- {item.get('agent', 'unknown')}: {item.get('status', 'unknown')}{latency_text} - {item.get('message', '')}")
        return "\n".join(lines)


def _indented_list(items: list[str]) -> str:
    if not items:
        return "  - None reported."
    return "\n".join(f"  - {item}" for item in items)
