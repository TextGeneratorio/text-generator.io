import pytest
from fastapi import HTTPException
from starlette.responses import Response

from questions.inference_server import inference_server
from questions.models import AudioParams


class DummyUploadFile:
    async def read(self):
        return b"RIFF....WAVEfmt "


@pytest.mark.asyncio
async def test_openai_audio_transcriptions_reports_missing_stt_config(monkeypatch):
    monkeypatch.setattr(inference_server, "STT_BACKEND", "gemini")
    monkeypatch.setattr(inference_server, "request_authorized", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(inference_server, "_gemini_stt_api_key", lambda: "")

    with pytest.raises(HTTPException) as exc_info:
        await inference_server.openai_audio_transcriptions(
            background_tasks=None,
            request=object(),
            response=None,
            file=DummyUploadFile(),
            model="whisper-1",
            response_format="json",
            language=None,
            translate=False,
            secret="test-secret",
        )

    assert exc_info.value.status_code == 424
    assert exc_info.value.detail == "Transcription backend is not configured"


def test_multimodal_transcription_does_not_fallback_when_stt_config_missing(monkeypatch):
    monkeypatch.setattr(inference_server, "STT_BACKEND", "gemini")
    monkeypatch.setattr(inference_server, "_gemini_stt_api_key", lambda: "")

    with pytest.raises(inference_server.MissingSTTBackendConfig):
        inference_server._transcribe_audio_with_multimodal_model(
            audio_bytes=b"RIFF....WAVEfmt ",
            source_name=None,
            translate_to_english=False,
            include_segments=False,
        )


def test_gemini_transcription_sends_key_in_header_not_url(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "hello"}]}}]}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(inference_server, "_gemini_stt_api_key", lambda: "test-key")
    monkeypatch.setattr("requests.post", fake_post)

    result = inference_server._transcribe_audio_with_gemini(b"RIFF....WAVEfmt ", False)

    assert result["text"] == "hello"
    assert "test-key" not in captured["url"]
    assert captured["headers"] == {"x-goog-api-key": "test-key"}


def test_missing_user_log_does_not_disclose_secret(monkeypatch, caplog):
    class Database:
        def close(self):
            return None

    secret = "credential-that-must-not-be-logged"
    inference_server.session_dict.pop(secret, None)
    monkeypatch.setattr(inference_server, "get_db_session_sync", Database)
    monkeypatch.setattr(inference_server.User, "get_by_secret", lambda _db, _secret: None)

    assert inference_server.user_secret_matches(secret) is None
    assert secret not in caplog.text


def test_audio_url_download_failure_is_client_error(monkeypatch):
    class FailedDownload:
        def result(self):
            raise RuntimeError("name resolution failed")

    monkeypatch.setattr(inference_server, "request_get", lambda _url: FailedDownload())

    params = AudioParams(
        audio_url="https://nonexistent.example.com/audio.wav",
        translate_to_english=False,
        output_filetype="txt",
    )

    with pytest.raises(HTTPException) as exc_info:
        inference_server._load_audio_bytes(params)

    assert exc_info.value.status_code == 400
    assert "Failed to download audio file" in exc_info.value.detail


@pytest.mark.asyncio
async def test_audio_extract_shared_preserves_http_exception(monkeypatch):
    monkeypatch.setattr(inference_server, "API_KEY", "test-api-key")
    monkeypatch.setattr(
        inference_server,
        "fast_audio_extract_inference",
        lambda _params: (_ for _ in ()).throw(HTTPException(status_code=400, detail="bad audio url")),
    )

    params = AudioParams(
        audio_url="https://nonexistent.example.com/audio.wav",
        translate_to_english=False,
        output_filetype="txt",
    )

    with pytest.raises(HTTPException) as exc_info:
        await inference_server.audio_extract_shared(
            None,
            params,
            None,
            Response(),
            "test-secret",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "bad audio url"
