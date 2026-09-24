import numpy as np
import pytest
from fastapi import BackgroundTasks
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


def test_audio_process_rejects_untokenizable_kokoro_input(monkeypatch):
    voicepacks = {"af_nicole": "nicole-pack"}

    class DummyCache:
        def add_or_get(self, name, loader):
            return "model", voicepacks

    def fake_generate_full(model, text, voicepack, lang, speed):
        return None

    monkeypatch.setattr(inference_server, "_get_model_cache", lambda: DummyCache())
    monkeypatch.setattr(
        inference_server,
        "_get_kokoro_runtime",
        lambda: (None, fake_generate_full, None),
    )

    with pytest.raises(ValueError, match="could not be tokenized"):
        inference_server.audio_process("...", voice="af_nicole")


@pytest.mark.asyncio
async def test_openai_audio_speech_returns_400_for_untokenizable_kokoro_input(monkeypatch):
    async def fake_run_tts(func, *args, **kwargs):
        raise ValueError("Speech input could not be tokenized for the selected voice.")

    monkeypatch.setattr(inference_server, "request_authorized", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(inference_server, "_run_tts", fake_run_tts)
    monkeypatch.setattr(inference_server, "API_KEY", "test-api-key")

    params = inference_server.OpenAISpeechParams(
        model="tts-1",
        input="...",
        voice="af_nicole",
        response_format="wav",
    )

    with pytest.raises(inference_server.HTTPException) as exc_info:
        await inference_server.openai_audio_speech(
            params,
            BackgroundTasks(),
            _request("/v1/audio/speech"),
            "test-secret",
        )

    assert exc_info.value.status_code == 400
    assert "could not be tokenized" in exc_info.value.detail


@pytest.mark.asyncio
async def test_generate_speech_runs_synthesis_off_event_loop(monkeypatch):
    calls = []

    async def fake_run_tts(func, *args, **kwargs):
        calls.append((func.__name__, args, kwargs))
        return b"RIFF-test-wav"

    monkeypatch.setattr(inference_server, "request_authorized", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(inference_server, "_run_tts", fake_run_tts)
    monkeypatch.setattr(inference_server, "API_KEY", "test-api-key")

    params = inference_server.GenerateSpeechParams(
        text="hello",
        voice="M1",
        speed=1.0,
        language="en",
        steps=4,
    )

    response = await inference_server.generate_speech(
        params,
        BackgroundTasks(),
        _request("/api/v1/generate_speech"),
        Response(),
        "test-secret",
    )

    assert response.body == b"RIFF-test-wav"
    assert response.media_type == "audio/wav"
    assert calls == [
        (
            "_synthesize_legacy_speech_wav",
            ("hello", "M1", 1.0),
            {"language": "en", "steps": 4},
        )
    ]


@pytest.mark.parametrize("fmt,media,magic", [("mp3", "audio/mpeg", b"\xff"), ("opus", "audio/ogg", b"OggS"), ("wav", "audio/wav", b"RIFF")])
def test_encode_audio_honors_response_format(fmt, media, magic):
    import numpy as np

    audio = (np.sin(np.arange(44100) / 20) * 0.3).astype(np.float32)
    data, got_media = inference_server._encode_audio(audio, 44100, fmt)
    assert got_media == media
    assert data[:len(magic)] == magic or (fmt == "mp3" and data[:3] == b"ID3")


def test_tts_synthesize_falls_back_to_cpu_when_gpu_down(monkeypatch):
    import numpy as np

    monkeypatch.setattr(inference_server, "_tts_gpu_synthesize", lambda *a, **k: None)
    monkeypatch.setattr(inference_server, "audio_process", lambda text, voice, *a, **k: (24000, np.zeros(10, np.float32)))
    rate, audio = inference_server.tts_synthesize("hello", "af")
    assert rate == 24000 and len(audio) == 10
