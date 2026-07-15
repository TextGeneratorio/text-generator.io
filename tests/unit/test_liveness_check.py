import json

import pytest

from questions.inference_server import inference_server


class DummyModelCache:
    def list_models(self):
        return []


@pytest.mark.asyncio
async def test_deep_liveness_skips_inference_when_vram_is_low(monkeypatch):
    calls = []

    async def fake_run_gpu_bound(*args, **kwargs):
        calls.append((args, kwargs))
        return [{"generated_text": "ok"}]

    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: DummyModelCache())
    monkeypatch.setattr(
        inference_server,
        "_deep_liveness_vram_status",
        lambda: (False, {"total": 32, "used": 31.9, "free": 0.1, "reserved": 0, "allocated": 0}),
    )
    monkeypatch.setattr(inference_server, "_run_gpu_bound", fake_run_gpu_bound)

    response = await inference_server.liveness_check(request=None, deep=1)
    body = json.loads(response.body)

    assert response.status_code == 200
    assert body["inference"] == "ok"
    assert body["deep_check"] == "skipped_low_vram"
    assert body["gpu_memory"]["free"] == 0.1
    assert calls == []


@pytest.mark.asyncio
async def test_deep_liveness_runs_inference_when_vram_is_available(monkeypatch):
    calls = []

    async def fake_run_gpu_bound(*args, **kwargs):
        calls.append((args, kwargs))
        return [{"generated_text": "ok"}]

    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: DummyModelCache())
    monkeypatch.setattr(inference_server, "_deep_liveness_vram_status", lambda: (True, {"free": 32}))
    monkeypatch.setattr(inference_server, "_run_gpu_bound", fake_run_gpu_bound)

    response = await inference_server.liveness_check(request=None, deep=1)
    body = json.loads(response.body)

    assert response.status_code == 200
    assert body["deep_check"] == "ok"
    assert len(calls) == 1
