"""RAG API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.schemas.review_schema import RAGIngestResponse, RAGStatusResponse
from app.dependencies import get_rag_service
from app.domain.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest", response_model=RAGIngestResponse)
def ingest(service: RAGService = Depends(get_rag_service)) -> RAGIngestResponse:
    summary = service.ingest()
    return RAGIngestResponse(
        indexed_documents=summary.indexed_documents,
        indexed_chunks=summary.indexed_chunks,
        categories=summary.categories,
    )


@router.get("/status", response_model=RAGStatusResponse)
def status(service: RAGService = Depends(get_rag_service)) -> RAGStatusResponse:
    return RAGStatusResponse(**service.status())

