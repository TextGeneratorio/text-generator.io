import asyncio

import pytest

from questions.inference_server import inference_server


@pytest.mark.asyncio
async def test_autocomplete_waits_for_shared_gpu_warmup(monkeypatch):
    monkeypatch.setattr(inference_server, "_inference_sem", None)
    monkeypatch.setattr(inference_server, "_autocomplete_sem", None)
    monkeypatch.setattr(inference_server, "AUTOCOMPLETE_QUEUE_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setattr(inference_server, "AUTOCOMPLETE_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(inference_server, "validate_generate_params", lambda _: None)
    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: object())

    gpu_sem = inference_server._get_inference_sem()
    await gpu_sem.acquire()

    async def release_warmup_gate():
        await asyncio.sleep(0.05)
        gpu_sem.release()

    warmup = asyncio.create_task(release_warmup_gate())

    calls = []

    def fake_fast_inference(generate_params, model_cache):
        calls.append(generate_params.text)
        return [{"generated_text": "ok", "stop_reason": "stop"}]

    monkeypatch.setattr(inference_server, "_fast_inference", fake_fast_inference)

    response = await inference_server.autocomplete_route(
        inference_server.AutocompleteParams(text="hello")
    )

    await warmup
    assert calls == ["hello"]
    assert response[0]["generated_text"] == "ok"
