import asyncio
import json
import os
import sys
import types

from starlette.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["BCRYPT_PEPPER"] = "pepper"
os.environ["GOOGLE_CLOUD_PROJECT"] = "local"
os.environ["DATASTORE_EMULATOR_HOST"] = "localhost:1234"

sys.modules["sellerinfo"] = types.SimpleNamespace(STRIPE_LIVE_SECRET="", STRIPE_LIVE_KEY="", CLAUDE_API_KEY="")

import main


client = TestClient(main.app)


class DisconnectedFrontendLogRequest:
    headers = {}
    client = None

    async def body(self):
        raise main.ClientDisconnect()


def test_frontend_error_log_writes_jsonl(tmp_path, monkeypatch):
    log_file = tmp_path / "frontend-errors.jsonl"
    monkeypatch.setattr(main, "FRONTEND_ERROR_LOG_FILE", log_file)

    response = client.post(
        "/api/frontend-error",
        json={
            "event": {"type": "fetch_5xx", "url": "https://api.text-generator.io/api/v1/generate_speech", "status": 500},
            "page": {"url": "https://text-generator.io/text-to-speech"},
            "sourceMaps": [{"scriptUrl": "https://text-generator.io/static/js/material.min.js", "sourceMapUrl": "material.min.js.map"}],
        },
        headers={"user-agent": "pytest-browser", "cf-ray": "test-ray"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "logged"}

    records = log_file.read_text(encoding="utf-8").splitlines()
    assert len(records) == 1
    record = json.loads(records[0])
    assert record["user_agent"] == "pytest-browser"
    assert record["cf_ray"] == "test-ray"
    assert record["payload"]["event"]["type"] == "fetch_5xx"
    assert record["payload"]["sourceMaps"][0]["sourceMapUrl"] == "material.min.js.map"


def test_frontend_error_log_rejects_large_payload(monkeypatch):
    monkeypatch.setattr(main, "MAX_FRONTEND_ERROR_LOG_BYTES", 16)

    response = client.post(
        "/api/frontend-error",
        content=b'{"message":"this is too large"}',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413


def test_frontend_error_log_ignores_client_disconnect():
    response = asyncio.run(main.log_frontend_error(DisconnectedFrontendLogRequest()))

    assert response.status_code == 204
