"""Markdown formatting helpers."""

from __future__ import annotations

from typing import Any


def bullet_list(items: list[str], empty_text: str = "None reported.") -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def fenced_code(code: str | None, language: str = "") -> str:
    if not code:
        return "Not isolated."
    return f"```{language}\n{code.strip()}\n```"


def confidence(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "0.00"

