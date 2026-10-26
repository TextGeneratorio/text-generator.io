import asyncio
import json
import threading
from http.client import RemoteDisconnected
from urllib.error import URLError

import pytest
import requests
from fastapi import HTTPException

from questions.inference_server import inference_server
from questions.models import ChatCompletionParams, ChatMessage, FeatureExtractParams, GenerateParams


class FakeUrlopenResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class FakeRequestsResponse:
    def __init__(self, payload=None, status_code=200, text="", reason="", chunks=None):
        self.payload = payload
        self.status_code = status_code
        self.text = text
        self.reason = reason
        self.chunks = chunks or []
        self.closed = False

    def json(self):
        return self.payload

    def iter_content(self, chunk_size=None):
        yield from self.chunks

    def close(self):
        self.closed = True


class FakeRequestsSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def post(self, url, data=None, headers=None, timeout=None, stream=False):
        self.calls.append({
            "url": url,
            "body": json.loads(data.decode("utf-8")),
            "headers": headers or {},
            "timeout": timeout,
            "stream": stream,
        })
        if self.exc:
            raise self.exc
        return self.response


class FakeRequestsSequenceSession:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def post(self, url, data=None, headers=None, timeout=None, stream=False):
        self.calls.append({
            "url": url,
            "body": json.loads(data.decode("utf-8")),
            "headers": headers or {},
            "timeout": timeout,
            "stream": stream,
        })
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def test_vllm_proxy_is_opt_in_and_explicit_empty_disables_adapter_alias(monkeypatch):
    monkeypatch.delenv("VLLM_TEXT_BACKEND_BASE", raising=False)
    monkeypatch.delenv("VLLM_ADAPTER_BASE", raising=False)
    assert inference_server._resolve_vllm_text_backend_base() == ""

    monkeypatch.setenv("VLLM_ADAPTER_BASE", "http://adapter:8300/")
    assert inference_server._resolve_vllm_text_backend_base() == "http://adapter:8300"

    monkeypatch.setenv("VLLM_TEXT_BACKEND_BASE", "")
    assert inference_server._resolve_vllm_text_backend_base() == ""


def test_vllm_adapter_uses_literal_continuation_when_healing_is_disabled(monkeypatch):
    from questions.inference_server import vllm_parity_adapter as adapter

    calls = []

    def complete(prompt, max_tokens, sampling, extra=None, model=None, n=1):
        calls.append({"prompt": prompt, "extra": extra, "n": n})
        return [{"text": " for something", "tokens": [" for", " something"],
                 "probs": [0.9, 0.8], "finish_reason": "stop"}]

    monkeypatch.setattr(adapter, "HEAL", False)
    monkeypatch.setattr(adapter, "_complete_raw", complete)

    result = adapter._continue_with_healing(
        "Hi i'm bored so looking", 8, {"temperature": 0.7}, n=1,
    )

    assert calls == [{"prompt": "Hi i'm bored so looking", "extra": {}, "n": 1}]
    assert result == [([" for", " something"], [0.9, 0.8], "stop")]


def test_vllm_adapter_repairs_uppercase_boundary_without_breaking_subwords():
    from questions.inference_server import vllm_parity_adapter as adapter

    base = adapter.GenerateParams(text="Hi i'm bored so looking", min_probability=0)
    repaired = adapter._postprocess_raw(base, 8, ["I"], [0.9], "stop")
    assert repaired["generated_text"] == "Hi i'm bored so looking I"

    partial = adapter.GenerateParams(text="Hi my n", min_probability=0)
    completed = adapter._postprocess_raw(partial, 8, ["ame", " is John"], [0.9, 0.8], "stop")
    assert completed["generated_text"] == "Hi my name is John"

    normal = adapter.GenerateParams(text="Maybe we", min_probability=0)
    spaced = adapter._postprocess_raw(normal, 8, [" could", " chat"], [0.9, 0.8], "stop")
    assert spaced["generated_text"] == "Maybe we could chat"

    stopped = adapter.GenerateParams(
        text="Hi i'm bored so looking", min_probability=0, stop_sequences=[" I"],
    )
    matched = adapter._postprocess_raw(stopped, 8, ["I", " was"], [0.9, 0.8], "stop")
    assert matched["generated_text"] == "Hi i'm bored so looking"
    assert matched["stop_reason"] == " I"


