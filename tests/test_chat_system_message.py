import pytest
from types import SimpleNamespace

from questions.inference_server import inference_server
from questions.models import ChatCompletionParams, GenerateParams, OpenaiParams, map_to_generate_params


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
