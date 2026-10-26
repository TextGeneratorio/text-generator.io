from pathlib import Path

from questions import tool_fixtures


def test_tool_fixture_urls_match_template_slugs():
    repo_root = Path(__file__).resolve().parents[3]

    for slug, tool in tool_fixtures.tools_fixtures.items():
        url = tool.get("url", "")
        if not url.startswith("/tools/"):
            continue

        url_slug = url.removeprefix("/tools/")
        template_path = repo_root / "static" / "templates" / "tools" / f"{url_slug}.jinja2"

        assert slug == url_slug
        assert template_path.exists(), f"Missing template for {slug}: {template_path}"


def test_external_first_party_tools_are_safe_and_searchable():
    external_tools = {
        slug: tool
        for slug, tool in tool_fixtures.tools_fixtures.items()
        if tool.get("url", "").startswith("https://app.nz/")
    }

    assert len(external_tools) >= 15
    assert external_tools["papers-search"]["url"] == "https://app.nz/papers"
    assert len({tool["url"] for tool in external_tools.values()}) == len(external_tools)
    for tool in external_tools.values():
        assert tool.get("icon")
        assert tool.get("label")
        assert tool.get("keywords")
