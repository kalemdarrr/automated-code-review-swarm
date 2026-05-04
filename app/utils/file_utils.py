"""Filesystem helpers used by scripts and loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def iter_files(root: Path, suffixes: Iterable[str]) -> list[Path]:
    suffix_set = {suffix.lower() for suffix in suffixes}
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffix_set)

