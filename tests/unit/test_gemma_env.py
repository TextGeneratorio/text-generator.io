import os
import importlib
import pytest

pytest.importorskip("transformers")


def test_load_gemma_pipe_env(monkeypatch):
    monkeypatch.setenv("GEMMA_MODEL_ID", "yujiepan/gemma-3n-tiny-random")
    module = importlib.import_module("questions.link_enricher")
    pipe = module.load_gemma_pipe()
    assert pipe.model.name_or_path == "yujiepan/gemma-3n-tiny-random"
