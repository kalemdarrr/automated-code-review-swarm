"""JSONL audit logging for review workflows."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.utils.file_utils import ensure_directory


class AuditLogger:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def log(self, event: dict[str, Any]) -> None:
        path = self.settings.audit_log_path
        ensure_directory(path.parent)
        enriched = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(enriched, default=_json_default, ensure_ascii=True) + "\n")


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    return str(value)

