from __future__ import annotations

from app.core.agents.code_reviewer_agent import CodeReviewerAgent
from app.core.agents.security_auditor_agent import SecurityAuditorAgent


def test_security_auditor_detects_common_vulnerabilities() -> None:
    code = """
password = "secret123"
def run(conn, user_id, expr):
    conn.execute(f"SELECT * FROM users WHERE id={user_id}")
    return eval(expr)
"""
    result = SecurityAuditorAgent().run({"code": code, "language": "python", "rag_sources": []})
    names = {finding["vulnerability_name"] for finding in result["findings"]}

    assert "Hardcoded secret" in names
    assert "SQL injection risk" in names
    assert "Unsafe eval execution" in names


def test_code_reviewer_detects_bare_exception_and_validation_gap() -> None:
    code = """
def parse_and_open(filename):
    try:
        return open(filename).read()
    except:
        return None
"""
    result = CodeReviewerAgent().run({"code": code, "language": "python", "rag_sources": []})
    titles = {finding["title"] for finding in result["findings"]}

    assert "Bare exception handler" in titles
    assert "Missing input validation" in titles


def test_security_auditor_does_not_flag_safe_read_text_helper_as_path_traversal() -> None:
    code = """
from pathlib import Path

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")
"""
    result = SecurityAuditorAgent().run({"code": code, "language": "python", "rag_sources": []})
    names = {finding["vulnerability_name"] for finding in result["findings"]}

    assert "Path traversal risk" not in names
