"""Base class for specialized code review agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from app.core.llm.local_llm_client import LocalLLMClient
from app.core.llm.prompt_runner import PromptRunner

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AgentResult:
    agent_name: str
    data: dict[str, Any]
    warnings: list[str]


class BaseAgent(ABC):
    """Common behavior for all swarm agents."""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        llm_client: LocalLLMClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm_client = llm_client
        self.settings = settings or get_settings()
        self.prompt_runner = PromptRunner(llm_client) if llm_client else None

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run the agent and return structured data."""

    def _run_llm_json(
        self,
        user_payload: dict[str, Any],
        output_contract: str,
        max_new_tokens: int = 420,
    ) -> tuple[dict[str, Any] | None, list[str]]:
        if self.prompt_runner is None:
            return None, ["No LocalLLMClient was supplied to this agent."]
        try:
            return (
                self.prompt_runner.run_json_prompt(
                    system_prompt=self.system_prompt,
                    user_payload=user_payload,
                    output_contract=output_contract,
                    max_new_tokens=max_new_tokens,
                ),
                [],
            )
        except Exception as exc:
            logger.warning("%s local LLM generation failed: %s", self.name, exc)
            return None, [f"{self.name} local LLM generation failed: {exc}"]
