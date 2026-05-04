"""Run end-to-end local stack verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.llm.local_model_loader import get_torch_device_summary
from app.dependencies import (
    get_model_loader,
    get_rag_service,
    get_review_service,
    get_vector_store,
)
from app.utils.logging_utils import configure_logging


SMOKE_CODE = """
import sqlite3
import subprocess

DB_PASSWORD = "bad-password"

def run(conn, user_id, expr, filename, host):
    q = f"SELECT * FROM users WHERE id = {user_id}"
    user = conn.execute(q).fetchone()
    value = eval(expr)
    text = open("/srv/app/uploads/" + filename).read()
    out = subprocess.check_output("ping -c 1 " + host, shell=True)
    return str(user) + str(value) + text + str(out)
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify local model + RAG + swarm review flow.")
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument("--skip-review", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging()

    cuda_available, device = get_torch_device_summary()
    print(f"[device] cuda_available={cuda_available} device={device}")

    model_loader = get_model_loader()
    print(f"[model] local_model_path={model_loader.settings.local_model_path}")
    print(f"[model] files_present={model_loader.model_files_present()}")
    loaded = model_loader.load()
    print(f"[model] loaded=True runtime_device={loaded.device} dtype={loaded.dtype}")

    vector_store = get_vector_store()
    print(f"[vector] available={vector_store.available} count={vector_store.count()}")

    if not args.skip_ingest:
        ingest_summary = get_rag_service().ingest()
        print(
            "[rag] ingested "
            f"documents={ingest_summary.indexed_documents} "
            f"chunks={ingest_summary.indexed_chunks} "
            f"categories={ingest_summary.categories}"
        )
        print(f"[vector] post_ingest_count={vector_store.count()}")

    if not args.skip_review:
        result = get_review_service().review_code(
            code=SMOKE_CODE,
            language="python",
            review_depth="standard",
            include_security=True,
            include_clean_code=True,
            include_rag_sources=True,
        )
        payload = result.as_dict()
        print(
            "[review] "
            f"risk_score={payload['risk_score']} "
            f"security_findings={len(payload['security_findings'])} "
            f"clean_code_findings={len(payload['clean_code_findings'])} "
            f"rag_sources={len(payload['rag_sources'])}"
        )
        print("[review] sample_report_header:")
        print("\n".join(payload["final_report"].splitlines()[:8]))
        print("[review] trace:")
        print(json.dumps(payload["agent_trace"], indent=2))

    print("[done] stack verification completed")


if __name__ == "__main__":
    main()

