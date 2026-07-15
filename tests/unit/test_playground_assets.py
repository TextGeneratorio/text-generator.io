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


def test_playground_uses_same_origin_app_scripts():
    response = client.get("/playground")

    assert response.status_code == 200
    assert 'src="/static/libs/jquery-3.2.1.min.js"' in response.text
    assert 'src="/static/js/material.min.js"' in response.text
    assert 'src="/static/libs/select2/dist/js/select2.min.js"' in response.text
    assert 'src="/static/libs/codemirror.js"' in response.text
    assert 'src="/static/libs/javascript.js"' in response.text
    assert 'src="/static/js/subscription-modal.js"' in response.text
    assert 'src="/static/js/playground.js?v=5"' in response.text
    assert 'href="/static/libs/styles/atom-one-dark.css"' in response.text
    assert 'href="/static/libs/select2/dist/css/select2.min.css"' in response.text
    assert 'href="/static/libs/codemirror.css"' in response.text
    assert 'src="/static/libs/highlight.pack.js"' in response.text
    assert 'src="/static/js/highlight-compat.js?v=1"' in response.text


def test_playground_url_parsing_avoids_object_from_entries():
    source = open("static/js/playground.js", encoding="utf-8").read()

    assert "Object.fromEntries" not in source
    assert "function parseQueryParams(search)" in source


def test_openai_cost_savings_blog_uses_local_highlight_assets():
    response = client.get("/blog/over-10x-openai-cost-savings-one-line-change")

    assert response.status_code == 200
    assert 'href="/static/libs/styles/default.css"' in response.text
    assert 'src="/static/libs/highlight.pack.js"' in response.text
    assert 'src="//cdnjs.cloudflare.com/ajax/libs/highlight.js/11.5.1/highlight.min.js"' not in response.text
