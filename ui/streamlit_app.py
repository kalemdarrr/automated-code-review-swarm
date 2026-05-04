"""Streamlit UI for the Automated Code Review & Security Swarm."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEMO_CODE = """import os
import sqlite3

DB_PASSWORD = "prod-password-123"

def handle_request(conn, user_id, expr, filename):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    user = conn.execute(query).fetchone()
    result = eval(expr)
    data = open("/srv/app/uploads/" + filename).read()
    if user:
        print("user found")
    return {"user": user, "result": result, "data": data}
"""


def main() -> None:
    st.set_page_config(page_title="Automated Code Review & Security Swarm", layout="wide")
    st.title("Automated Code Review & Security Swarm")
    st.caption("Local Transformer inference, RAG, specialized agents, monitoring, and evaluation.")

    with st.sidebar:
        st.header("Review Settings")
        language = st.selectbox("Language", ["python", "javascript", "typescript", "java", "csharp", "go"], index=0)
        review_depth = st.selectbox("Review depth", ["standard", "deep"], index=0)
        include_security = st.checkbox("Include security audit", value=True)
        include_clean_code = st.checkbox("Include clean code review", value=True)
        include_rag_sources = st.checkbox("Include RAG sources", value=True)
        backend_url = st.text_input("FastAPI backend URL", os.getenv("BACKEND_URL", "http://localhost:8000"))

    uploaded_file = st.file_uploader("Upload a source file", type=["py", "js", "ts", "java", "cs", "go", "txt"])
    initial_code = DEMO_CODE
    if uploaded_file is not None:
        initial_code = uploaded_file.read().decode("utf-8", errors="ignore")

    code = st.text_area("Source code", value=initial_code, height=360)
    analyze = st.button("Analyze Code", type="primary")

    if analyze:
        with st.spinner("Running multi-agent review locally..."):
            payload = {
                "code": code,
                "language": language,
                "review_depth": review_depth,
                "include_security": include_security,
                "include_clean_code": include_clean_code,
                "include_rag_sources": include_rag_sources,
            }
            result = _run_review(payload, backend_url)

        st.subheader("Risk Score")
        st.metric("Risk", f"{result.get('risk_score', 0)}/100")

        tabs = st.tabs(["Final Report", "Security Findings", "Clean Code Findings", "RAG Sources", "Agent Trace"])
        with tabs[0]:
            st.markdown(result.get("final_report", "No report generated."))
        with tabs[1]:
            st.dataframe(result.get("security_findings", []), use_container_width=True)
        with tabs[2]:
            st.dataframe(result.get("clean_code_findings", []), use_container_width=True)
        with tabs[3]:
            for source in result.get("rag_sources", []):
                st.markdown(
                    f"**{source.get('source', 'unknown')}** · {source.get('category', 'general')} · "
                    f"{source.get('relevance_score', 0)}"
                )
                st.write(source.get("snippet", ""))
        with tabs[4]:
            st.json(result.get("agent_trace", []))

        notes = result.get("evaluation_notes", [])
        if notes:
            st.info("\n".join(str(note) for note in notes))


def _run_review(payload: dict[str, Any], backend_url: str) -> dict[str, Any]:
    try:
        response = requests.post(f"{backend_url.rstrip('/')}/review", json=payload, timeout=240)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        st.warning(f"Backend call failed, using direct local service layer: {exc}")
        from app.dependencies import get_review_service

        result = get_review_service().review_code(**payload)
        data = result.as_dict()
        return {
            "final_report": data["final_report"],
            "agent_trace": data["agent_trace"],
            "risk_score": data["risk_score"],
            "rag_sources": data["rag_sources"],
            "evaluation_notes": data["evaluation_notes"],
            "security_findings": data["security_findings"],
            "clean_code_findings": data["clean_code_findings"],
        }


if __name__ == "__main__":
    main()
