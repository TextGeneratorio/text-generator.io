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
    assert 'href="/static/css/site-redesign.css?v=11"' in response.text
    # The IndieHunt badge now belongs to the global footer, after the homepage CTA.
    assert response.text.index("tg-final-cta") < response.text.index("indiehunt-badge")


def test_provider_directory_and_detail_pages_render():
    directory = client.get("/providers")
    detail = client.get("/providers/anthropic")
    assert directory.status_code == 200
    assert "Every serious AI provider" in directory.text
    assert "/providers/anthropic" in directory.text
    assert detail.status_code == 200
    assert "Claude Sonnet" in detail.text
    assert "/models/claude-sonnet-latest" in detail.text


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
