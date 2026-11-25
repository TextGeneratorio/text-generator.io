"""TEXTGEN_AUTH_MODE gate: modes, credential types and the rejection cases.

Runs without models, a database or network: paying-user lookups are a stub.
"""
import logging

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from questions import omniserve_paywall, textgen_auth

PAID = "paid-user-secret-0000000000000001"
CREDITS = "credit-user-secret-00000000000002"
FREE = "free-user-secret-0000000000000003"
INTERNAL = "internal-service-key-000000000004"


def fake_paid_check(credential):
    return {PAID: "sub", CREDITS: "paid", FREE: False}.get(credential)


def build_app(paid_check=fake_paid_check, **gate_kwargs):
    app = FastAPI()
    omniserve_paywall.install(app)

    @app.post("/api/v1/generate")
    async def generate(request: Request):
        params = type("P", (), {"max_length": 200, "number_of_results": 3})()
        decision = textgen_auth.gate(request, "/api/v1/generate", paid_check, **gate_kwargs)
        textgen_auth.clamp_max_length(params, decision)
        return {
            "ok": True,
            "reason": decision.reason if decision else None,
            "max_length": params.max_length,
            "number_of_results": params.number_of_results,
        }

    return app


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for name in ("TEXTGEN_AUTH_MODE", "TEXTGEN_INTERNAL_API_KEYS", "TEXTGEN_INTERNAL_API_KEYS_FILE",
                 "TEXTGEN_TOKEN_SECRET", "TEXTGEN_FREE_ORIGINS", "TEXTGEN_FREE_RPM", "TEXTGEN_FREE_MAX_LENGTH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TEXTGEN_INTERNAL_API_KEYS", f"netwrck:{INTERNAL}")
    monkeypatch.setenv("TEXTGEN_TOKEN_SECRET", "token-secret-for-tests")
    textgen_auth.free_limiter.reset()
    yield
    textgen_auth.free_limiter.reset()


def post(client, headers=None):
    return client.post("/api/v1/generate", json={"text": "hi"}, headers=headers or {})


# --- modes -------------------------------------------------------------------

def test_default_mode_is_warn(monkeypatch):
    assert textgen_auth.auth_mode() == "warn"
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "bogus")
    assert textgen_auth.auth_mode() == "warn"


def test_off_mode_serves_everything_without_checks(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "off")

    def boom(_):
        raise AssertionError("paid_check must not run in off mode")

    r = post(TestClient(build_app(paid_check=boom)), {"secret": "whatever"})
    assert r.status_code == 200 and r.json()["reason"] is None


def test_warn_mode_serves_but_logs_would_reject(monkeypatch, caplog):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "warn")
    client = TestClient(build_app())
    with caplog.at_level(logging.WARNING, logger="textgen_auth"):
        r = post(client)
        r2 = post(client, {"secret": FREE})
    assert r.status_code == 200 and r.json()["reason"] == "warn:missing_credential"
    assert r2.status_code == 200 and r2.json()["reason"] == "warn:not_subscribed"
    lines = [rec.getMessage() for rec in caplog.records]
    assert any("would_reject" in l and "status=401" in l and "endpoint=/api/v1/generate" in l for l in lines)
    assert any("would_reject" in l and "status=402" in l for l in lines)
    assert not any(FREE in l for l in lines), "credentials must never be logged"


