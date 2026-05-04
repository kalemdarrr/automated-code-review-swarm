"""FastAPI entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.evaluation_routes import router as evaluation_router
from app.api.routes.health_routes import router as health_router
from app.api.routes.rag_routes import router as rag_router
from app.api.routes.review_routes import router as review_router
from app.config import get_settings
from app.utils.logging_utils import configure_logging

configure_logging()

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Local-first multi-agent code review and security audit system with RAG and monitoring.",
)

app.include_router(health_router)
app.include_router(review_router)
app.include_router(rag_router)
app.include_router(evaluation_router)

