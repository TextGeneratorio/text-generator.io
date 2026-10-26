import shutil
import subprocess
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

import main


class InlineScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_inline_script = False
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag != "script":
            return

        attr_names = {name for name, _value in attrs}
        self._in_inline_script = "src" not in attr_names

    def handle_data(self, data):
        if self._in_inline_script and data.strip():
            self.scripts.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_inline_script = False


def test_kubernetes_docs_inline_scripts_parse(tmp_path):
    if not shutil.which("node"):
        pytest.skip("node is required to syntax-check rendered inline scripts")

    client = TestClient(main.app, raise_server_exceptions=False)
    response = client.get("/docs/kubernetes")

    assert response.status_code == 200

    parser = InlineScriptParser()
    parser.feed(response.text)

    assert parser.scripts

    for index, script in enumerate(parser.scripts):
        script_path = tmp_path / f"inline-script-{index}.js"
        script_path.write_text(script, encoding="utf-8")
        result = subprocess.run(
            ["node", "--check", str(script_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
