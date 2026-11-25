import xml.etree.ElementTree as ET

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_sitemap_is_xml_with_real_urls():
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml")
    assert "max-age" in r.headers["cache-control"]
    root = ET.fromstring(r.content)
    locs = [e.text for e in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert "https://text-generator.io/guides/openai-compatible-api" in locs
    assert len(locs) == len(set(locs)) > 100


def test_llms_txt_and_full():
    r = client.get("/llms.txt")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain")
    assert "api.text-generator.io/v1" in r.text
    full = client.get("/llms-full.txt")
    assert full.status_code == 200 and "text-generator/auto" in full.text and "kimi-k3" in full.text


def test_guides_compare_agents_pages():
    for path in ["/guides", "/guides/cheap-llm-api", "/compare/openrouter", "/agents", "/guides/kimi-k3-api"]:
        r = client.get(path, headers={"user-agent": "t"})
        assert r.status_code == 200, path
        assert "application/ld+json" in r.text and "FAQPage" in r.text or path == "/guides"
        assert "cache-control" in r.headers
    assert client.get("/guides/nope").status_code == 404


def test_wellknown_and_openapi_headers():
    assert client.get("/.well-known/api-catalog").status_code == 200
    assert client.get("/.well-known/openapi.json").status_code == 200
    assert "max-age" in client.get("/openapi.json").headers["cache-control"]
    assert "Sitemap:" in client.get("/robots.txt").text
