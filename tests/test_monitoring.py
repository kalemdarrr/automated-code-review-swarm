from __future__ import annotations

from app.core.monitoring.command_safety_filter import CommandSafetyFilter
from app.core.monitoring.output_guard import OutputGuard


def test_command_safety_filter_blocks_destructive_commands() -> None:
    result = CommandSafetyFilter().scan("Run rm -rf /tmp/app and then chmod 777 secrets")

    assert result.safe is False
    assert len(result.dangerous_commands) == 2


def test_output_guard_marks_unsupported_claims_without_rag_sources() -> None:
    risk = OutputGuard().validate(
        text="SQL injection finding",
        security_findings=[
            {
                "vulnerability_name": "SQL injection",
                "severity": "HIGH",
                "explanation": "string interpolation",
                "confidence_score": 0.9,
            }
        ],
        clean_code_findings=[],
        rag_sources=[],
        rag_confidence=0.0,
    )

    assert risk.unsupported_claims
    assert risk.risk_score > 0


def test_output_guard_caps_clean_code_only_risk() -> None:
    risk = OutputGuard().validate(
        text="clean code style findings",
        security_findings=[],
        clean_code_findings=[
            {
                "title": "Long function",
                "severity": "MEDIUM",
                "explanation": "Function is long",
                "confidence_score": 0.9,
            },
            {
                "title": "Duplicated code",
                "severity": "LOW",
                "explanation": "Repeated statements",
                "confidence_score": 0.8,
            },
        ],
        rag_sources=[],
        rag_confidence=0.0,
    )

    assert risk.risk_score <= 28
