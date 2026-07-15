import numpy as np
import pytest
from starlette.requests import Request
from starlette.responses import Response

from questions.inference_server import inference_server


def _request(path):
    return Request({
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
        "server": ("127.0.0.1", 9080),
        "scheme": "http",
    })


def test_partner_secret_authorizes_service_proxy(monkeypatch):
    monkeypatch.setattr(inference_server, "NETWRCK_PARTNER_SECRET", "partner-key")
    monkeypatch.setattr(inference_server, "API_KEY", None)

    assert inference_server.request_authorized(_request("/api/v1/generate_speech"), "partner-key")


@pytest.mark.asyncio
async def test_partner_stt_request_skips_subscriber_lookup_and_billing(monkeypatch):
    monkeypatch.setattr(inference_server, "NETWRCK_PARTNER_SECRET", "partner-key")
    monkeypatch.setattr(inference_server, "API_KEY", None)
    monkeypatch.setattr(
        inference_server,
        "_user_has_subscription_or_credits",
        lambda *_args, **_kwargs: pytest.fail("partner request queried subscriber billing"),
    )
    monkeypatch.setattr(
        inference_server,
        "_consume_user_credits",
        lambda *_args, **_kwargs: pytest.fail("partner request consumed subscriber credits"),
    )
    monkeypatch.setattr(
        inference_server,
        "fast_audio_extract_inference",
        lambda _params: {"segments": [], "text": "ok"},
    )
    params = inference_server.AudioParams(
        audio_url="https://example.com/audio.wav",
        output_filetype="txt",
    )

    result = await inference_server.audio_extract_shared(
        None,
        params,
        _request("/api/v1/audio-extraction"),
        Response(),
        "partner-key",
    )

    assert result["text"] == "ok"


def test_normalize_kokoro_voice_accepts_legacy_aliases():
    voicepacks = {
        "am_adam": object(),
        "am_michael": object(),
        "bm_lewis": object(),
        "af_bella": object(),
        "af_sarah": object(),
    }

    assert inference_server.normalize_kokoro_voice("Male fast", voicepacks) == "am_adam"
    assert inference_server.normalize_kokoro_voice("Male default", voicepacks) == "am_michael"
    assert inference_server.normalize_kokoro_voice("Male slower", voicepacks) == "bm_lewis"
    assert inference_server.normalize_kokoro_voice("Female 1", voicepacks) == "af_bella"
    assert inference_server.normalize_kokoro_voice("Female 2", voicepacks) == "af_sarah"


def test_normalize_kokoro_voice_rejects_unknown_instead_of_falling_back():
    with pytest.raises(ValueError, match="Unsupported Kokoro voice"):
        inference_server.normalize_kokoro_voice("not-a-real-voice", {"af_nicole": object()})


def test_audio_process_passes_requested_voicepack(monkeypatch):
    voicepacks = {"am_adam": "adam-pack", "af_nicole": "nicole-pack"}
    captured = {}

    class DummyCache:
        def add_or_get(self, name, loader):
            return "model", voicepacks

    def fake_generate_full(model, text, voicepack, lang, speed):
        captured.update({"model": model, "text": text, "voicepack": voicepack, "lang": lang, "speed": speed})
        return np.ones(8, dtype=np.float32), []

    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: DummyCache())
    monkeypatch.setattr(
        inference_server,
        "_get_kokoro_runtime",
        lambda: (None, fake_generate_full, None),
    )
    monkeypatch.setattr(inference_server, "_optimize_generated_audio", lambda audio, sample_rate=24000: audio)

    rate, audio = inference_server.audio_process("hello", voice="Male fast", speed=1.25)

    assert rate == 24000
    assert audio.shape[0] == 8
    assert captured == {
        "model": "model",
        "text": "hello",
        "voicepack": "adam-pack",
        "lang": "a",
        "speed": 1.25,
    }
