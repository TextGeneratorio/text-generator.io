import numpy as np
from starlette.testclient import TestClient

import questions.inference_server.inference_server as inference_server


ORIGIN = "https://text-generator.io"


def _client(monkeypatch):
    monkeypatch.setattr(inference_server, "request_authorized", lambda request, secret: True)
    monkeypatch.setattr(inference_server, "track_stripe_request_usage", lambda **kwargs: None)
    return TestClient(inference_server.app, raise_server_exceptions=False)


def test_generate_speech_preflight_allows_text_generator_origin(monkeypatch):
    client = _client(monkeypatch)

    response = client.options(
        "/api/v1/generate_speech",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,secret",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "secret" in response.headers["access-control-allow-headers"]


def test_generate_speech_from_text_generator_origin_returns_wav_with_cors(monkeypatch):
    captured = {}

    def fake_audio_process(text, voice, speed, language="en", steps=4):
        captured.update({"text": text, "voice": voice, "speed": speed, "language": language, "steps": steps})
        return 24000, np.zeros(240, dtype=np.float32)

    monkeypatch.setattr(inference_server, "audio_process", fake_audio_process)
    client = _client(monkeypatch)

    response = client.post(
        "/api/v1/generate_speech",
        headers={"Origin": ORIGIN, "secret": "test-secret"},
        json={"text": "Hey hows it going", "voice": "M1", "language": "en", "speed": 1, "steps": 4},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["content-disposition"] == "attachment; filename=audio.wav"
    assert response.content.startswith(b"RIFF")
    assert captured == {"text": "Hey hows it going", "voice": "M1", "speed": 1.0, "language": "en", "steps": 4}


def test_generate_speech_synthesis_failure_keeps_cors_header(monkeypatch):
    def broken_audio_process(*args, **kwargs):
        raise RuntimeError("model import failed")

    monkeypatch.setattr(inference_server, "audio_process", broken_audio_process)
    client = _client(monkeypatch)

    response = client.post(
        "/api/v1/generate_speech",
        headers={"Origin": ORIGIN, "secret": "test-secret"},
        json={"text": "Hey hows it going", "voice": "M1", "language": "en", "speed": 1, "steps": 4},
    )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.json() == {"detail": "Speech synthesis failed. Please try again."}
