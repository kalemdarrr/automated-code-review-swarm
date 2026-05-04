"""Named workflow steps for the code review swarm."""

from __future__ import annotations


REVIEW_WORKFLOW_STEPS = [
    "receive_user_code",
    "retrieve_rag_context",
    "run_code_reviewer_agent",
    "run_security_auditor_agent",
    "monitor_agent_outputs",
    "synthesize_final_report",
    "monitor_final_report",
    "return_safe_report",
]

