from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from questions import omniserve_paywall as pw


class FakeResp:
    def __init__(self, status, body=None, headers=None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


def _app(resp):
    app = FastAPI()
    pw.install(app)

    @app.get("/x")
    def x():
        pw.raise_for_upstream(resp)
        return {"ok": True}

    return TestClient(app)


def test_upstream_402_maps_to_contract():
    body = {"error": {"code": "subscription_required", "message": "Subscribe", "subscribe_url": "https://other/x"}}
    r = _app(FakeResp(402, body, {"X-Subscribe-URL": "https://other/x"})).get("/x")
    assert r.status_code == 402
    assert r.headers["X-Subscribe-URL"] == pw.SUBSCRIBE_URL
    err = r.json()["error"]
    assert err == {"code": "subscription_required", "message": "Subscribe", "subscribe_url": pw.SUBSCRIBE_URL}


def test_upstream_401_non_json():
    r = _app(FakeResp(401)).get("/x")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "authentication_required"
    assert r.headers["X-Subscribe-URL"] == pw.SUBSCRIBE_URL


@pytest.mark.parametrize("status", [200, 500, 403])
def test_other_status_passthrough(status):
    assert pw.from_upstream(status, {}) is None
    pw.raise_for_upstream(FakeResp(status, {}))


def test_caption_backend_402_is_not_502(monkeypatch):
    from questions.inference_server import inference_server as inf

    monkeypatch.setattr(inf, "IMAGE_CAPTION_BACKEND_BASE", "http://127.0.0.1:8790")
    monkeypatch.setattr(inf, "_get_vllm_session", lambda: SimpleNamespace(post=lambda *a, **k: FakeResp(402, {"error": {"message": "pay"}})))
    with pytest.raises(pw.SubscriptionRequired) as ei:
        inf._caption_image_via_omniserve(b"x", fast_mode=True)
    assert ei.value.status_code == 402
