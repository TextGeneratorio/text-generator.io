import pytest
from types import SimpleNamespace
from io import BytesIO

from starlette.datastructures import Headers, UploadFile

from questions.inference_server import inference_server
from questions.models import ChatCompletionParams, GenerateParams, OpenaiParams, map_to_generate_params


def _part_value(part, field):
    return getattr(part, field) if hasattr(part, field) else part[field]


@pytest.mark.asyncio
async def test_image_caption_accepts_legacy_valid_secret_without_credits(monkeypatch):
    def fake_request_authorized(request, secret):
        return secret == "legacy-valid-secret"

    monkeypatch.setattr(inference_server, "request_authorized", fake_request_authorized)
    monkeypatch.setattr(inference_server, "_user_has_subscription_or_credits", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(inference_server, "_consume_user_credits", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        inference_server,
        "_run_media_prompt_with_multimodal_model",
        lambda **_kwargs: "a small test image",
    )

    upload = UploadFile(
        filename="test.png",
        file=BytesIO(b"not-actually-decoded-by-this-test"),
        headers=Headers({"content-type": "image/png"}),
    )

    response = await inference_server.image_caption(
        image_file=upload,
        image_url=None,
        fast_mode=True,
        custom_prompt=None,
        request=SimpleNamespace(headers={}),
        secret="legacy-valid-secret",
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_image_caption_accepts_netwrck_caption_secret(monkeypatch):
    def fail_request_authorized(_request, _secret):
        raise AssertionError("netwrck image caption secret should not hit DB auth")

    monkeypatch.setattr(inference_server, "NETWRCK_IMAGE_CAPTION_SECRET", "netwrck-caption-secret")
    monkeypatch.setattr(inference_server, "request_authorized", fail_request_authorized)
    monkeypatch.setattr(inference_server, "_consume_user_credits", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        inference_server,
        "_run_media_prompt_with_multimodal_model",
        lambda **_kwargs: "a small test image",
    )

    upload = UploadFile(
        filename="test.png",
        file=BytesIO(b"not-actually-decoded-by-this-test"),
        headers=Headers({"content-type": "image/png"}),
    )

    response = await inference_server.image_caption(
        image_file=upload,
        image_url=None,
        fast_mode=True,
        custom_prompt=None,
        request=SimpleNamespace(headers={}),
        secret="netwrck-caption-secret",
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_route_injects_top_level_system_message(monkeypatch):
    captured = {}

    def fake_chat_inference(**kwargs):
        captured.update(kwargs)
        return {"generated_text": "ok", "thinking_content": None, "stop_reason": "stop"}

    monkeypatch.setattr(inference_server, "_chat_inference", fake_chat_inference)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: None)

    params = ChatCompletionParams(
        model="qwen3.5-4b",
        system_message="You are strict.",
        messages=[{"role": "user", "content": "Hello"}],
        stream=False,
        enable_thinking=False,
    )

    response = await inference_server.chat_completions_route(params)

    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][0]["content"] == "You are strict."
    assert captured["messages"][1]["role"] == "user"
    assert response["choices"][0]["message"]["content"] == "ok"


@pytest.mark.asyncio
async def test_chat_route_merges_top_level_with_existing_system_message(monkeypatch):
    captured = {}

    def fake_chat_inference(**kwargs):
        captured.update(kwargs)
        return {"generated_text": "ok", "thinking_content": None, "stop_reason": "stop"}

    monkeypatch.setattr(inference_server, "_chat_inference", fake_chat_inference)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: None)

    params = ChatCompletionParams(
        model="qwen3.5-4b",
        system_message="Top-level instruction.",
        messages=[
            {"role": "system", "content": "Existing instruction."},
            {"role": "user", "content": "Hello"},
        ],
        stream=False,
        enable_thinking=False,
    )

    await inference_server.chat_completions_route(params)

    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][0]["content"] == "Top-level instruction.\n\nExisting instruction."
    assert captured["messages"][1]["role"] == "user"


