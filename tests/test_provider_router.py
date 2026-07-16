from __future__ import annotations

from questions.provider_catalog import openai_model_list, resolve_model, usage_cost_cents
from questions.provider_router import ProviderRouter


class FakeResponse:
    def __init__(self, status_code=200, data=None, text=""):
        self.status_code = status_code
        self._data = data or {}
        self.text = text
        self.reason = text

    def json(self):
        return self._data


class RecordingSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_catalog_resolves_auto_alias_and_exposes_openai_list():
    assert resolve_model("auto").id == "text-generator/auto"
    payload = openai_model_list()
    ids = {item["id"] for item in payload["data"]}
    assert payload["object"] == "list"
    assert "text-generator/auto" in ids
    assert "claude-sonnet-latest" in ids


def test_usage_cost_is_model_priced_and_rounded_to_whole_cents():
    assert usage_cost_cents("gpt-4o-mini", {"prompt_tokens": 1, "completion_tokens": 1}) == 1
    assert usage_cost_cents("gpt-4o-mini", {"prompt_tokens": 1_000_000, "completion_tokens": 0}) == 15
    assert usage_cost_cents("claude-sonnet-latest", {"input_tokens": 10_000, "output_tokens": 1_000}) == 5


def test_router_sends_openai_compatible_request(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    session = RecordingSession([
        FakeResponse(data={
            "id": "chatcmpl-test",
            "choices": [{"message": {"role": "assistant", "content": "hello"}, "finish_reason": "stop"}],
        })
    ])
    router = ProviderRouter(session=session)

    result = router.chat_completion({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 50,
        "temperature": 0.5,
    })

    url, request = session.calls[0]
    assert url == "https://api.openai.com/v1/chat/completions"
    assert request["headers"]["Authorization"] == "Bearer test-openai"
    assert request["json"]["model"] == "gpt-4o-mini"
    assert result.selected_model == "gpt-4o-mini"
    assert result.data["provider"] == "openai"


def test_reasoning_models_use_max_completion_tokens(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    session = RecordingSession([FakeResponse(data={"choices": []})])
    router = ProviderRouter(session=session)

    router.chat_completion({
        "model": "gpt-5.4-mini",
        "messages": [{"role": "user", "content": "solve this"}],
        "max_tokens": 100,
        "temperature": 0.2,
        "top_p": 0.8,
    })

    body = session.calls[0][1]["json"]
    assert body["max_completion_tokens"] == 100
    assert "max_tokens" not in body
    assert "temperature" not in body
    assert "top_p" not in body


def test_router_fails_over_to_configured_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter")
    session = RecordingSession([
        FakeResponse(429, {"error": {"message": "rate limited"}}),
        FakeResponse(data={"id": "fallback", "choices": []}),
    ])
    router = ProviderRouter(session=session)

    result = router.chat_completion({
        "model": "gpt-5.4-mini",
        "messages": [{"role": "user", "content": "implement an endpoint"}],
    })

    assert len(session.calls) == 2
    assert "openrouter.ai" in session.calls[1][0]
    assert result.provider == "openrouter"
    assert result.selected_model == "or/gpt-5.4"


def test_anthropic_response_is_normalized(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
    session = RecordingSession([
        FakeResponse(data={
            "id": "msg_test",
            "content": [{"type": "text", "text": "normalized"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 2},
        })
    ])
    router = ProviderRouter(session=session)

    result = router.chat_completion({
        "model": "claude-sonnet-latest",
        "messages": [
            {"role": "system", "content": "Be concise"},
            {"role": "user", "content": "Hello"},
        ],
        "max_tokens": 80,
    })

    body = session.calls[0][1]["json"]
    assert body["system"] == "Be concise"
    assert body["messages"] == [{"role": "user", "content": "Hello"}]
    assert result.data["choices"][0]["message"]["content"] == "normalized"
    assert result.data["usage"]["total_tokens"] == 12


def test_anthropic_translates_openai_image_parts(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
    session = RecordingSession([FakeResponse(data={"content": [], "usage": {}})])
    router = ProviderRouter(session=session)

    router.chat_completion({
        "model": "claude-haiku",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What is shown?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,ZmFrZQ=="}},
            ],
        }],
    })

    content = session.calls[0][1]["json"]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "What is shown?"}
    assert content[1] == {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": "ZmFrZQ=="},
    }


def test_auto_profile_uses_semantic_selection(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral")
    session = RecordingSession([FakeResponse(data={"choices": []})])
    router = ProviderRouter(session=session)
    monkeypatch.setattr(router.auto_router, "select", lambda profile, prompt: "codestral-latest")

    result = router.chat_completion({
        "model": "auto-code",
        "messages": [{"role": "user", "content": "complete this function"}],
    })

    assert result.requested_model == "auto-code"
    assert result.selected_model == "codestral-latest"
    assert result.data["routing"]["auto_selected_model"] == "codestral-latest"