@pytest.mark.asyncio
async def test_disabled_vllm_proxy_uses_local_text_inference(monkeypatch):
    calls = []

    def local_inference(generate_params, model_cache):
        calls.append((generate_params.text, model_cache))
        return [{"generated_text": "local result"}]

    cache = object()
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "")
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_fast_inference", local_inference)

    result = await inference_server._run_text_generate(
        GenerateParams(text="hello", max_length=5, min_probability=0),
        cache,
    )

    assert result == [{"generated_text": "local result"}]
    assert calls == [("hello", cache)]


@pytest.mark.asyncio
async def test_text_generate_uses_vllm_adapter_without_local_cache(monkeypatch):
    fake_session = FakeRequestsSession(
        FakeRequestsResponse([{"generated_text": "hello world", "stop_reason": "stop"}])
    )

    def fail_local_inference(*args, **kwargs):
        raise AssertionError("local HF inference should not run when vLLM backend is enabled")

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server, "_fast_inference", fail_local_inference)

    result = await inference_server._run_text_generate(
        GenerateParams(text="hello", max_length=5, min_probability=0),
        model_cache=object(),
        secret="secret-key",
    )

    assert result[0]["generated_text"] == "hello world"
    assert fake_session.calls[0]["url"] == "http://127.0.0.1:8300/api/v1/generate"
    assert fake_session.calls[0]["headers"]["secret"] == "secret-key"
    assert fake_session.calls[0]["headers"]["X-Omniserve-Internal"] == "local"
    assert fake_session.calls[0]["body"]["text"] == "hello"
    assert fake_session.calls[0]["body"]["max_length"] == 5
    assert fake_session.calls[0]["timeout"] >= 180


@pytest.mark.asyncio
async def test_text_generate_vllm_proxy_does_not_wait_for_local_inference_gate(monkeypatch):
    fake_session = FakeRequestsSession(
        FakeRequestsResponse([{"generated_text": "hello world", "stop_reason": "stop"}])
    )

    class EmptyCache:
        def list_models(self):
            return []

    sem = asyncio.Semaphore(1)
    await sem.acquire()
    monkeypatch.setattr(inference_server, "_inference_sem", sem)
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)

    try:
        result = await asyncio.wait_for(
            inference_server._run_text_generate(
                GenerateParams(text="hello", max_length=5, min_probability=0),
                model_cache=EmptyCache(),
            ),
            timeout=0.1,
        )
    finally:
        sem.release()

    assert result[0]["generated_text"] == "hello world"
    assert fake_session.calls[0]["url"] == "http://127.0.0.1:8791/api/v1/generate"


def test_vllm_proxy_retries_transient_connection_failure(monkeypatch):
    fake_session = FakeRequestsSequenceSession([
        requests.ConnectionError("connection refused"),
        FakeRequestsResponse([{"generated_text": "hello world", "stop_reason": "stop"}]),
    ])
    sleeps = []

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_SECONDS", 1.0)
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_INTERVAL", 0.01)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = inference_server._proxy_vllm_generate(
        GenerateParams(text="hello", max_length=5, min_probability=0)
    )

    assert result[0]["generated_text"] == "hello world"
    assert len(fake_session.calls) == 2
    assert sleeps == [pytest.approx(0.01)]


def test_vllm_proxy_waits_through_native_restart_window(monkeypatch):
    fake_session = FakeRequestsSequenceSession([
        requests.ConnectionError("connection refused"),
        requests.ConnectionError("connection refused"),
        requests.ConnectionError("connection refused"),
        requests.ConnectionError("connection refused"),
        FakeRequestsResponse([{"generated_text": "hello world", "stop_reason": "stop"}]),
    ])
    now = [100.0]
    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_SECONDS", 75.0)
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_INTERVAL", 15.0)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(inference_server.time, "sleep", fake_sleep)

    result = inference_server._proxy_vllm_generate(
        GenerateParams(text="hello", max_length=5, min_probability=0)
    )

    assert result[0]["generated_text"] == "hello world"
    assert len(fake_session.calls) == 5
    assert sleeps == [pytest.approx(15.0)] * 4


