"""Thin generation client around the local Transformer model."""

from __future__ import annotations

import logging
from typing import Any

from app.config import Settings, get_settings
from app.core.llm.local_model_loader import LocalModelLoader

logger = logging.getLogger(__name__)


class LocalLLMClient:
    """Provides a small, testable interface for local text generation."""

    def __init__(self, loader: LocalModelLoader | None = None, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.loader = loader or LocalModelLoader(self.settings)

    @property
    def is_loaded(self) -> bool:
        return self.loader.is_loaded

    def generate(self, prompt: str, max_new_tokens: int = 1024, temperature: float = 0.2) -> str:
        loaded = self.loader.load()

        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("torch is required for local generation.") from exc

        tokenizer = loaded.tokenizer
        model = loaded.model

        encoded = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.settings.max_input_tokens,
        )
        input_length = int(encoded["input_ids"].shape[-1])
        input_device = self._resolve_input_device(model)
        encoded = {name: tensor.to(input_device) for name, tensor in encoded.items()}

        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "pad_token_id": tokenizer.pad_token_id or tokenizer.eos_token_id,
            "eos_token_id": tokenizer.eos_token_id,
            "do_sample": temperature > 0,
        }
        if temperature > 0:
            generation_kwargs["temperature"] = max(0.01, temperature)

        with torch.no_grad():
            output_ids = model.generate(**encoded, **generation_kwargs)

        generated_ids = output_ids[0][input_length:]
        answer = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        if answer:
            return answer

        decoded = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
        if decoded.startswith(prompt):
            return decoded[len(prompt) :].strip()
        return decoded

    @staticmethod
    def _resolve_input_device(model: Any) -> str:
        try:
            return str(next(model.parameters()).device)
        except Exception:
            return "cuda:0" if getattr(model, "hf_device_map", None) else "cpu"

