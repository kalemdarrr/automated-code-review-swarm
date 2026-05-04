"""Local HuggingFace causal language model loading with CUDA support."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class LocalModelLoadError(RuntimeError):
    """Raised when the local Transformer model cannot be loaded."""


@dataclass(slots=True)
class LoadedLocalModel:
    tokenizer: Any
    model: Any
    device: str
    dtype: str
    model_path: Path


class LocalModelLoader:
    """Loads a local HuggingFace-compatible causal LLM.

    This class never downloads remote model files. It expects a complete model
    directory with a tokenizer and model weights under ``models/local_llm/`` or
    the configured ``LOCAL_MODEL_PATH``.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._loaded_model: LoadedLocalModel | None = None

    @property
    def is_loaded(self) -> bool:
        return self._loaded_model is not None

    def model_files_present(self) -> bool:
        path = self.settings.local_model_path
        if not path.exists() or not path.is_dir():
            return False
        has_config = (path / "config.json").exists()
        has_tokenizer = any(
            (path / name).exists()
            for name in ("tokenizer.json", "tokenizer.model", "vocab.json", "spiece.model")
        )
        has_hf_weights = any(path.glob(pattern) for pattern in ("*.safetensors", "*.bin", "*.pt"))
        return has_config and has_tokenizer and has_hf_weights

    def load(self) -> LoadedLocalModel:
        if self._loaded_model is not None:
            return self._loaded_model

        self._validate_model_path()

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise LocalModelLoadError(
                "Missing local inference dependencies. Install torch and transformers from requirements.txt."
            ) from exc

        cuda_available = bool(torch.cuda.is_available())
        device = "cuda" if cuda_available else "cpu"
        if cuda_available:
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            logger.info("CUDA detected. Loading local model with device_map='auto' and dtype=%s.", dtype)
            model_kwargs: dict[str, Any] = {
                "torch_dtype": dtype,
                "device_map": "auto",
                "local_files_only": True,
                "trust_remote_code": self.settings.trust_remote_code,
            }
        else:
            dtype = torch.float32
            logger.warning("CUDA is not available. Falling back to CPU local inference.")
            model_kwargs = {
                "torch_dtype": dtype,
                "local_files_only": True,
                "trust_remote_code": self.settings.trust_remote_code,
            }

        tokenizer = AutoTokenizer.from_pretrained(
            self.settings.local_model_path,
            local_files_only=True,
            trust_remote_code=self.settings.trust_remote_code,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(self.settings.local_model_path, **model_kwargs)
        if not cuda_available:
            model.to(device)
        model.eval()

        self._loaded_model = LoadedLocalModel(
            tokenizer=tokenizer,
            model=model,
            device=device,
            dtype=str(dtype).replace("torch.", ""),
            model_path=self.settings.local_model_path,
        )
        return self._loaded_model

    def _validate_model_path(self) -> None:
        path = self.settings.local_model_path
        if not path.exists():
            raise LocalModelLoadError(
                f"Local model directory does not exist: {path}. "
                "Place a HuggingFace-compatible causal model under models/local_llm/."
            )
        has_gguf_only = any(path.glob("*.gguf")) and not any(
            path.glob(pattern) for pattern in ("*.safetensors", "*.bin", "*.pt")
        )
        if has_gguf_only:
            raise LocalModelLoadError(
                "Found GGUF files only. This project uses transformers.AutoModelForCausalLM and requires "
                "HuggingFace model weights (.safetensors/.bin/.pt) in models/local_llm/."
            )
        if not self.model_files_present():
            raise LocalModelLoadError(
                "Local model files are incomplete. Expected config.json, tokenizer files, and model weights "
                f"inside {path}. No remote downloads are allowed because local_files_only=True is required."
            )


def get_torch_device_summary() -> tuple[bool, str]:
    """Return CUDA availability and a human-readable device string."""

    try:
        import torch
    except ImportError:
        return False, "torch-not-installed"
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        return True, f"cuda:0 ({device_name})"
    return False, "cpu"
