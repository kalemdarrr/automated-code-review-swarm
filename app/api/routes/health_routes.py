"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.schemas.agent_schema import HealthResponse
from app.core.llm.local_model_loader import LocalModelLoader, get_torch_device_summary
from app.core.rag.vector_store import ChromaVectorStore
from app.dependencies import get_model_loader, get_vector_store

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    model_loader: LocalModelLoader = Depends(get_model_loader),
    vector_store: ChromaVectorStore = Depends(get_vector_store),
) -> HealthResponse:
    cuda_available, device = get_torch_device_summary()
    return HealthResponse(
        status="ok",
        cuda_available=cuda_available,
        device=device,
        model_path=str(model_loader.settings.local_model_path),
        model_files_present=model_loader.model_files_present(),
        model_loaded=model_loader.is_loaded,
        vector_db_available=vector_store.available,
        indexed_documents=vector_store.count(),
    )