def test_vllm_proxy_retries_native_model_not_loaded_503(monkeypatch):
    fake_session = FakeRequestsSequenceSession([
        FakeRequestsResponse(
            status_code=503,
            text='{"error":{"message":"no LLM model loaded or configured upstream"}}',
        ),
        FakeRequestsResponse([{"generated_text": "hello world", "stop_reason": "stop"}]),
    ])
    sleeps = []

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_SECONDS", 1.0)
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_INTERVAL", 0.01)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = inference_server._proxy_vllm_generate(
        GenerateParams(text="hello", max_length=5, min_probability=0)
    )

    assert result[0]["generated_text"] == "hello world"
    assert len(fake_session.calls) == 2
    assert sleeps == [pytest.approx(0.01)]


def test_vllm_proxy_retries_native_admission_timeout_503(monkeypatch):
    fake_session = FakeRequestsSequenceSession([
        FakeRequestsResponse(
            status_code=503,
            text='{"error":{"message":"admission timeout; retry","type":"invalid_request_error"}}',
        ),
        FakeRequestsResponse([{"generated_text": "hello world", "stop_reason": "stop"}]),
    ])
    sleeps = []

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_SECONDS", 1.0)
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_INTERVAL", 0.01)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = inference_server._proxy_vllm_generate(
        GenerateParams(text="hello", max_length=5, min_probability=0)
    )

    assert result[0]["generated_text"] == "hello world"
    assert len(fake_session.calls) == 2
    assert sleeps == [pytest.approx(0.01)]


def test_vllm_proxy_retries_native_admission_timeout_json_body(monkeypatch):
    fake_session = FakeRequestsSequenceSession([
        FakeRequestsResponse(
            payload={"error": {"message": "admission timeout; retry", "type": "invalid_request_error"}},
            status_code=503,
        ),
        FakeRequestsResponse([{"generated_text": "hello world", "stop_reason": "stop"}]),
    ])
    sleeps = []

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_SECONDS", 1.0)
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_INTERVAL", 0.01)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = inference_server._proxy_vllm_generate(
        GenerateParams(text="hello", max_length=5, min_probability=0)
    )

    assert result[0]["generated_text"] == "hello world"
    assert len(fake_session.calls) == 2
    assert sleeps == [pytest.approx(0.01)]


def test_vllm_proxy_preserves_503_when_connection_retry_window_elapsed(monkeypatch):
    fake_session = FakeRequestsSession(exc=requests.ConnectionError("connection refused"))

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_SECONDS", 0.0)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)

    with pytest.raises(HTTPException) as exc_info:
        inference_server._proxy_vllm_generate(
            GenerateParams(text="hello", max_length=5, min_probability=0)
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Text generation backend unavailable"
    assert len(fake_session.calls) == 1


@pytest.mark.asyncio
async def test_vllm_cache_eviction_waits_for_active_gpu_inference(monkeypatch):
    local_started = threading.Event()
    release_local = threading.Event()
    events = []

    class DummyCache:
        def list_models(self):
            return ["multimodal_cuda"]

        def unload_all(self, reason):
            events.append(("unload", reason))

    def local_inference():
        local_started.set()
        release_local.wait(timeout=1)
        events.append(("local_done", None))

    def proxy(generate_params, secret=None, timeout=None):
        events.append(("proxy", generate_params.text))
        return [{"generated_text": "ok"}]

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_vllm_text_backend_needs_warmup", lambda: True)
    monkeypatch.setattr(inference_server, "_proxy_vllm_generate", proxy)

    local_task = asyncio.create_task(inference_server._run_gpu_bound(local_inference))
    assert await asyncio.to_thread(local_started.wait, 0.5)
    backend_task = asyncio.create_task(inference_server._run_text_generate(
        GenerateParams(text="hello", max_length=5, min_probability=0),
        DummyCache(),
    ))

    await asyncio.sleep(0.02)
    assert events == []
    release_local.set()
    await local_task
    await backend_task

    assert [event[0] for event in events] == ["local_done", "unload", "proxy"]


def test_chat_completion_proxy_preserves_normalized_messages(monkeypatch):
    fake_session = FakeRequestsSession(
        FakeRequestsResponse({"choices": [{"message": {"content": "ok"}}]})
    )

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)

    params = ChatCompletionParams(
        messages=[ChatMessage(role="user", content="hello")],
        max_tokens=12,
        enable_thinking=False,
    )
    result = inference_server._proxy_vllm_chat_completion(
        params,
        [{"role": "system", "content": "reply briefly"}, {"role": "user", "content": "hello"}],
    )

    assert result["choices"][0]["message"]["content"] == "ok"
    assert fake_session.calls[0]["url"] == "http://127.0.0.1:8300/v1/chat/completions"
    assert fake_session.calls[0]["body"]["messages"] == [
        {"role": "system", "content": "reply briefly"},
        {"role": "user", "content": "hello"},
    ]
    assert fake_session.calls[0]["body"]["max_tokens"] == 12
    assert fake_session.calls[0]["headers"]["X-Omniserve-Internal"] == "local"


