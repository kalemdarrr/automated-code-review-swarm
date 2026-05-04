"""Prompt execution helpers for structured local LLM outputs."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.llm.local_llm_client import LocalLLMClient

logger = logging.getLogger(__name__)


class PromptRunner:
    """Runs prompts and extracts JSON when an agent requests structured output."""

    def __init__(self, llm_client: LocalLLMClient) -> None:
        self.llm_client = llm_client

    def run_json_prompt(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_contract: str,
        max_new_tokens: int = 1200,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        prompt = self._build_prompt(system_prompt, user_payload, output_contract)
        raw = self.llm_client.generate(prompt, max_new_tokens=max_new_tokens, temperature=temperature)
        return extract_json_object(raw)

    @staticmethod
    def _build_prompt(system_prompt: str, user_payload: dict[str, Any], output_contract: str) -> str:
        return (
            f"{system_prompt}\n\n"
            "You must analyze the input as static text only. Do not execute code. "
            "Return valid JSON only, with no markdown fences.\n\n"
            f"Output contract:\n{output_contract}\n\n"
            f"Input JSON:\n{json.dumps(user_payload, ensure_ascii=True, indent=2)}\n\n"
            "JSON response:"
        )


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from model output."""

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(cleaned[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            logger.debug("Failed to parse extracted JSON: %s", exc)

    raise ValueError("Local LLM did not return a valid JSON object.")

