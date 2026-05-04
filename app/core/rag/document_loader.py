"""Knowledge base document loading."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.utils.file_utils import iter_files

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class KnowledgeDocument:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentLoader:
    """Loads markdown, text, and optional PDF documents from the raw KB tree."""

    supported_suffixes = {".txt", ".md", ".pdf"}

    def __init__(self, raw_root: Path) -> None:
        self.raw_root = raw_root

    def load(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        for path in iter_files(self.raw_root, self.supported_suffixes):
            documents.extend(self._load_file(path))
        return documents

    def _load_file(self, path: Path) -> list[KnowledgeDocument]:
        category = self._category_for(path)
        base_metadata = {
            "source": str(path.relative_to(self.raw_root)) if path.is_relative_to(self.raw_root) else str(path),
            "category": category,
            "file_name": path.name,
        }
        if path.suffix.lower() == ".pdf":
            return self._load_pdf(path, base_metadata)

        text = path.read_text(encoding="utf-8", errors="ignore")
        metadata = {**base_metadata, "section": _first_markdown_heading(text)}
        return [KnowledgeDocument(text=text, metadata=metadata)]

    def _load_pdf(self, path: Path, base_metadata: dict[str, Any]) -> list[KnowledgeDocument]:
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.warning("Skipping PDF %s because pypdf is not installed.", path)
            return []

        reader = PdfReader(str(path))
        documents: list[KnowledgeDocument] = []
        for index, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                documents.append(
                    KnowledgeDocument(text=text, metadata={**base_metadata, "page": index + 1, "section": None})
                )
        return documents

    def _category_for(self, path: Path) -> str:
        try:
            relative = path.relative_to(self.raw_root)
            return relative.parts[0] if len(relative.parts) > 1 else "general"
        except ValueError:
            return "general"


def _first_markdown_heading(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
    return None

