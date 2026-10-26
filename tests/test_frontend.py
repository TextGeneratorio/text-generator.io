from fastapi.testclient import TestClient

import main

client = TestClient(main.app, raise_server_exceptions=False)


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Text Generator" in response.text


def test_sitemap_page_renders():
    response = client.get("/sitemap")
    assert response.status_code == 200
    assert "Text Generator Sitemap" in response.text
    assert 'href="/sitemap.xml"' in response.text


def test_unfiltered_chat_blog_does_not_require_jquery_for_highlighting():
    response = client.get("/blog/new-unfiltered-chat-gpt-model")

    assert response.status_code == 200
    assert "New Uncensored Chat GPT Model" in response.text
    assert "$(document).ready" not in response.text
    assert "document.addEventListener('DOMContentLoaded'" in response.text
    assert "document.querySelectorAll('.hljs-addition')" in response.text


def test_tools_cta_does_not_send_existing_users_to_signup():
    response = client.get("/tools")

    assert response.status_code == 200
    assert '>Try Our Tools</a>' not in response.text
    assert 'href="/playground">Open Playground</a>' in response.text


def test_auth_pages_return_to_safe_next_url_and_keep_it_when_switching():
    login = client.get("/login?next=%2Ftools%2Ftext-to-image%3Fsize%3D1024")
    signup = client.get("/signup?next=%2Ftools%2Fdomain-generator")

    assert login.status_code == 200
    assert "window.getSafeAuthReturnUrl('/playground')" in login.text
    assert "window.location.href = authReturnUrl" in login.text
    assert 'data-auth-switch' in login.text
    assert signup.status_code == 200
    assert "window.getSafeAuthReturnUrl('/playground')" in signup.text
    assert "window.location.href = authReturnUrl" in signup.text
    assert 'data-auth-switch' in signup.text


def test_tool_login_links_return_to_the_tool():
    domain_tool = client.get("/tools/domain-generator")

    assert domain_tool.status_code == 200
    assert 'href="/login?next=%2Ftools%2Fdomain-generator"' in domain_tool.text


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


