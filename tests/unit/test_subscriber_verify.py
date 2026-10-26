from questions.inference_server import subscriber_verify as sv


def _reset(monkeypatch, netwrck=None, cutedsl=None):
    sv._cache.clear()
    monkeypatch.setattr(sv, "_netwrck", lambda c: netwrck)
    monkeypatch.setattr(sv, "_cutedsl", lambda c: cutedsl)


def test_service_key(monkeypatch):
    _reset(monkeypatch)
    monkeypatch.setenv("OMNISERVE_NATIVE_KEY_TIERS", "k1=paid,k2=background,bad=gold")
    assert sv.verify_credential("k1") == {"status": 200, "tier": "paid", "source": "service"}
    assert sv.service_key_tier("k2") == "background"
    assert sv.service_key_tier("bad") is None


def test_sources(monkeypatch):
    monkeypatch.delenv("OMNISERVE_NATIVE_KEY_TIERS", raising=False)
    _reset(monkeypatch, netwrck=True)
    assert sv.verify_credential("a")["source"] == "netwrck"
    _reset(monkeypatch, netwrck=False, cutedsl=None)
    assert sv.verify_credential("b")["status"] == 402
    _reset(monkeypatch)
    assert sv.verify_credential("c", lambda c: None)["status"] == 401
    _reset(monkeypatch)
    assert sv.verify_credential("d", lambda c: True)["source"] == "textgen"
    assert sv.verify_credential(None)["status"] == 401


def test_error_not_cached(monkeypatch):
    _reset(monkeypatch)

    def boom(c):
        raise RuntimeError("db down")

    monkeypatch.setattr(sv, "_netwrck", boom)
    assert sv.verify_credential("e")["status"] == 503
    monkeypatch.setattr(sv, "_netwrck", lambda c: True)
    assert sv.verify_credential("e")["status"] == 200


def test_contract_body():
    body = sv.subscription_error_body(402)
    assert body["error"]["code"] == "subscription_required"
    assert body["error"]["subscribe_url"] == "https://text-generator.io/subscribe"
