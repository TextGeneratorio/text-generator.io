from questions import prompt_fixtures


def test_prompt_fixture_catalog_has_expected_structure():
    prompts = prompt_fixtures.get_all_prompts()
    slugs = {prompt["slug"] for prompt in prompts}

    assert len(prompts) == 1000
    assert len(slugs) == len(prompts)

    required = {
        "instagram-logo-prompt",
        "threads-logo-prompt",
        "x-logo-prompt",
        "reddit-logo-prompt",
        "bluesky-logo-prompt",
        "discord-logo-prompt",
    }
    assert required.issubset(slugs)


def test_prompt_fixture_links_and_facets_are_consistent():
    prompts = prompt_fixtures.get_all_prompts()
    categories = {item["slug"] for item in prompt_fixtures.get_categories()}
    models = {item["slug"] for item in prompt_fixtures.get_models()}
    prompt_types = {item["slug"] for item in prompt_fixtures.get_prompt_types()}

    for prompt in prompts:
        assert prompt["category_slug"] in categories
        assert prompt["model_slug"] in models
        assert prompt["modality"] in prompt_types
        assert prompt["url"] == f"/prompts/{prompt['slug']}"
        assert prompt["category_url"] == f"/prompts/category/{prompt['category_slug']}"
        assert prompt["model_url"] == f"/prompts/model/{prompt['model_slug']}"
        assert prompt["modality_url"] == f"/prompts/type/{prompt['modality']}"


def test_prompt_sitemap_sections_are_populated():
    sections = prompt_fixtures.get_sitemap_sections()

    assert sections
    assert any(section["title"] == "Categories" for section in sections)
    assert any(section["title"] == "Models" for section in sections)
    assert all(section["items"] for section in sections)