@pytest.mark.asyncio
async def test_non_streaming_chat_frees_local_cache_before_vllm_start(monkeypatch):
    events = []

    class DummyCache:
        def list_models(self):
            return ["speech_model"]

        def unload_all(self, reason):
            events.append("unload")

    def proxy(chat_params, messages, secret=None):
        events.append("proxy")
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: DummyCache())
    monkeypatch.setattr(inference_server, "_vllm_text_backend_needs_warmup", lambda: True)
    monkeypatch.setattr(inference_server, "_proxy_vllm_chat_completion", proxy)

    result = await inference_server.chat_completions_route(ChatCompletionParams(
        messages=[ChatMessage(role="user", content="hello")],
        stream=False,
    ))

    assert result["choices"][0]["message"]["content"] == "ok"
    assert events == ["unload", "proxy"]


@pytest.mark.asyncio
async def test_voice_chat_reply_frees_local_cache_before_vllm_start(monkeypatch):
    events = []

    class DummyCache:
        def list_models(self):
            return ["audio_model"]

        def unload_all(self, reason):
            events.append("unload")

    def proxy(chat_params, messages, secret=None):
        events.append("proxy")
        return {"choices": [{"message": {"content": "spoken reply"}}]}

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: DummyCache())
    monkeypatch.setattr(inference_server, "_vllm_text_backend_needs_warmup", lambda: True)
    monkeypatch.setattr(inference_server, "_proxy_vllm_chat_completion", proxy)

    result = await inference_server._generate_voice_chat_reply(
        [{"role": "user", "content": "hello"}],
        20,
        0.7,
        None,
    )

    assert result == "spoken reply"
    assert events == ["unload", "proxy"]


@pytest.mark.asyncio
async def test_streaming_chat_proxies_configured_backend_and_frees_cache(monkeypatch):
    chunks = [b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n', b"data: [DONE]\n\n"]
    fake_response = FakeRequestsResponse(chunks=chunks)
    fake_session = FakeRequestsSession(fake_response)
    events = []

    class DummyCache:
        def list_models(self):
            return ["speech_model"]

        def unload_all(self, reason):
            events.append("unload")

    def fail_local_stream(*args, **kwargs):
        raise AssertionError("local streaming must not run when vLLM is configured")

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: DummyCache())
    monkeypatch.setattr(inference_server, "_vllm_text_backend_needs_warmup", lambda: True)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server, "_chat_inference_streaming", fail_local_stream)

    response = await inference_server.chat_completions_route(ChatCompletionParams(
        messages=[ChatMessage(role="user", content="hello")],
        stream=True,
    ))
    body = b"".join([chunk async for chunk in response.body_iterator])

    assert body == b"".join(chunks)
    assert events == ["unload"]
    assert fake_session.calls[0]["stream"] is True
    assert fake_session.calls[0]["body"]["stream"] is True
    assert fake_response.closed is True


