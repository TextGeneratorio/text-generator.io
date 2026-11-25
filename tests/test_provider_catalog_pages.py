from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_homepage_presents_router_providers_and_open_source():
    response = client.get("/", headers={"user-agent": "catalog-test"})
    assert response.status_code == 200
    assert "Use the best of AI" in response.text
    assert "GPT-5.6 Sol" in response.text
    assert "Claude Sonnet" not in response.text
    assert "Unlimited chat, UI tools, and provider APIs" in response.text
    assert "Every API provider" in response.text
    assert 'href="/subscribe"' in response.text
    assert "text-generator/auto" in response.text
    assert "/providers/openai" in response.text
    assert "github.com/TextGeneratorio/text-generator.io" in response.text
    # This stylesheet must be same-origin: the static CDN can retain an older
    # copy during an application deploy and previously left new sections raw.
    assert 'href="/static/css/site-redesign.css?v=13"' in response.text
    # The IndieHunt badge now belongs to the global footer, after the homepage CTA.
    assert response.text.index("tg-final-cta") < response.text.index("indiehunt-badge")


def test_homepage_api_examples_have_working_language_tabs():
    response = client.get("/", headers={"user-agent": "catalog-test"})

    assert response.status_code == 200
    assert 'role="tablist" aria-label="API example language"' in response.text
    assert 'data-code-tab="python"' in response.text
    assert 'data-code-tab="javascript"' in response.text
    assert 'data-code-tab="curl"' in response.text
    assert 'data-code-panel="javascript" hidden' in response.text
    assert 'data-code-panel="curl" hidden' in response.text
    assert 'src="/static/js/homepage-code-tabs.js?v=1"' in response.text
    assert "client.chat.completions.create" in response.text
    assert "curl https://api.text-generator.io/v1/chat/completions" in response.text


def test_provider_directory_and_detail_pages_render():
    directory = client.get("/providers")
    detail = client.get("/providers/anthropic")
    assert directory.status_code == 200
    assert "Every serious AI provider" in directory.text
    assert "/providers/anthropic" in directory.text
    assert detail.status_code == 200
    assert "Claude Haiku 5.5" in detail.text
    assert "/models/claude-haiku-5-5" in detail.text
    assert "Claude Sonnet" not in detail.text


def test_first_party_providers_publish_callable_services():
    directory = client.get("/providers")
    appnz = client.get("/providers/appnz")
    netwrck = client.get("/providers/netwrck")

    assert 'href="/providers/appnz"' in directory.text
    assert 'href="/providers/netwrck"' in directory.text
    assert "First party" in directory.text
    assert "/api/cogs/{model_id}/predict" in appnz.text
    assert "per running second" in appnz.text
    assert "Papers Search" in appnz.text
    assert "https://papers.app.nz/api/search" in appnz.text
    assert "$1" in appnz.text
    assert "per 1,000 searches" in appnz.text
    assert "/tools/text-to-image" in netwrck.text
    assert "Fast SDXL" in netwrck.text


def test_tools_directory_includes_first_party_research_and_cog_suite():
    response = client.get("/tools")

    assert response.status_code == 200
    assert "Papers &amp; Research Search" in response.text
    assert 'href="https://app.nz/papers" target="_blank" rel="noopener noreferrer"' in response.text
    assert "Vocal &amp; Stem Separator" in response.text
    assert "AI Image Upscaler" in response.text
    assert "Background Remover" in response.text
    assert "Image to 3D" in response.text
    assert "Text to Video" in response.text
    assert "Talking Avatar" in response.text
    assert "Photos to Gaussian Splat" in response.text
    assert "LTX Video Studio" in response.text
    assert "Open on App.nz" in response.text
    assert "Showing <strong id=\"tools-visible-count\">" in response.text


def test_model_directory_detail_and_filter_api():
    directory = client.get("/models")
    detail = client.get("/models/text-generator/auto")
    api = client.get("/api/models?provider=anthropic")

    assert directory.status_code == 200
    assert 'id="model-search"' in directory.text
    assert detail.status_code == 200
    assert 'model="text-generator/auto"' in detail.text
    assert api.status_code == 200
    assert api.json()["models"]
    assert {model["provider"] for model in api.json()["models"]} == {"anthropic"}


def test_provider_api_never_exposes_credentials_or_upstream_urls():
    response = client.get("/api/providers")
    assert response.status_code == 200
    payload = response.json()
    assert payload["providers"]
    assert all("secret_names" not in provider for provider in payload["providers"])
    assert all("chat_url" not in provider for provider in payload["providers"])
