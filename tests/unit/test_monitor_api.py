import inspect

from monitoring.service_probe import ProbeResult
from monitors import monitor_api


def _probe(name: str, ok: bool, detail: str = "contract ok") -> ProbeResult:
    return ProbeResult(name=name, ok=ok, elapsed_ms=1, detail=detail, status=200 if ok else None)


def test_local_contracts_probe_compatibility_worker(monkeypatch):
    calls = []

    def fake_systemd(unit, *, expected_port):
        calls.append(("systemd", unit, expected_port))
        return _probe(f"systemd:{unit}", True)

    def fake_feature(name, url, **kwargs):
        calls.append(("feature", name, url))
        return _probe(name, True)

    def fake_embeddings(name, url, **kwargs):
        calls.append(("embeddings", name, url))
        return _probe(name, True)

    monkeypatch.setattr(monitor_api.service_probe, "probe_systemd_service", fake_systemd)
    monkeypatch.setattr(monitor_api.service_probe, "probe_feature_extraction", fake_feature)
    monkeypatch.setattr(monitor_api.service_probe, "probe_openai_embeddings", fake_embeddings)

    assert monitor_api.check_local_contracts() is True
    assert ("systemd", "text-generator-inference.service", 9083) in calls
    assert ("feature", "compat:feature-extraction", "http://127.0.0.1:9083/api/v1/feature-extraction") in calls
    assert ("embeddings", "compat:openai-embeddings", "http://127.0.0.1:9083/v1/embeddings") in calls


def test_local_contract_failure_is_logged(monkeypatch):
    messages = []

    monkeypatch.setattr(monitor_api, "log", messages.append)
    monkeypatch.setattr(
        monitor_api.service_probe,
        "probe_systemd_service",
        lambda *args, **kwargs: _probe("systemd:text-generator-inference.service", True),
    )
    monkeypatch.setattr(
        monitor_api.service_probe,
        "probe_feature_extraction",
        lambda *args, **kwargs: _probe("compat:feature-extraction", False, "URLError: refused"),
    )
    monkeypatch.setattr(
        monitor_api.service_probe,
        "probe_openai_embeddings",
        lambda *args, **kwargs: _probe("compat:openai-embeddings", True),
    )

    assert monitor_api.check_local_contracts() is False
    assert messages == ["Local contract check failed: compat:feature-extraction: URLError: refused"]


def test_api_monitor_does_not_probe_retired_9080_port():
    assert "9080" not in inspect.getsource(monitor_api)