@pytest.mark.parametrize(
    ("backend_exc", "expected_status", "expected_detail"),
    [
        (
            requests.ConnectionError(RemoteDisconnected("Remote end closed connection without response")),
            503,
            "Text generation backend unavailable",
        ),
        (requests.ConnectionError(URLError("connection refused")), 503, "Text generation backend unavailable"),
        (requests.Timeout("timed out"), 504, "Text generation backend timed out"),
    ],
)
def test_vllm_proxy_maps_transport_errors_to_http_exception(
    monkeypatch,
    backend_exc,
    expected_status,
    expected_detail,
):
    fake_session = FakeRequestsSession(exc=backend_exc)

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_CONNECT_RETRY_SECONDS", 0.0)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)

    with pytest.raises(HTTPException) as exc_info:
        inference_server._proxy_vllm_generate(GenerateParams(text="hello", max_length=5, min_probability=0))

    assert exc_info.value.status_code == expected_status
    assert exc_info.value.detail == expected_detail


def test_vllm_proxy_maps_backend_500_to_unavailable(monkeypatch):
    fake_session = FakeRequestsSession(
        FakeRequestsResponse(status_code=500, text="backend exploded", reason="Internal Server Error")
    )

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)

    with pytest.raises(HTTPException) as exc_info:
        inference_server._proxy_vllm_generate(GenerateParams(text="hello", max_length=5, min_probability=0))

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Text generation backend unavailable"


@pytest.mark.asyncio
async def test_feature_extraction_uses_native_backend_without_loading_local_model(monkeypatch):
    fake_session = FakeRequestsSession(FakeRequestsResponse([0.25, -0.5, 0.75]))

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(
        inference_server,
        "_get_model_cache",
        lambda: (_ for _ in ()).throw(AssertionError("local model cache must not load")),
    )

    result = await inference_server._run_feature_extraction(
        FeatureExtractParams(text="hello", num_features=3),
        secret="secret-key",
    )

    assert result == [0.25, -0.5, 0.75]
    assert fake_session.calls[0]["url"] == "http://127.0.0.1:8791/api/v1/feature-extraction"
    assert fake_session.calls[0]["body"] == {"text": "hello", "num_features": 3}
    assert fake_session.calls[0]["headers"]["secret"] == "secret-key"
    assert fake_session.calls[0]["headers"]["X-Omniserve-Internal"] == "local"


@pytest.mark.asyncio
async def test_openai_embeddings_proxies_native_contract(monkeypatch):
    payload = {
        "object": "list",
        "data": [{"object": "embedding", "index": 0, "embedding": [0.25, -0.5]}],
        "model": "omniserve-modernbert",
        "usage": {"prompt_tokens": 1, "total_tokens": 1},
    }
    fake_session = FakeRequestsSession(FakeRequestsResponse(payload))
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)

    result = await inference_server.openai_embeddings(
        inference_server.OpenAIEmbeddingParams(input="hello", dimensions=2),
        secret="secret-key",
    )

    assert result == payload
    assert fake_session.calls[0]["url"] == "http://127.0.0.1:8791/v1/embeddings"
    assert fake_session.calls[0]["body"]["input"] == "hello"
    assert fake_session.calls[0]["body"]["dimensions"] == 2


def test_vllm_readiness_handles_managed_model_status(monkeypatch):
    def fake_urlopen(request, timeout):
        return FakeUrlopenResponse({
            "default": "qwen3.5-4b",
            "models": {
                "qwen3.5-4b": {
                    "managed": True,
                    "running": False,
                    "ready": False,
                }
            },
        })

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server.urllib.request, "urlopen", fake_urlopen)

    assert inference_server._vllm_text_backend_ready() is False


def test_vllm_warmup_unloads_local_model_cache(monkeypatch):
    class DummyCache:
        def __init__(self):
            self.unloaded_reason = None

        def list_models(self):
            return ["gitbase_cuda"]

        def unload_all(self, reason):
            self.unloaded_reason = reason

    def fake_urlopen(request, timeout):
        return FakeUrlopenResponse({
            "managed": True,
            "models": {
                "qwen3.5-4b": {
                    "managed": True,
                    "ready": False,
                }
            },
        })

    cache = DummyCache()
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server.urllib.request, "urlopen", fake_urlopen)

    inference_server._free_local_model_cache_for_vllm(cache)

    assert cache.unloaded_reason == "vLLM text backend warmup"


