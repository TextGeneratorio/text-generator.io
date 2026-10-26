import json

from monitoring import monitor_500s


def test_harmless_server_lines_ignored(tmp_path):
    log_file = tmp_path / "mainserver.log"
    text = "\n".join([
        'INFO uvicorn.access - 1.2.3.4:5 - "POST /api/x HTTP/1.1" 503',
        "Completed request: GET https://text-generator.io/a - Status: 502 - Time: 1s",
        "    raise exc_value.with_traceback(exc_tb)",
        "Status: 500 ClientDisconnect while streaming",
        "Status: 500 upstream openrouter returned 429",
    ])
    assert monitor_500s.extract_signals(log_file, text) == []


def test_real_500_and_traceback_captured(tmp_path):
    log_file = tmp_path / "mainserver.log"
    text = 'INFO - 1.2.3.4:5 - "POST /api/login HTTP/1.1" 500\nTraceback (most recent call last):'
    assert len(monitor_500s.extract_signals(log_file, text)) == 2


def line(n):
    return f'2026-10-07 03:0{n}:00 INFO uvicorn.access - 10.0.0.{n}:{n}00 - "POST /api/login?u=a{n} HTTP/1.1" 500'


def test_gate_threshold_dedupe_and_cooldown(monkeypatch):
    monkeypatch.setenv("TEXTGEN_MONITOR_SIGNAL_SCANS", "99")
    state = {}
    assert monitor_500s.gate_signals(state, {"mainserver.log": [line(1)]}, now=1000) == {}
    assert monitor_500s.gate_signals(state, {"mainserver.log": [line(2), line(3)]}, now=1001) == {"mainserver.log": [line(3)]}
    assert monitor_500s.gate_signals(state, {"mainserver.log": [line(4)] * 5}, now=1002) == {}


def test_gate_consecutive_scans(monkeypatch):
    state = {}
    probe = {"synthetic-service-probe": ["Status: 500 synthetic probe production:generate failed: HTTP 500"]}
    assert monitor_500s.gate_signals(state, probe, now=1) == {}
    assert monitor_500s.gate_signals(state, {}, now=2) == {}
    assert monitor_500s.gate_signals(state, probe, now=3) == {}
    assert monitor_500s.gate_signals(state, probe, now=4) == probe


def test_frontend_signature_ignores_receipt_fields():
    rec = lambda n: json.dumps({"received_at": n, "remote_addr": n, "payload": {"event": {"type": "window_error", "message": "x is undefined", "ts": n}}})
    assert monitor_500s.signal_signature("frontend-errors.jsonl", rec(1)) == monitor_500s.signal_signature("frontend-errors.jsonl", rec(2))


def test_restart_grace_skips_one_scan_only():
    state = {}
    young = lambda unit: 30.0
    assert monitor_500s.in_restart_grace(state, uptime=young) is True
    assert monitor_500s.in_restart_grace(state, uptime=young) is False
    assert monitor_500s.in_restart_grace(state, uptime=lambda unit: None) is False
