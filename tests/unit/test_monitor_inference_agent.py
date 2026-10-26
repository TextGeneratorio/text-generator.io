import json

from monitors import monitor_inference_agent


class _Response:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def test_check_endpoint_accepts_compat_inference_liveness(monkeypatch):
    monkeypatch.setattr(
        monitor_inference_agent.urllib.request,
        "urlopen",
        lambda *args, **kwargs: _Response(200, {"inference": "ok"}),
    )

    ok, detail = monitor_inference_agent.check_endpoint("http://127.0.0.1:9083/liveness_check")

    assert ok is True
    assert detail == "status=200 inference=ok"


def test_check_endpoint_accepts_native_status_liveness(monkeypatch):
    monkeypatch.setattr(
        monitor_inference_agent.urllib.request,
        "urlopen",
        lambda *args, **kwargs: _Response(200, {"status": "ok", "gpu": True}),
    )

    ok, detail = monitor_inference_agent.check_endpoint("https://api.text-generator.io/liveness_check")

    assert ok is True
    assert detail == "status=200 status=ok"


def test_check_endpoint_rejects_unhealthy_json(monkeypatch):
    monkeypatch.setattr(
        monitor_inference_agent.urllib.request,
        "urlopen",
        lambda *args, **kwargs: _Response(200, {"status": "error"}),
    )

    ok, detail = monitor_inference_agent.check_endpoint("https://api.text-generator.io/liveness_check")

    assert ok is False
    assert "status=200 body=" in detail
