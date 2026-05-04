"""Run extrinsic benchmark evaluation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dependencies import get_evaluation_service
from app.utils.logging_utils import configure_logging


def main() -> None:
    configure_logging()
    result = get_evaluation_service().run()
    print(f"total examples: {result['total_examples']}")
    print(f"detected vulnerabilities: {result['detected_vulnerabilities']}")
    print(f"missed vulnerabilities: {result['missed_vulnerabilities']}")
    print(f"false positives: {result['false_positives']}")
    print(f"RAG relevance average: {result['rag_relevance_average']}")
    print(f"latency average: {result['latency_average']}")
    print(f"final score: {result['final_score']}")


if __name__ == "__main__":
    main()

