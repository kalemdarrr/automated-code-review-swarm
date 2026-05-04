"""Text normalization and lightweight parsing helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 40].rstrip() + "\n...[truncated for safety]..."


def keyword_overlap(left: str, right: str) -> float:
    left_terms = _keywords(left)
    right_terms = _keywords(right)
    if not left_terms or not right_terms:
        return 0.0
    return len(left_terms & right_terms) / max(len(left_terms), 1)


def _keywords(text: str) -> set[str]:
    stop_words = {
        "the",
        "and",
        "or",
        "of",
        "to",
        "a",
        "in",
        "for",
        "is",
        "with",
        "this",
        "that",
        "be",
        "as",
        "by",
        "on",
        "it",
    }
    return {token for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text.lower()) if token not in stop_words}


def deduplicate_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result