def test_empty_local_cache_skips_vllm_status_probe(monkeypatch):
    class EmptyCache:
        def list_models(self):
            return []

    monkeypatch.setattr(
        inference_server,
        "_vllm_text_backend_needs_warmup",
        lambda: (_ for _ in ()).throw(AssertionError("empty cache does not need a backend status probe")),
    )

    inference_server._free_local_model_cache_for_vllm(EmptyCache())


def test_vllm_ready_backend_keeps_local_model_cache(monkeypatch):
    class DummyCache:
        def list_models(self):
            return ["gitbase_cuda"]

        def unload_all(self, reason):
            raise AssertionError("ready vLLM backend should not unload local models")

    def fake_urlopen(request, timeout):
        return FakeUrlopenResponse({
            "managed": True,
            "models": {
                "qwen3.5-4b": {
                    "managed": True,
                    "ready": True,
                }
            },
        })

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server.urllib.request, "urlopen", fake_urlopen)

    inference_server._free_local_model_cache_for_vllm(DummyCache())


def test_vllm_adapter_maps_managed_startup_failure_to_503(monkeypatch):
    from questions.inference_server import vllm_parity_adapter

    class FailingRegistry:
        def ensure(self, model=None):
            raise RuntimeError("backend exited during startup (code 1)")

    monkeypatch.setattr(vllm_parity_adapter, "REGISTRY", FailingRegistry())

    with pytest.raises(HTTPException) as exc_info:
        vllm_parity_adapter._ensure_backend("gemma-roleplay-v2")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Text generation backend unavailable"


@pytest.mark.asyncio
async def test_vllm_autocomplete_timeout_returns_empty_completion(monkeypatch):
    def ready():
        return True

    async def slow_to_thread(func, *args, **kwargs):
        if func is ready:
            return True
        await asyncio.sleep(0.02)

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "AUTOCOMPLETE_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(inference_server, "_vllm_text_backend_ready", ready)
    monkeypatch.setattr(asyncio, "to_thread", slow_to_thread)
    monkeypatch.setattr(inference_server, "_deep_liveness_vram_status", lambda: (True, None))

    result = await inference_server._run_autocomplete_inference(
        inference_server.AutocompleteParams(text="hello", max_length=5, min_probability=0),
        model_cache=object(),
    )
    await asyncio.sleep(0.05)

    assert result == [{
        "generated_text": "hello",
        "stop_reason": "timeout",
        "thinking_content": None,
    }]


@pytest.mark.asyncio
async def test_vllm_autocomplete_uses_short_backend_timeout(monkeypatch):
    fake_session = FakeRequestsSession(
        FakeRequestsResponse([{"generated_text": "ok", "stop_reason": "stop"}])
    )

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "AUTOCOMPLETE_TIMEOUT_SECONDS", 0.25)
    monkeypatch.setattr(inference_server, "_vllm_text_backend_ready", lambda: True)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)

    result = await inference_server._run_autocomplete_inference(
        inference_server.AutocompleteParams(text="hello", max_length=5, min_probability=0),
        model_cache=object(),
    )

    assert result[0]["generated_text"] == "ok"
    assert fake_session.calls[0]["timeout"] == 0.25


@pytest.mark.asyncio
async def test_vllm_autocomplete_backend_timeout_returns_empty_completion(monkeypatch):
    fake_session = FakeRequestsSession(exc=requests.Timeout("timed out"))

    calls = []

    def fake_fast_inference(generate_params, model_cache):
        calls.append(generate_params.text)
        return [{"generated_text": "local ok", "stop_reason": "stop"}]

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_vllm_text_backend_ready", lambda: True)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server, "_fast_inference", fake_fast_inference)
    monkeypatch.setattr(inference_server, "_deep_liveness_vram_status", lambda: (True, None))

    result = await inference_server._run_autocomplete_inference(
        inference_server.AutocompleteParams(text="hello", max_length=5, min_probability=0),
        model_cache=object(),
    )

    assert calls == []
    assert result == [{
        "generated_text": "hello",
        "stop_reason": "backend_unavailable",
        "thinking_content": None,
    }]


