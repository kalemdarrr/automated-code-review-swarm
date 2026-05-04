"""Ingest raw knowledge base documents into ChromaDB."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dependencies import get_rag_service
from app.utils.logging_utils import configure_logging


def main() -> None:
    configure_logging()
    summary = get_rag_service().ingest()
    print(f"Indexed documents: {summary.indexed_documents}")
    print(f"Indexed chunks: {summary.indexed_chunks}")
    print(f"Categories: {', '.join(summary.categories)}")


if __name__ == "__main__":
    main()