def test_enforce_rejects_missing_credential_with_401_json(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = post(TestClient(build_app()))
    assert r.status_code == 401
    body = r.json()
    assert body["error"]["code"] == "authentication_required"
    assert "subscribe_url" in body["error"]


def test_enforce_rejects_unknown_key_401(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    assert post(TestClient(build_app()), {"secret": "not-a-real-key-123456"}).status_code == 401


def test_enforce_rejects_free_account_402(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = post(TestClient(build_app()), {"secret": FREE})
    assert r.status_code == 402
    assert r.json()["error"]["code"] == "subscription_required"


# --- credential types ----------------------------------------------------------

@pytest.mark.parametrize("headers", [
    {"secret": PAID},
    {"Authorization": f"Bearer {PAID}"},
    {"X-API-Key": PAID},
    {"secret": CREDITS},
])
def test_enforce_existing_paying_user_keys_keep_working(monkeypatch, headers):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = post(TestClient(build_app()), headers)
    assert r.status_code == 200
    assert r.json()["reason"] == "paid_key"
    assert r.json()["max_length"] == 200  # paying users are never clamped


def test_rapid_api_header_is_not_a_free_pass(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    assert post(TestClient(build_app()), {"X-Rapid-API-Key": "YHWEFVNWHXIWNGVSH"}).status_code == 401


def test_internal_service_key_accepted_and_logged_by_name(monkeypatch, caplog):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    with caplog.at_level(logging.INFO, logger="textgen_auth"):
        r = post(TestClient(build_app()), {"Authorization": f"Bearer {INTERNAL}"})
    assert r.status_code == 200 and r.json()["reason"] == "internal_key"
    assert any("caller=internal:netwrck" in rec.getMessage() for rec in caplog.records)
    assert not any(INTERNAL in rec.getMessage() for rec in caplog.records)


def test_internal_keys_file(monkeypatch, tmp_path):
    keys = tmp_path / "keys"
    keys.write_text("# comment\nringnz:ringnz-service-key-0000000001\n")
    monkeypatch.setenv("TEXTGEN_INTERNAL_API_KEYS", "")
    monkeypatch.setenv("TEXTGEN_INTERNAL_API_KEYS_FILE", str(keys))
    assert textgen_auth.internal_key_name("ringnz-service-key-0000000001") == "ringnz"
    assert textgen_auth.internal_key_name(INTERNAL) is None


def test_short_internal_keys_are_ignored(monkeypatch):
    monkeypatch.setenv("TEXTGEN_INTERNAL_API_KEYS", "x:short")
    assert textgen_auth.internal_key_name("short") is None


def test_signed_token_accepted(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    token = textgen_auth.mint_token("netwrck-user-42", ttl_s=300)
    r = post(TestClient(build_app()), {"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json()["reason"] == "signed_token"


def test_expired_token_rejected(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    import time

    token = textgen_auth.mint_token("u", ttl_s=60, now=time.time() - 3600)
    assert textgen_auth.verify_token(token) == (None, "token_expired")
    assert post(TestClient(build_app()), {"Authorization": f"Bearer {token}"}).status_code == 401


def test_tampered_or_foreign_token_rejected(monkeypatch):
    token = textgen_auth.mint_token("u", ttl_s=60)
    head, sig = token.rsplit(".", 1)
    assert textgen_auth.verify_token(head.replace(".u", ".admin") + "." + sig)[1] == "token_bad_signature"
    other = textgen_auth.mint_token("u", ttl_s=60, secret="some-other-secret")
    assert textgen_auth.verify_token(other)[1] == "token_bad_signature"


def test_token_ttl_is_capped():
    token = textgen_auth.mint_token("u", ttl_s=10 ** 9)
    exp = int(token.split(".")[1])
    import time

    assert exp <= time.time() + textgen_auth.MAX_TOKEN_TTL_S + 1


# --- free tier ---------------------------------------------------------------

def test_free_tier_for_allowlisted_origin_is_clamped(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = post(TestClient(build_app()), {"Origin": "https://text-generator.io"})
    assert r.status_code == 200
    assert r.json()["reason"] == "free_tier:missing_credential"
    assert r.json()["max_length"] == 64 and r.json()["number_of_results"] == 1


def test_free_tier_referer_counts_as_origin(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = post(TestClient(build_app()), {"Referer": "https://text-generator.io/questions-game"})
    assert r.status_code == 200


def test_wrong_origin_rejected(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    client = TestClient(build_app())
    assert post(client, {"Origin": "https://evil.example"}).status_code == 401
    assert post(client, {"Origin": "https://text-generator.io.evil.example"}).status_code == 401


def test_free_tier_rate_limited_429(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    monkeypatch.setenv("TEXTGEN_FREE_RPM", "2")
    client = TestClient(build_app())
    h = {"Origin": "https://text-generator.io", "CF-Connecting-IP": "203.0.113.9"}
    assert post(client, h).status_code == 200
    assert post(client, h).status_code == 200
    r = post(client, h)
    assert r.status_code == 429 and r.headers.get("retry-after") == "60"
    # a different client IP has its own budget
    assert post(client, {**h, "CF-Connecting-IP": "203.0.113.10"}).status_code == 200


def test_free_tier_disabled(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    monkeypatch.setenv("TEXTGEN_FREE_RPM", "0")
    assert post(TestClient(build_app()), {"Origin": "https://text-generator.io"}).status_code == 401


def test_free_tier_not_offered_when_disallowed(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    client = TestClient(build_app(allow_free_tier=False))
    assert post(client, {"Origin": "https://text-generator.io"}).status_code == 401


def test_free_account_from_our_site_falls_back_to_free_tier(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = post(TestClient(build_app()), {"secret": FREE, "Origin": "https://text-generator.io"})
    assert r.status_code == 200 and r.json()["reason"] == "free_tier:not_subscribed"


# --- internal peers and verifier failures ------------------------------------

def test_internal_peer_only_when_loopback_without_relay_headers(monkeypatch):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")

    class Req:
        def __init__(self, host, headers):
            self.client = type("C", (), {"host": host})()
            self.headers = headers

    assert textgen_auth.is_internal_request(Req("127.0.0.1", {}))
    assert not textgen_auth.is_internal_request(Req("127.0.0.1", {"cf-connecting-ip": "1.2.3.4"}))
    assert not textgen_auth.is_internal_request(Req("198.51.100.1", {}))
    # TestClient's peer is "testclient", so this is not internal and still needs a key.
    assert post(TestClient(build_app(allow_internal_peer=True))).status_code == 401


def test_verifier_outage_fails_open_and_is_logged(monkeypatch, caplog):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")

    def broken(_):
        raise ConnectionError("db down")

    with caplog.at_level(logging.INFO, logger="textgen_auth"):
        r = post(TestClient(build_app(paid_check=broken)), {"secret": PAID})
    assert r.status_code == 200 and r.json()["reason"] == "verify_error_fail_open"
    assert any("verify_error_fail_open" in rec.getMessage() for rec in caplog.records)
