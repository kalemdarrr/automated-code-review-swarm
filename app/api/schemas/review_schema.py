"""Review request and response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Source code to analyze as text only.")
    language: str = Field(default="python", min_length=1)
    review_depth: Literal["standard", "deep"] = "standard"
    include_security: bool = True
    include_clean_code: bool = True
    include_rag_sources: bool = True


class ReviewResponse(BaseModel):
    final_report: str
    agent_trace: list[dict[str, Any]]
    risk_score: int = Field(..., ge=0, le=100)
    rag_sources: list[dict[str, Any]]
    evaluation_notes: list[str]
    security_findings: list[dict[str, Any]] = Field(default_factory=list)
    clean_code_findings: list[dict[str, Any]] = Field(default_factory=list)


class RAGIngestResponse(BaseModel):
    indexed_documents: int
    indexed_chunks: int
    categories: list[str]


class RAGStatusResponse(BaseModel):
    vector_db_available: bool
    indexed_documents: int
    categories: list[str]
    collection_name: str

