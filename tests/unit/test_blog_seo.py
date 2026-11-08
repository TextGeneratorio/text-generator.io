import re

import pytest
from fastapi.testclient import TestClient

import main
from questions import blog_fixtures


@pytest.fixture(scope="module")
def client():
    return TestClient(main.app, raise_server_exceptions=False)


def test_unknown_post_is_404(client):
    assert client.get("/blog/does-not-exist").status_code == 404


def test_every_fixture_has_a_template():
    from pathlib import Path

    root = Path(main.__file__).parent / "static/templates/shared"
    missing = [name for name in blog_fixtures.blogs if not (root / f"{name}.jinja2").exists()]
    assert missing == []


def test_checklist_post_renders_with_seo_meta(client):
    path = "/blog/multimodal-api-test-checklist"
    response = client.get(path + "?utm_source=test")
    assert response.status_code == 200
    html = response.text
    assert f'content="https://text-generator.io{path}"' in html
    assert "utm_source" not in re.search(r'property="og:url" content="([^"]*)"', html).group(1)
    assert '"@type":"BlogPosting"' in html
    assert blog_fixtures.blogs["multimodal-api-test-checklist"]["title"] in html
