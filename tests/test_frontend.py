from fastapi.testclient import TestClient

import main

client = TestClient(main.app, raise_server_exceptions=False)


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Text Generator" in response.text


def test_use_case_with_escaped_surrogate_emoji_renders():
    response = client.get("/use-cases/default-movie-to-emoji")

    assert response.status_code == 200
    assert "Movie to Emoji" in response.text
    assert "%F0%9F%91%A8" in response.text


def test_normal_browser_keeps_auth_hydration_enabled():
    response = client.get("/", headers={"user-agent": "Mozilla/5.0 pytest-browser"})

    assert response.status_code == 200
    assert "window.skip_auth_hydration = false;" in response.text


def test_social_crawler_skips_auth_hydration():
    response = client.get(
        "/use-cases/default-sql-request",
        headers={"user-agent": "meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)"},
    )

    assert response.status_code == 200
    assert "window.skip_auth_hydration = true;" in response.text


def test_unknown_tool_slug_returns_404():
    response = client.get("/tools/.env")

    assert response.status_code == 404


def test_openapi_json_renders_valid_json():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["openapi"]


def test_openapi_json_uses_cached_spec_when_static_file_is_invalid(tmp_path, monkeypatch):
    bad_openapi = tmp_path / "openapi.json"
    bad_openapi.write_text('{"openapi": ', encoding="utf-8")
    cached_spec = {"openapi": "3.1.0", "info": {"title": "cached", "version": "test"}, "paths": {}}

    monkeypatch.setattr(main, "OPENAPI_JSON_PATH", bad_openapi)
    monkeypatch.setattr(main, "_OPENAPI_SPEC_CACHE", cached_spec)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json() == cached_spec
