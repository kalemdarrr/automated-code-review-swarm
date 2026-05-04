"""Application configuration.

The project is intentionally local-first: model paths, vector database paths,
and embedding paths are resolved from the repository unless explicitly
overridden with environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Central settings object used by APIs, services, and scripts."""

    project_root: Path
    local_model_path: Path
    local_embedding_model_path: Path
    knowledge_base_raw_path: Path
    chroma_db_path: Path
    chroma_collection_name: str
    audit_log_path: Path
    max_input_tokens: int
    default_top_k: int
    rag_low_confidence_threshold: float
    enable_heuristic_fallback: bool
    trust_remote_code: bool
    app_name: str = "Automated Code Review & Security Swarm"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_dir = Path(__file__).resolve().parent
    project_root = app_dir.parent
    return Settings(
        project_root=project_root,
        local_model_path=Path(os.getenv("LOCAL_MODEL_PATH", project_root / "models" / "local_llm")),
        local_embedding_model_path=Path(
            os.getenv("LOCAL_EMBEDDING_MODEL_PATH", project_root / "models" / "local_embedding")
        ),
        knowledge_base_raw_path=Path(
            os.getenv("KNOWLEDGE_BASE_RAW_PATH", project_root / "knowledge_base" / "raw")
        ),
        chroma_db_path=Path(os.getenv("CHROMA_DB_PATH", project_root / "knowledge_base" / "chroma_db")),
        chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "code_review_security_knowledge"),
        audit_log_path=Path(os.getenv("AUDIT_LOG_PATH", project_root / "reports" / "audit_logs" / "audit.jsonl")),
        max_input_tokens=int(os.getenv("MAX_INPUT_TOKENS", "4096")),
        default_top_k=int(os.getenv("RAG_TOP_K", "6")),
        rag_low_confidence_threshold=float(os.getenv("RAG_LOW_CONFIDENCE_THRESHOLD", "0.32")),
        enable_heuristic_fallback=_bool_env("ENABLE_HEURISTIC_FALLBACK", True),
        trust_remote_code=_bool_env("TRUST_REMOTE_CODE", False),
    )

