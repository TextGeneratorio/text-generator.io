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

import main  # noqa: E402, I001


client = TestClient(main.app)


def test_playground_uses_same_origin_app_scripts():
    response = client.get("/playground")

    assert response.status_code == 200
    assert response.text.index("if (!Array.prototype.at)") < response.text.index(
        'src="/static/js/frontend-error-logger.js?v=4"'
    )
    assert 'src="/static/libs/jquery-3.2.1.min.js"' in response.text
    assert 'src="/static/js/material.min.js?v=2"' in response.text
    assert "if (!window.jQuery)" in response.text
    assert "loadScript('/static/libs/select2/dist/js/select2.min.js'" in response.text
    assert 'src="/static/libs/codemirror.js"' in response.text
    assert 'src="/static/libs/javascript.js?v=2"' in response.text
    assert 'src="/static/js/subscription-modal.js"' in response.text
    assert "loadScript('/static/js/playground.js?v=10'" in response.text
    assert 'href="/static/libs/styles/atom-one-dark.css"' in response.text
    assert 'href="/static/libs/select2/dist/css/select2.min.css"' in response.text
    assert 'href="/static/libs/codemirror.css"' in response.text
    assert 'src="/static/libs/highlight.pack.js"' in response.text
    assert "window.__tgPatchHighlightJs" in response.text
    assert 'src="/static/js/highlight-compat.js' not in response.text


def test_bulk_uses_same_origin_app_script():
    response = client.get("/bulk-text-generator")

    assert response.status_code == 200
    assert 'src="/static/libs/select2/dist/js/select2.min.js"' in response.text
    assert 'src="/static/js/bulk.js?v=2"' in response.text
    assert 'src="https://text-generatorstatic.text-generator.io/static/js/bulk.js"' not in response.text


def test_playground_url_parsing_avoids_object_from_entries():
    source = open("static/js/playground.js", encoding="utf-8").read()

    assert "Object.fromEntries" not in source
    assert "function parseQueryParams(search)" in source


def test_playground_select2_usage_is_guarded():
    source = open("static/js/playground.js", encoding="utf-8").read()

    assert "function hasSelect2()" in source
    assert "function initializeSelect2(selector, options)" in source
    assert "function getStopSequenceValues()" in source
    assert "$('#preset').select2(" not in source
    assert "$('#select-stop-sequences').select2({" not in source
    assert "return $('#select-stop-sequences').select2('data').map" in source


def test_bulk_select2_usage_is_guarded():
    source = open("static/js/bulk.js", encoding="utf-8").read()

    assert "function hasSelect2()" in source
    assert "function initializeSelect2(selector, options)" in source
    assert "function getStopSequenceValues()" in source
    assert "$('#preset').select2(" not in source
    assert "$('#select-stop-sequences').select2({" not in source
    assert "$('#select-model').select2({" not in source
    assert "return $('#select-stop-sequences').select2('data').map" in source


def test_playground_text_ui_falls_back_until_codemirror_is_ready():
    source = open("static/js/playground.js", encoding="utf-8").read()

    assert "var setTextUI = function (value)" in source
    assert "if (editor && typeof editor.setValue === 'function')" in source
    assert "document.getElementById('playground-text')" in source
    assert "textArea.value = value" in source


def test_playground_code_dialog_has_accessible_top_right_close_button():
    response = client.get("/playground")

    assert response.status_code == 200
    assert 'id="code-example-dialog"' in response.text
    assert 'aria-labelledby="code-dialog-title"' in response.text
    assert 'class="code-dialog__close close"' in response.text
    assert 'aria-label="Close code example dialog"' in response.text
    assert "onclick=\"this.closest('dialog').close()\"" in response.text
    assert '<button type="button" class="mdl-button close">Close</button>' not in response.text


def test_playground_javascript_targets_only_the_code_dialog():
    source = open("static/js/playground.js", encoding="utf-8").read()

    assert "document.getElementById('code-example-dialog')" in source
    assert "document.querySelector('dialog')" not in source


def test_playground_does_not_turn_http_errors_into_empty_results():
    source = open("static/js/playground.js", encoding="utf-8").read()

    assert "function responseError(response)" in source
    assert "return responseError(response);" in source
    assert "showError({ error: textError }" not in source
    assert "return [];" not in source[source.index("function setupSubmitForm()") :]


def test_playground_submit_uses_same_origin_generate_proxy():
    source = open("static/js/playground.js", encoding="utf-8").read()
    submit_source = source[source.index("function setupSubmitForm()") :]

    assert "fetch('/api/v1/generate'" in submit_source
    assert "fetch('https://api.text-generator.io/api/v1/generate'" not in submit_source


def test_generate_proxy_forwards_to_local_inference(monkeypatch):
    captured = {}

    class UpstreamResponse:
        status_code = 200
        content = b'[{"generated_text":"Hello world"}]'
        headers = {"content-type": "application/json"}

    def fake_post(url, *, json, headers, timeout):
        captured.update(url=url, json=json, headers=headers, timeout=timeout)
        return UpstreamResponse()

    monkeypatch.setattr(main.requests, "post", fake_post)

    response = client.post(
        "/api/v1/generate",
        json={"text": "Hello", "max_length": 5},
        headers={"secret": "test-secret"},
    )

    assert response.status_code == 200
    assert response.json() == [{"generated_text": "Hello world"}]
    assert captured["url"] == "http://127.0.0.1:8791/api/v1/generate"
    assert captured["json"]["text"] == "Hello"
    assert captured["json"]["max_length"] == 5
    assert captured["headers"] == {"secret": "test-secret"}
    assert captured["timeout"] == (5, 1800)


def test_openai_cost_savings_blog_uses_local_highlight_assets():
    response = client.get("/blog/over-10x-openai-cost-savings-one-line-change")

    assert response.status_code == 200
    assert 'href="/static/libs/styles/default.css"' in response.text
    assert 'src="/static/libs/highlight.pack.js"' in response.text
    assert 'src="//cdnjs.cloudflare.com/ajax/libs/highlight.js/11.5.1/highlight.min.js"' not in response.text


def test_openai_cost_savings_blog_has_highlight_fallback_before_inline_highlighting():
    response = client.get("/blog/over-10x-openai-cost-savings-one-line-change")

    assert response.status_code == 200
    assert "function createHighlightFallback()" in response.text
    assert "var currentHljs = createHighlightFallback();" in response.text
    assert "window.hljs = currentHljs;" in response.text
    assert response.text.index("function createHighlightFallback()") < response.text.index(
        'src="/static/libs/highlight.pack.js"'
    )
    assert response.text.index("function createHighlightFallback()") < response.text.index("hljs.highlightAll();")


def test_highlight_compat_bootstrap_runs_before_docs_highlight_pack():
    response = client.get("/docs/docker")

    assert response.status_code == 200
    assert response.text.index("window.__tgPatchHighlightJs") < response.text.index('src="/static/libs/highlight.pack.js"')


def test_codemirror_javascript_mode_is_safe_when_core_asset_fails():
    source = open("static/libs/javascript.js", encoding="utf-8").read()

    assert 'typeof CodeMirror != "undefined"' in source
    assert "else\n    return;" in source
