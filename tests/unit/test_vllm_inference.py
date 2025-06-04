import pytest

from questions.vllm_inference import VLLM_AVAILABLE, fast_vllm_inference
from questions.models import GenerateParams
from questions.inference_server.model_cache import ModelCache


@pytest.mark.skipif(VLLM_AVAILABLE, reason="vllm available - skip lightweight test")
def test_vllm_missing():
    params = GenerateParams(text="hi")
    with pytest.raises(RuntimeError):
        fast_vllm_inference(params, ModelCache())
