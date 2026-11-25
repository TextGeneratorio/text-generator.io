"""The text-generator.io /api/v1/generate proxy is gated by TEXTGEN_AUTH_MODE.

It reaches omniserve-native over loopback without relay headers, which the gateway treats as
internal (no auth), so this gate is what stops the site host being a free generation API.
"""
import importlib
import sys

import pytest

if "sellerinfo" not in sys.modules:
    try:
        importlib.import_module("sellerinfo")
    except ImportError:
        sys.modules["sellerinfo"] = importlib.import_module("sellerinfo_faked")
main = pytest.importorskip("main")
from fastapi.testclient import TestClient  # noqa: E402

PAID = "paid-user-secret-0000000000000001"
FREE = "free-user-secret-0000000000000003"


class _Upstream:
    status_code = 200
    headers = {"content-type": "application/json"}
    content = b'[{"generated_text": "hi there"}]'

    def json(self):
        return [{"generated_text": "hi there"}]


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def fake_post(url, json=None, headers=None, timeout=None):
        seen.append({"url": url, "json": json, "headers": headers})
        return _Upstream()

    monkeypatch.setattr(main.requests, "post", fake_post)
    monkeypatch.setattr(main, "_site_paid_check", lambda c: {PAID: "paid", FREE: False}.get(c))
    from questions import textgen_auth

    textgen_auth.free_limiter.reset()
    return seen


def gen(headers=None, **body):
    return TestClient(main.app).post("/api/v1/generate", json={"text": "hello there", **body}, headers=headers or {})


def test_warn_mode_still_serves_anonymous(monkeypatch, calls):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "warn")
    assert gen().status_code == 200
    assert len(calls) == 1


def test_enforce_blocks_anonymous_before_any_inference(monkeypatch, calls):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = gen()
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "authentication_required"
    assert calls == []


def test_enforce_free_account_gets_402(monkeypatch, calls):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    assert gen({"secret": FREE}).status_code == 402
    assert calls == []


def test_enforce_paying_user_proxied_with_secret(monkeypatch, calls):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = gen({"secret": PAID}, max_length=300)
    assert r.status_code == 200
    assert calls[0]["headers"]["secret"] == PAID
    assert calls[0]["json"]["max_length"] == 300


def test_enforce_own_site_free_tier_is_clamped(monkeypatch, calls):
    monkeypatch.setenv("TEXTGEN_AUTH_MODE", "enforce")
    r = gen({"Origin": "https://text-generator.io"}, max_length=300)
    assert r.status_code == 200
    assert calls[0]["json"]["max_length"] == 64
