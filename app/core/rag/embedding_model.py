"""Local embedding model abstraction."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


class EmbeddingModel(Protocol):
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class LocalSentenceTransformerEmbedding:
    """SentenceTransformer wrapper that loads only from a local path."""

    def __init__(self, model_path: Path, device: str | None = None) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Local embedding model path does not exist: {model_path}")

        try:
            import torch
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("sentence-transformers and torch are required for local embedding models.") from exc

        resolved_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        try:
            self.model = SentenceTransformer(str(model_path), device=resolved_device, local_files_only=True)
        except TypeError:
            self.model = SentenceTransformer(str(model_path), device=resolved_device)
        self.dimension = int(self.model.get_sentence_embedding_dimension() or 384)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return [vector.astype(float).tolist() for vector in vectors]


class HashingEmbeddingModel:
    """Deterministic local fallback embedding model.

    It is not as semantically strong as a SentenceTransformer, but it preserves
    the no-network/no-API constraint and keeps ChromaDB retrieval functional in
    environments where a local embedding model has not been supplied yet.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,}", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def build_embedding_model(model_path: Path) -> EmbeddingModel:
    if model_path.exists():
        logger.info("Loading local SentenceTransformer embedding model from %s.", model_path)
        return LocalSentenceTransformerEmbedding(model_path)
    logger.warning(
        "Local embedding model path %s was not found. Using deterministic hashing embeddings; "
        "place a SentenceTransformer model there for stronger semantic retrieval.",
        model_path,
    )
    return HashingEmbeddingModel()

