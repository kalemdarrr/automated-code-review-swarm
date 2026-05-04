"""Agent schema objects for traces and health checks."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentTraceItem(BaseModel):
    agent: str
    status: str
    message: str
    latency_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    cuda_available: bool
    device: str
    model_path: str
    model_files_present: bool
    model_loaded: bool
    vector_db_available: bool
    indexed_documents: int
