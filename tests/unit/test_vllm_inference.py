import pytest
from questions.vllm_inference import VLLM_AVAILABLE, vllm_inference
from questions.models import GenerateParams


def test_vllm_import_flag():
    assert isinstance(VLLM_AVAILABLE, bool)


def test_vllm_inference_raises_when_missing():
    if VLLM_AVAILABLE:
        pytest.skip("vLLM installed, skip missing test")
    params = GenerateParams(text="hi")
    with pytest.raises(RuntimeError):
        vllm_inference(params, "models/SmolLM-1.7B")