def test_openai_completions_system_message_maps_to_generate_params():
    openai_params = OpenaiParams(
        prompt="def can_balance(a):",
        n=1,
        max_tokens=64,
        system_message="Continue code only.",
    )

    generate_params = map_to_generate_params(openai_params)
    assert generate_params.system_message == "Continue code only."


def test_openai_completions_system_prompt_alias_maps_to_generate_params():
    openai_params = OpenaiParams(
        prompt="def can_balance(a):",
        n=1,
        max_tokens=64,
        system_prompt="Alias prompt",
    )

    generate_params = map_to_generate_params(openai_params)
    assert generate_params.system_message == "Alias prompt"


@pytest.mark.asyncio
async def test_generate_route_forwards_system_message(monkeypatch):
    captured = {}

    def fake_fast_inference(generate_params, model_cache):
        captured["system_message"] = generate_params.system_message
        return [{"generated_text": "ok", "stop_reason": "stop", "thinking_content": None}]

    monkeypatch.setattr(inference_server, "validate_generate_params", lambda _: None)
    monkeypatch.setattr(inference_server, "_fast_inference", fake_fast_inference)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: None)

    params = GenerateParams(
        text="def can_balance(a):",
        system_message="Continue code only.",
        max_length=32,
    )

    response = await inference_server.generate_route(params)
    assert captured["system_message"] == "Continue code only."
    assert response[0]["generated_text"] == "ok"


@pytest.mark.asyncio
async def test_generate_route_forwards_system_prompt_alias(monkeypatch):
    captured = {}

    def fake_fast_inference(generate_params, model_cache):
        captured["system_message"] = generate_params.system_prompt
        return [{"generated_text": "ok", "stop_reason": "stop", "thinking_content": None}]

    monkeypatch.setattr(inference_server, "validate_generate_params", lambda _: None)
    monkeypatch.setattr(inference_server, "_fast_inference", fake_fast_inference)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: None)

    params = GenerateParams(
        text="def can_balance(a):",
        system_prompt="Alias prompt",
        max_length=32,
    )

    response = await inference_server.generate_route(params)
    assert captured["system_message"] == "Alias prompt"
    assert response[0]["generated_text"] == "ok"


@pytest.mark.asyncio
async def test_openai_completions_route_forwards_system_message(monkeypatch):
    captured = {}

    def fake_fast_inference(generate_params, model_cache):
        captured["system_message"] = generate_params.system_message
        return [{"generated_text": "done", "stop_reason": "stop", "thinking_content": None}]

    monkeypatch.setattr(inference_server, "validate_generate_params", lambda _: None)
    monkeypatch.setattr(inference_server, "_fast_inference", fake_fast_inference)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: None)
    monkeypatch.setattr(inference_server, "request_authorized", lambda request, secret: True)

    params = OpenaiParams(
        prompt="def can_balance(a):",
        system_message="Continue code only.",
        max_tokens=64,
        echo=True,
    )
    request = SimpleNamespace(headers={})

    response = await inference_server.openai_route(params, request=request)

    assert captured["system_message"] == "Continue code only."
    assert response["choices"][0]["text"] == "done"


@pytest.mark.asyncio
async def test_chat_route_accepts_system_prompt_alias(monkeypatch):
    captured = {}

    def fake_chat_inference(**kwargs):
        captured.update(kwargs)
        return {"generated_text": "ok", "thinking_content": None, "stop_reason": "stop"}

    monkeypatch.setattr(inference_server, "_chat_inference", fake_chat_inference)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: None)

    params = ChatCompletionParams(
        model="qwen3.5-4b",
        system_prompt="Alias chat prompt.",
        messages=[{"role": "user", "content": "Hello"}],
        stream=False,
        enable_thinking=False,
    )

    response = await inference_server.chat_completions_route(params)
    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][0]["content"] == "Alias chat prompt."
    assert response["choices"][0]["message"]["content"] == "ok"