def test_external_tool_slug_redirects_to_configured_url():
    response = client.get("/tools/background-remover", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://app.nz/cogs?template=background-remover"


def test_text_to_image_tool_and_tts_studio_render():
    image_tool = client.get("/tools/text-to-image")
    speech_tool = client.get("/text-to-speech")

    assert image_tool.status_code == 200
    assert 'id="tti-form"' in image_tool.text
    assert "images2.netwrck.com" in image_tool.text
    assert speech_tool.status_code == 200
    assert 'id="tts-typeahead"' in speech_tool.text
    assert 'src="/static/js/tts-autocomplete-words.js?v=1"' in speech_tool.text
    assert "Pocket TTS" in speech_tool.text


def test_text_to_image_generation_requires_login():
    response = client.post(
        "/api/tools/text-to-image/generate",
        json={"prompt": "a quiet forest", "size": "1024x1024"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Log in to generate images."


def test_domain_search_tool_renders_first_party_recursive_ui(monkeypatch):
    monkeypatch.setitem(main.tool_fixtures.tools_fixtures["domain-generator"], "premium", False)

    response = client.get("/tools/domain-generator")

    assert response.status_code == 200
    assert 'id="domain-search-form"' in response.text
    assert 'data-endpoint="/api/tools/domain-generator/search"' in response.text
    assert "AI research assistant" in response.text
    assert "helixscience.com" in response.text
    assert "Explore variations" in response.text
    assert "Find more names" in response.text
    assert "GPT-5.6 Luna" not in response.text
    assert "RDAP" not in response.text
    assert 'src="/static/js/domain-generator.js?v=2"' in response.text
    assert 'src="https://domains.netwrck.com"' not in response.text


def test_prompt_optimizer_renders_simplified_ui_without_model_jargon(monkeypatch):
    monkeypatch.setitem(main.tool_fixtures.tools_fixtures["prompt-optimizer"], "premium", False)

    response = client.get("/tools/prompt-optimizer")

    assert response.status_code == 200
    assert 'id="prompt-opt-form"' in response.text
    assert "Start rough." in response.text
    assert "What does “good” look like?" in response.text
    assert 'src="/static/js/prompt-optimizer.js?v=2"' in response.text
    assert "Claude" not in response.text


def test_prompt_optimizer_api_requires_login():
    response = client.post(
        "/api/v1/optimize-prompt",
        json={
            "prompt": "Write a launch plan",
            "evolve_prompt": "Make it specific",
            "judge_prompt": "It should be actionable",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Log in to optimize prompts."


def test_prompt_optimizer_api_uses_session_access_and_returns_result(monkeypatch):
    monkeypatch.setattr(main, "require_paid_tool_access", lambda request, db, **kwargs: object())

    async def fake_optimize(params):
        assert params.prompt == "Write a launch plan"
        return {
            "final_prompt": "Write a focused launch plan for a small design team.",
            "evaluations": [{"prompt": params.prompt, "feedback": "Add an audience.", "score": 55}],
            "model": "deepseek-chat",
        }

    monkeypatch.setattr(main, "optimize_prompt", fake_optimize)
    response = client.post(
        "/api/v1/optimize-prompt",
        json={
            "prompt": "Write a launch plan",
            "evolve_prompt": "Make it clearer",
            "judge_prompt": "It should be actionable",
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "deepseek-chat"
    assert response.json()["final_prompt"].startswith("Write a focused")


def test_domain_search_api_requires_login():
    response = client.post(
        "/api/tools/domain-generator/search",
        json={"description": "Science analytics agent", "current_ideas": []},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Log in to explore domain names."


def test_domain_search_api_runs_server_search(monkeypatch):
    captured = {}

    class User:
        email = "domain-user@example.com"

    def fake_run(description, current_ideas, excluded, **kwargs):
        captured.update(
            description=description,
            current_ideas=current_ideas,
            excluded=excluded,
            kwargs=kwargs,
        )
        return {
            "domains": [{"domain": "helixsignal.com", "status": "available"}],
            "model": "gpt-5.6-luna",
            "checked": 1,
            "available": 1,
        }

    monkeypatch.setattr(main, "require_domain_search_access", lambda request, db: User())
    monkeypatch.setattr(main, "run_domain_search", fake_run)

    response = client.post(
        "/api/tools/domain-generator/search",
        json={
            "description": "  Science analytics agent  ",
            "current_ideas": ["helixscience.com"],
            "exclude_domains": ["twohelixes.com"],
            "inspiration": "helixsignal.com",
            "batch_size": 99,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "gpt-5.6-luna"
    assert captured["description"] == "Science analytics agent"
    assert captured["kwargs"]["count"] == 24
    assert captured["kwargs"]["inspiration"] == "helixsignal.com"
    assert captured["kwargs"]["safety_identifier"].startswith("domain_")


def test_netwrck_static_host_is_normalized():
    assert (
        main.normalize_netwrck_image_url("https://netwrckstatic/static/uploads/example.webp")
        == "https://netwrckstatic.netwrck.com/static/uploads/example.webp"
    )
    assert main.normalize_netwrck_image_url("https://cdn.example/image.webp") == "https://cdn.example/image.webp"


def test_text_to_image_generation_proxies_netwrck(monkeypatch):
    captured = {}

    class UpstreamResponse:
        ok = True
        status_code = 200

        @staticmethod
        def json():
            return {"path": "https://netwrckstatic/static/uploads/generated.webp"}

    def fake_get(url, *, params, timeout):
        captured.update(url=url, params=params, timeout=timeout)
        return UpstreamResponse()

    monkeypatch.setattr(main, "get_current_user", lambda request, db: object())
    monkeypatch.setattr(main.requests, "get", fake_get)

    response = client.post(
        "/api/tools/text-to-image/generate",
        json={"prompt": "  a glass observatory above the clouds  ", "size": "1344x768"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "image_url": "https://netwrckstatic.netwrck.com/static/uploads/generated.webp",
        "provider": "netwrck",
        "model": "fast-sdxl",
        "size": "1344x768",
    }
    assert captured["url"] == "https://images2.netwrck.com/create_and_upload_image"
    assert captured["params"]["prompt"] == "a glass observatory above the clouds"
    assert captured["params"]["width"] == 1344
    assert captured["params"]["height"] == 768
    assert captured["params"]["save_path"].startswith("textgenerator/")
    assert captured["timeout"] == 240


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
