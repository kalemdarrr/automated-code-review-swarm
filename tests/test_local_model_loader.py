from __future__ import annotations

from dataclasses import replace

import pytest

from app.config import get_settings
from app.core.llm.local_model_loader import LocalModelLoadError, LocalModelLoader


def test_local_model_loader_reports_missing_model_files(tmp_path) -> None:
    settings = replace(get_settings(), local_model_path=tmp_path / "missing_model")
    loader = LocalModelLoader(settings)

    with pytest.raises(LocalModelLoadError) as error:
        loader.load()

    assert "Local model directory does not exist" in str(error.value)


def test_model_files_present_false_for_empty_directory(tmp_path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    settings = replace(get_settings(), local_model_path=model_dir)
    loader = LocalModelLoader(settings)

    assert loader.model_files_present() is False

