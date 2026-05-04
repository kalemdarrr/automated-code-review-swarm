"""Download local LLM and embedding models into project folders.

This script downloads public HuggingFace model repositories directly into:
- models/local_llm/
- models/local_embedding/

No remote inference APIs are used; the models are downloaded once and used
locally via transformers/sentence-transformers.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.utils.file_utils import ensure_directory


DEFAULT_LLM_MODEL_ID = os.getenv("HF_LLM_MODEL_ID", "Qwen/Qwen2.5-Coder-0.5B-Instruct")
DEFAULT_EMBEDDING_MODEL_ID = os.getenv("HF_EMBEDDING_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download local models for the review swarm.")
    parser.add_argument("--llm-model-id", default=DEFAULT_LLM_MODEL_ID)
    parser.add_argument("--embedding-model-id", default=DEFAULT_EMBEDDING_MODEL_ID)
    parser.add_argument("--skip-llm", action="store_true")
    parser.add_argument("--skip-embedding", action="store_true")
    parser.add_argument("--force", action="store_true", help="Force re-download of model files.")
    return parser.parse_args()


def download_repo(repo_id: str, local_dir: Path, allow_patterns: list[str], force: bool) -> None:
    from huggingface_hub import snapshot_download

    ensure_directory(local_dir)
    print(f"[download] repo={repo_id} -> {local_dir}")
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        allow_patterns=allow_patterns,
        resume_download=True,
        force_download=force,
    )


def main() -> None:
    args = parse_args()
    settings = get_settings()

    if not args.skip_llm:
        llm_patterns = [
            "*.json",
            "*.txt",
            "*.safetensors",
            "*.bin",
            "*.model",
            "tokenizer.*",
            "vocab.*",
            "merges.txt",
        ]
        download_repo(args.llm_model_id, settings.local_model_path, llm_patterns, force=args.force)

    if not args.skip_embedding:
        embedding_patterns = [
            "*.json",
            "*.txt",
            "*.safetensors",
            "*.bin",
            "*.model",
            "*.py",
            "tokenizer.*",
            "vocab.*",
            "merges.txt",
            "modules.json",
            "config_sentence_transformers.json",
            "README.md",
        ]
        download_repo(
            args.embedding_model_id,
            settings.local_embedding_model_path,
            embedding_patterns,
            force=args.force,
        )

    print("[done] model download completed")


if __name__ == "__main__":
    main()
