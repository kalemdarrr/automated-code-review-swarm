"""Dependency construction for API routes and scripts."""

from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.core.agents.code_reviewer_agent import CodeReviewerAgent
from app.core.agents.rag_research_agent import RAGResearchAgent
from app.core.agents.risk_monitor_agent import RiskMonitorAgent
from app.core.agents.security_auditor_agent import SecurityAuditorAgent
from app.core.agents.senior_developer_agent import SeniorDeveloperAgent
from app.core.evaluation.evaluator import Evaluator
from app.core.llm.local_llm_client import LocalLLMClient
from app.core.llm.local_model_loader import LocalModelLoader
from app.core.monitoring.audit_logger import AuditLogger
from app.core.monitoring.output_guard import OutputGuard
from app.core.orchestration.swarm_orchestrator import SwarmOrchestrator
from app.core.rag.embedding_model import EmbeddingModel, build_embedding_model
from app.core.rag.rag_pipeline import RAGPipeline
from app.core.rag.retriever import Retriever
from app.core.rag.vector_store import ChromaVectorStore
from app.domain.services.evaluation_service import EvaluationService
from app.domain.services.rag_service import RAGService
from app.domain.services.review_service import ReviewService


@lru_cache(maxsize=1)
def get_model_loader() -> LocalModelLoader:
    return LocalModelLoader(get_settings())


@lru_cache(maxsize=1)
def get_llm_client() -> LocalLLMClient:
    return LocalLLMClient(loader=get_model_loader(), settings=get_settings())


@lru_cache(maxsize=1)
def get_embedding() -> EmbeddingModel:
    settings = get_settings()
    return build_embedding_model(settings.local_embedding_model_path)


@lru_cache(maxsize=1)
def get_vector_store() -> ChromaVectorStore:
    settings = get_settings()
    return ChromaVectorStore(
        persist_path=settings.chroma_db_path,
        collection_name=settings.chroma_collection_name,
        embedding_model=get_embedding(),
    )


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline(Retriever(get_vector_store()), settings=get_settings())


@lru_cache(maxsize=1)
def get_orchestrator() -> SwarmOrchestrator:
    settings = get_settings()
    llm_client = get_llm_client()
    rag_agent = RAGResearchAgent(rag_pipeline=get_rag_pipeline(), settings=settings)
    return SwarmOrchestrator(
        rag_agent=rag_agent,
        code_reviewer_agent=CodeReviewerAgent(llm_client=llm_client, settings=settings),
        security_auditor_agent=SecurityAuditorAgent(llm_client=llm_client, settings=settings),
        risk_monitor_agent=RiskMonitorAgent(output_guard=OutputGuard(), settings=settings),
        senior_developer_agent=SeniorDeveloperAgent(llm_client=llm_client, settings=settings),
        audit_logger=AuditLogger(settings),
    )


@lru_cache(maxsize=1)
def get_review_service() -> ReviewService:
    return ReviewService(get_orchestrator())


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService(get_settings(), get_vector_store())


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(Evaluator(get_review_service()))


def get_app_settings() -> Settings:
    return get_settings()

