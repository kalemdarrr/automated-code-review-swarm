"""Run a demo review against the bundled vulnerable Python sample."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dependencies import get_review_service
from app.utils.logging_utils import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local multi-agent code review demo.")
    parser.add_argument("--sample", default=str(PROJECT_ROOT / "reports" / "sample_outputs" / "vulnerable_demo.py"))
    args = parser.parse_args()

    configure_logging()
    sample_path = Path(args.sample)
    code = sample_path.read_text(encoding="utf-8")
    result = get_review_service().review_code(
        code=code,
        language="python",
        review_depth="deep",
        include_security=True,
        include_clean_code=True,
        include_rag_sources=True,
    )
    output_path = PROJECT_ROOT / "reports" / "sample_outputs" / "demo_report.md"
    output_path.write_text(result.final_report, encoding="utf-8")
    print(result.final_report)
    print(f"\nDemo report written to: {output_path}")


if __name__ == "__main__":
    main()

