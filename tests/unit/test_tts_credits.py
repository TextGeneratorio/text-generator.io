from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app
from questions.credits import estimate_appnz_tts_credits

client = TestClient(app)


def test_estimate_appnz_tts_credits_has_minimum():
    assert estimate_appnz_tts_credits("appnz-tts", "hi") >= 1
    assert estimate_appnz_tts_credits("pocket-tts", "hi") >= 1
    assert estimate_appnz_tts_credits("appnz-tts", "x" * 900) >= estimate_appnz_tts_credits("pocket-tts", "x" * 900)


def test_credits_balance_requires_auth():
    response = client.get("/api/credits/balance")
    assert response.status_code == 401


def test_credits_balance_returns_autotopup(monkeypatch):
    user = MagicMock()
    user.stripe_id = "cus_test"
    user.free_credits = 0

    with (
        patch("main.get_current_user", return_value=user),
        patch("main.get_stripe_credit_balance_cents", return_value=250),
        patch("main.get_autotopup_settings", return_value={"enabled": False, "threshold": 100, "amount": 500, "hasCard": False}),
    ):
        response = client.get("/api/credits/balance")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["balance"]["total"] == 250
    assert body["unit_cents"] == 1
    assert body["autotopup"]["threshold"] == 100


def test_credits_autotopup_persists_settings():
    user = MagicMock()
    user.stripe_id = "cus_test"

    with (
        patch("main.get_current_user", return_value=user),
        patch("main.set_autotopup_settings", return_value={"enabled": True, "threshold": 50, "amount": 200, "hasCard": True}) as mock_set,
        patch("main.get_stripe_credit_balance_cents", return_value=40),
    ):
        response = client.post(
            "/api/credits/autotopup",
            json={"enabled": True, "threshold": 50, "amount": 200},
        )

    assert response.status_code == 200
    mock_set.assert_called_once()
    assert response.json()["autotopup"]["enabled"] is True


def test_text_to_speech_tool_requires_login():
    response = client.post(
        "/api/tools/text-to-speech/generate",
        json={"model": "appnz-tts", "input": "hello", "voice": "eve"},
    )
    assert response.status_code == 401


def test_text_to_speech_tool_requires_credits():
    user = MagicMock()
    user.stripe_id = "cus_test"
    user.free_credits = 0

    with (
        patch("main.get_current_user", return_value=user),
        patch("main.check_user_subscription", create=True),
        patch("questions.subscription_utils.check_user_subscription", return_value=False),
        patch("main.get_stripe_credit_balance_cents", return_value=0),
    ):
        response = client.post(
            "/api/tools/text-to-speech/generate",
            json={"model": "appnz-tts", "input": "hello from text generator", "voice": "eve"},
        )

    assert response.status_code == 402


def test_text_to_speech_tool_proxies_and_charges(monkeypatch):
    user = MagicMock()
    user.stripe_id = "cus_test"
    user.free_credits = 100

    upstream = MagicMock()
    upstream.status_code = 200
    upstream.ok = True
    upstream.content = b"ID3fake-mp3"
    upstream.headers = {"content-type": "audio/mpeg"}

    with (
        patch("main.get_current_user", return_value=user),
        patch("questions.subscription_utils.check_user_subscription", return_value=False),
        patch("main.get_stripe_credit_balance_cents", return_value=100),
        patch("main.appnz_api_key", return_value="app-test"),
        patch("main.requests.post", return_value=upstream) as mock_post,
        patch("main._consume_user_api_credits", return_value=97) as mock_consume,
    ):
        response = client.post(
            "/api/tools/text-to-speech/generate",
            json={"model": "pocket-tts", "input": "hello from text generator", "voice": "alba"},
        )

    assert response.status_code == 200
    assert response.content == b"ID3fake-mp3"
    assert response.headers["x-credits-charged"]
    mock_post.assert_called_once()
    mock_consume.assert_called_once()


def test_tts_studio_shows_credit_topup_controls():
    response = client.get("/text-to-speech")
    assert response.status_code == 200
    assert 'id="tts-credit-balance"' in response.text
    assert 'id="tts-topup"' in response.text
    assert "tts-app-key" not in response.text
    assert "TG credits" in response.text


def test_tts_studio_skips_auth_probes_for_crawlers():
    source = Path("static/js/text-to-speech-studio.js").read_text(encoding="utf-8")

    assert "if (!window.skip_auth_hydration)" in source
    assert "if (!window.skip_auth_hydration && new URLSearchParams" in source
