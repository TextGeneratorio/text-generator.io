import os
import importlib
import pytest

from questions.vllm_inference import VLLM_AVAILABLE


def test_use_vllm_env_flag(monkeypatch):
    monkeypatch.setenv("USE_VLLM", "0")
    try:
        module = importlib.reload(
            importlib.import_module("questions.inference_server.inference_server")
        )
    except ModuleNotFoundError:
        pytest.skip("torch or other deps missing")
    assert (module.USE_VLLM is False) or (not VLLM_AVAILABLE)