@pytest.mark.asyncio
async def test_chat_route_uses_multimodal_inference_for_structured_media_content(monkeypatch):
    captured = {}

    def fake_multimodal_chat_inference(**kwargs):
        captured.update(kwargs)
        return {"generated_text": "transcript", "thinking_content": None, "stop_reason": "stop"}

    monkeypatch.setattr(inference_server, "_multimodal_chat_inference", fake_multimodal_chat_inference)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: None)

    params = ChatCompletionParams(
        model="google/gemma-4-26B-A4B-it",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "audio", "url": "https://example.com/test.mp3"},
                    {"type": "text", "text": "Transcribe the audio."},
                ],
            }
        ],
        stream=False,
        enable_thinking=False,
    )

    response = await inference_server.chat_completions_route(params)

    first_part = captured["messages"][0]["content"][0]
    second_part = captured["messages"][0]["content"][1]

    assert _part_value(first_part, "type") == "audio"
    assert _part_value(first_part, "url") == "https://example.com/test.mp3"
    assert _part_value(second_part, "type") == "text"
    assert response["choices"][0]["message"]["content"] == "transcript"


def test_select_multimodal_model_routes_audio_to_audio_capable_gemma(monkeypatch):
    monkeypatch.setattr(inference_server, "GEMMA_TEXT_IMAGE_MODEL_ID", "google/gemma-4-26B-A4B-it")
    monkeypatch.setattr(inference_server, "GEMMA_AUDIO_MODEL_ID", "google/gemma-4-e4b-it")
    monkeypatch.setattr(inference_server, "GEMMA_VIDEO_MODEL_ID", "google/gemma-4-e4b-it")

    audio_messages = [
        {
            "role": "user",
            "content": [
                {"type": "audio", "url": "https://example.com/test.mp3"},
                {"type": "text", "text": "Transcribe the audio."},
            ],
        }
    ]
    image_messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "url": "https://example.com/test.png"},
                {"type": "text", "text": "Describe the image."},
            ],
        }
    ]

    assert inference_server._select_multimodal_model_id(audio_messages) == "google/gemma-4-e4b-it"
    assert inference_server._select_multimodal_model_id(image_messages) == "google/gemma-4-26B-A4B-it"


def test_build_multimodal_generation_kwargs_defaults_to_sampling_off():
    kwargs = inference_server._build_multimodal_generation_kwargs(
        max_tokens=32,
        temperature=0.0,
        top_p=0.95,
        top_k=64,
    )

    assert kwargs["max_new_tokens"] == 32
    assert kwargs["do_sample"] is False
    assert "compile_config" not in kwargs
    assert "cache_implementation" not in kwargs


def test_build_multimodal_generation_kwargs_adds_compile_config(monkeypatch):
    monkeypatch.setattr(inference_server, "GEMMA_ENABLE_TORCH_COMPILE", True)
    monkeypatch.setattr(inference_server, "GEMMA_TORCH_COMPILE_BACKEND", "inductor")
    monkeypatch.setattr(inference_server, "GEMMA_TORCH_COMPILE_MODE", "reduce-overhead")
    monkeypatch.setattr(inference_server, "GEMMA_TORCH_COMPILE_FULLGRAPH", False)
    monkeypatch.setattr(inference_server, "GEMMA_TORCH_COMPILE_DYNAMIC", "1")

    kwargs = inference_server._build_multimodal_generation_kwargs(
        max_tokens=64,
        temperature=1.0,
        top_p=0.9,
        top_k=32,
    )

    assert kwargs["do_sample"] is True
    assert kwargs["temperature"] == 1.0
    assert kwargs["top_p"] == 0.9
    assert kwargs["top_k"] == 32
    assert kwargs["cache_implementation"] == "static"
    assert kwargs["compile_config"].backend == "inductor"
    assert kwargs["compile_config"].mode == "reduce-overhead"
    assert kwargs["compile_config"].dynamic is True