@pytest.mark.asyncio
async def test_vllm_autocomplete_fallback_failure_returns_empty_completion(monkeypatch):
    fake_session = FakeRequestsSession(exc=requests.Timeout("timed out"))

    def fail_fast_inference(generate_params, model_cache):
        raise RuntimeError("cuda out of memory")

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_vllm_text_backend_ready", lambda: True)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server, "_fast_inference", fail_fast_inference)
    monkeypatch.setattr(inference_server, "_deep_liveness_vram_status", lambda: (True, None))

    result = await inference_server._run_autocomplete_inference(
        inference_server.AutocompleteParams(text="hello", max_length=5, min_probability=0),
        model_cache=object(),
    )

    assert result == [{
        "generated_text": "hello",
        "stop_reason": "backend_unavailable",
        "thinking_content": None,
    }]


@pytest.mark.asyncio
async def test_vllm_autocomplete_skips_local_fallback(monkeypatch):
    fake_session = FakeRequestsSession(exc=requests.Timeout("timed out"))

    def fail_fast_inference(generate_params, model_cache):
        raise AssertionError("local fallback should not run when VRAM is low")

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_vllm_text_backend_ready", lambda: True)
    monkeypatch.setattr(inference_server, "_get_vllm_session", lambda: fake_session)
    monkeypatch.setattr(inference_server, "_fast_inference", fail_fast_inference)
    monkeypatch.setattr(
        inference_server,
        "_deep_liveness_vram_status",
        lambda: (_ for _ in ()).throw(AssertionError("VRAM check should not run")),
    )

    result = await inference_server._run_autocomplete_inference(
        inference_server.AutocompleteParams(text="hello", max_length=5, min_probability=0),
        model_cache=object(),
    )

    assert result == [{
        "generated_text": "hello",
        "stop_reason": "backend_unavailable",
        "thinking_content": None,
    }]


@pytest.mark.asyncio
async def test_vllm_autocomplete_not_ready_returns_empty_completion(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise AssertionError("autocomplete generation should not run when backend is not ready")

    def fail_fast_inference(*args, **kwargs):
        raise AssertionError("local fallback should not run when vLLM is configured")

    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8300")
    monkeypatch.setattr(inference_server, "_vllm_text_backend_ready", lambda: False)
    monkeypatch.setattr(inference_server.urllib.request, "urlopen", fail_urlopen)
    monkeypatch.setattr(inference_server, "_fast_inference", fail_fast_inference)

    result = await inference_server._run_autocomplete_inference(
        inference_server.AutocompleteParams(text="hello", max_length=5, min_probability=0),
        model_cache=object(),
    )

    assert result == [{
        "generated_text": "hello",
        "stop_reason": "backend_unavailable",
        "thinking_content": None,
    }]


@pytest.mark.asyncio
async def test_proxied_chat_does_not_wait_for_local_inference_gate(monkeypatch):
    chunks = [b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n', b"data: [DONE]\n\n"]

    class EmptyCache:
        def list_models(self):
            return []

    def proxy(chat_params, messages, secret=None):
        return {"choices": [{"message": {"content": "ok"}}]}

    sem = asyncio.Semaphore(1)
    await sem.acquire()
    monkeypatch.setattr(inference_server, "_inference_sem", sem)
    monkeypatch.setattr(inference_server, "_vllm_proxy_sem", None)
    monkeypatch.setattr(inference_server, "VLLM_TEXT_BACKEND_BASE", "http://127.0.0.1:8791")
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: EmptyCache())
    monkeypatch.setattr(inference_server, "_get_vllm_session",
                        lambda: FakeRequestsSession(FakeRequestsResponse(chunks=chunks)))
    monkeypatch.setattr(inference_server, "_proxy_vllm_chat_completion", proxy)

    try:
        streamed = await asyncio.wait_for(inference_server.chat_completions_route(ChatCompletionParams(
            messages=[ChatMessage(role="user", content="hello")], stream=True)), timeout=0.5)
        body = b"".join([chunk async for chunk in streamed.body_iterator])
        result = await asyncio.wait_for(inference_server.chat_completions_route(ChatCompletionParams(
            messages=[ChatMessage(role="user", content="hello")], stream=False)), timeout=0.5)
    finally:
        sem.release()

    assert body == b"".join(chunks)
    assert result["choices"][0]["message"]["content"] == "ok"
