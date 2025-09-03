import pytest
import requests
from click.testing import CliRunner

from questions.tools.document_markdown_cli import main

pytestmark = [pytest.mark.integration, pytest.mark.internet]

DOCX_URL = "https://calibre-ebook.com/downloads/demos/demo.docx"


def download(url, path):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)


@pytest.fixture(scope="session")
def docx_file(tmp_path_factory):
    path = tmp_path_factory.mktemp("docs") / "cli.docx"
    download(DOCX_URL, path)
    return path


def test_cli_output_file(docx_file, tmp_path):
    runner = CliRunner()
    output_file = tmp_path / "out.md"
    result = runner.invoke(main, [str(docx_file), "-o", str(output_file)])
    assert result.exit_code == 0
    assert output_file.read_text().strip()
