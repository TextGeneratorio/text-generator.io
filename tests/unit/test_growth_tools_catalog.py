from questions.tool_fixtures import tools_fixtures


def test_growth_tools_are_listed():
    expected = {
        "competitor-teardown",
        "seo-content-gap-finder",
        "deep-researcher",
        "keyword-glossary-explorer",
    }
    assert expected.issubset(set(tools_fixtures.keys()))


def test_growth_tools_use_shared_workflow_template():
    for key in [
        "competitor-teardown",
        "seo-content-gap-finder",
        "deep-researcher",
        "keyword-glossary-explorer",
    ]:
        tool = tools_fixtures[key]
        assert tool["template"] == "static/templates/tools/marketing-workflow-tool.jinja2"
        assert tool["workflow_key"] == key
