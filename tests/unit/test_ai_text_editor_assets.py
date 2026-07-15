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


def test_ai_text_editor_uses_local_quill_assets():
    response = client.get("/ai-text-editor")

    assert response.status_code == 200
    assert "cdn.quilljs.com" not in response.text
    assert "/static/libs/quill.min.js" in response.text
    assert "/static/libs/quill.snow.css" in response.text
    assert "/static/js/text-generator-docs.js" in response.text
    assert "/static/js/text-generator-docs-enhanced.js" in response.text
    assert "/static/js/ai-text-editor-init.js" in response.text

    quill_response = client.get("/static/libs/quill.min.js")
    assert quill_response.status_code == 200
    assert len(quill_response.content) > 200_000


def test_ai_text_editor_exposes_markdown_table_controls():
    response = client.get("/ai-text-editor")

    assert response.status_code == 200
    assert 'id="insert-table-btn"' in response.text
    assert "format_table" in response.text

    with open("static/js/text-generator-docs.js", encoding="utf-8") as js_file:
        editor_js = js_file.read()

    assert "convertDelimitedTextToMarkdownTable" in editor_js
    assert "buildBlankMarkdownTable" in editor_js
    assert "insertMarkdownTable" in editor_js
