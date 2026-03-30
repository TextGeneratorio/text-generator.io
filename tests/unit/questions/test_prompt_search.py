import numpy as np

from questions import prompt_fixtures, prompt_search


def _fake_embedding(text: str) -> np.ndarray:
    lowered = text.lower()
    vector = np.array(
        [
            1.0 if "instagram" in lowered else 0.0,
            1.0 if "logo" in lowered or "icon" in lowered else 0.0,
            1.0 if "video" in lowered or "teaser" in lowered or "walkthrough" in lowered else 0.0,
            1.0 if "email" in lowered or "brief" in lowered or "summary" in lowered else 0.0,
            1.0 if "photo" in lowered or "portrait" in lowered else 0.0,
            1.0 if "game" in lowered or "arena" in lowered else 0.0,
        ],
        dtype=float,
    )
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def test_prompt_search_prefers_instagram_logo_prompt(monkeypatch):
    monkeypatch.setattr(prompt_search, "get_embedding", _fake_embedding)
    monkeypatch.setattr(
        prompt_search,
        "get_embeddings",
        lambda texts: np.vstack([_fake_embedding(text) for text in texts]),
    )

    index = prompt_search.PromptSearchIndex(prompt_fixtures.get_all_prompts())
    results = index.search("instagram logo", limit=3)

    assert results
    assert results[0]["slug"] == "instagram-logo-prompt"


def test_prompt_search_respects_prompt_type_filter(monkeypatch):
    monkeypatch.setattr(prompt_search, "get_embedding", _fake_embedding)
    monkeypatch.setattr(
        prompt_search,
        "get_embeddings",
        lambda texts: np.vstack([_fake_embedding(text) for text in texts]),
    )

    index = prompt_search.PromptSearchIndex(prompt_fixtures.get_all_prompts())
    results = index.search("launch video", prompt_type_slug="video", limit=8)

    assert results
    assert all(result["modality"] == "video" for result in results)


def test_prompt_search_returns_featured_results_for_empty_query(monkeypatch):
    monkeypatch.setattr(prompt_search, "get_embedding", _fake_embedding)
    monkeypatch.setattr(
        prompt_search,
        "get_embeddings",
        lambda texts: np.vstack([_fake_embedding(text) for text in texts]),
    )

    index = prompt_search.PromptSearchIndex(prompt_fixtures.get_all_prompts())
    results = index.search("", limit=5)

    assert results
    assert results[0]["featured"] is True
