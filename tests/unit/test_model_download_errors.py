import pytest
from fastapi import HTTPException
from google.auth.exceptions import DefaultCredentialsError

from questions import download_utils
from questions.inference_server import inference_server
from questions.models import GenerateParams


def test_download_model_maps_missing_google_credentials(monkeypatch, tmp_path):
    def missing_credentials_client():
        raise DefaultCredentialsError("missing credentials")

    monkeypatch.setattr(download_utils.storage, "Client", missing_credentials_client)

    with pytest.raises(download_utils.ModelDownloadUnavailable) as exc_info:
        download_utils.download_model("models/missing", str(tmp_path / "model"))

    assert "Model storage credentials are unavailable" in str(exc_info.value)


def test_smollm_path_falls_back_to_public_hf_repo_when_model_storage_unavailable(monkeypatch):
    from questions import text_generator_inference

    def missing_config(_weights_path):
        return False

    def unavailable_download(*_args, **_kwargs):
        raise download_utils.ModelDownloadUnavailable("Model storage credentials are unavailable")

    monkeypatch.setattr(text_generator_inference, "_has_model_config", missing_config)
    monkeypatch.setattr(text_generator_inference, "download_model", unavailable_download)

    assert (
        text_generator_inference._resolve_model_weights_path("models/SmolLM3-3B")
        == "HuggingFaceTB/SmolLM3-3B"
    )


def test_smollm_public_fallback_skips_private_storage_when_not_local(monkeypatch):
    from questions import text_generator_inference

    def missing_config(_weights_path):
        return False

    def unexpected_download(*_args, **_kwargs):
        raise AssertionError("download_model should not be called for public fallback models")

    monkeypatch.setattr(text_generator_inference, "_has_model_config", missing_config)
    monkeypatch.setattr(text_generator_inference, "download_model", unexpected_download)

    assert (
        text_generator_inference._resolve_model_weights_path("models/SmolLM3-3B")
        == "HuggingFaceTB/SmolLM3-3B"
    )


def test_unknown_model_path_keeps_storage_unavailable_error(monkeypatch):
    from questions import text_generator_inference

    def missing_config(_weights_path):
        return False

    def unavailable_download(*_args, **_kwargs):
        raise download_utils.ModelDownloadUnavailable("Model storage credentials are unavailable")

    monkeypatch.setattr(text_generator_inference, "_has_model_config", missing_config)
    monkeypatch.setattr(text_generator_inference, "download_model", unavailable_download)

    with pytest.raises(download_utils.ModelDownloadUnavailable):
        text_generator_inference._resolve_model_weights_path("models/private-model")


@pytest.mark.asyncio
async def test_run_text_generate_maps_model_download_unavailable_to_503(monkeypatch):
    def unavailable_model(*_args, **_kwargs):
        raise download_utils.ModelDownloadUnavailable("Model storage credentials are unavailable")

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "")
    monkeypatch.setattr(inference_server, "_fast_inference", unavailable_model)

    with pytest.raises(HTTPException) as exc_info:
        await inference_server._run_text_generate(
            GenerateParams(text="hello", max_length=1, min_probability=0),
            model_cache=None,
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Text generation model unavailable"


@pytest.mark.asyncio
async def test_run_text_generate_maps_cuda_capacity_error_to_503(monkeypatch):
    class FakeModelCache:
        def __init__(self):
            self.unload_reasons = []

        def unload_all(self, reason):
            self.unload_reasons.append(reason)

    def cuda_capacity_error(*_args, **_kwargs):
        raise RuntimeError("CUDA error: CUBLAS_STATUS_ALLOC_FAILED when calling `cublasCreate(handle)`")

    model_cache = FakeModelCache()
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "")
    monkeypatch.setattr(inference_server, "_fast_inference", cuda_capacity_error)

    with pytest.raises(HTTPException) as exc_info:
        await inference_server._run_text_generate(
            GenerateParams(text="hello", max_length=1, min_probability=0),
            model_cache=model_cache,
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Text generation backend unavailable"
    assert model_cache.unload_reasons == ["GPU capacity error"]
