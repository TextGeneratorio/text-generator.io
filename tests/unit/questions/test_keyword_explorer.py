import numpy as np
import pytest

from questions.keyword_explorer import (
    KeywordExplorerResult,
    WordNetEntry,
    _extract_json,
    _tokenize_topic,
    explore_wordnet,
    find_related_by_embedding,
    generate_llm_content,
    get_stems_and_lemmas,
    get_synonyms_from_wordnet,
    run_keyword_explorer,
)


def test_tokenize_topic():
    assert _tokenize_topic("machine learning") == ["machine", "learning"]
    assert _tokenize_topic("AI") == ["ai"]
    assert _tokenize_topic("a") == []  # single char filtered out
    assert _tokenize_topic("hello-world 123") == ["hello", "world"]


def test_extract_json_from_clean():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_from_fenced():
    raw = '```json\n{"seo_keywords": ["foo"]}\n```'
    result = _extract_json(raw)
    assert result["seo_keywords"] == ["foo"]


def test_extract_json_returns_empty_on_garbage():
    assert _extract_json("no json here") == {}
    assert _extract_json("") == {}


def test_explore_wordnet_returns_entries():
    entries = explore_wordnet("computer")
    assert len(entries) > 0
    assert entries[0].definition
    assert entries[0].pos in ("noun", "verb", "adjective", "adverb")


def test_explore_wordnet_handles_unknown_word():
    entries = explore_wordnet("xyznotaword")
    assert entries == []


def test_get_synonyms_from_wordnet():
    synonyms = get_synonyms_from_wordnet("car")
    assert len(synonyms) > 0
    # "automobile" is a classic WordNet synonym for "car"
    lower_syns = [s.lower() for s in synonyms]
    assert "automobile" in lower_syns or "auto" in lower_syns or "motorcar" in lower_syns


def test_get_stems_and_lemmas():
    stems, lemmas = get_stems_and_lemmas("running machines")
    assert "run" in stems or "machin" in stems
    assert len(lemmas) > 0


def test_find_related_by_embedding_returns_terms(monkeypatch):
    # Mock the embedding functions to avoid loading the real model
    def fake_embedding(t):
        return np.random.randn(4).astype(np.float32)

    def fake_embeddings(texts):
        return np.random.randn(len(texts), 4).astype(np.float32)

    monkeypatch.setattr("questions.keyword_explorer.get_embedding", fake_embedding)
    monkeypatch.setattr("questions.keyword_explorer.get_embeddings", fake_embeddings)

    related = find_related_by_embedding("computer")
    assert isinstance(related, list)
    # WordNet should give us candidates for "computer"
    assert len(related) > 0


def test_generate_llm_content_fallback_on_connection_error(monkeypatch):
    """When the inference server is unreachable, return empty defaults."""
    monkeypatch.setattr(
        "questions.keyword_explorer._call_inference_server",
        lambda *a, **kw: (_ for _ in ()).throw(ConnectionError("no server")),
    )
    result = generate_llm_content("testing")
    assert result["definition"] == ""
    assert result["seo_keywords"] == []
    assert result["glossary"] == []


def test_run_keyword_explorer_returns_complete_structure(monkeypatch):
    """Full pipeline with mocked LLM."""
    monkeypatch.setattr(
        "questions.keyword_explorer.generate_llm_content",
        lambda topic: {
            "definition": f"{topic} is a concept.",
            "seo_keywords": [f"{topic} guide", f"best {topic}"],
            "glossary": [{"term": topic, "definition": "A test concept."}],
        },
    )

    # Mock embeddings to avoid model loading
    monkeypatch.setattr(
        "questions.keyword_explorer.get_embedding",
        lambda t: np.ones(4, dtype=np.float32),
    )
    monkeypatch.setattr(
        "questions.keyword_explorer.get_embeddings",
        lambda ts: np.ones((len(ts), 4), dtype=np.float32),
    )

    # Clear cache to ensure fresh run
    from questions.keyword_explorer import _explorer_cache
    _explorer_cache.clear()

    result = run_keyword_explorer("computer")
    assert result["topic"] == "computer"
    assert isinstance(result["wordnet_entries"], list)
    assert isinstance(result["synonyms"], list)
    assert isinstance(result["related_terms"], list)
    assert result["seo_keywords"] == ["computer guide", "best computer"]
    assert result["topic_definition"] == "computer is a concept."
    assert len(result["glossary_entries"]) == 1
    assert isinstance(result["stems"], list)
    assert isinstance(result["lemmas"], list)


def test_run_keyword_explorer_caches_results(monkeypatch):
    """Second call with same topic should return cached result."""
    call_count = {"n": 0}

    def counting_llm(topic):
        call_count["n"] += 1
        return {"definition": "cached", "seo_keywords": [], "glossary": []}

    monkeypatch.setattr("questions.keyword_explorer.generate_llm_content", counting_llm)
    monkeypatch.setattr(
        "questions.keyword_explorer.get_embedding",
        lambda t: np.ones(4, dtype=np.float32),
    )
    monkeypatch.setattr(
        "questions.keyword_explorer.get_embeddings",
        lambda ts: np.ones((len(ts), 4), dtype=np.float32),
    )

    from questions.keyword_explorer import _explorer_cache
    _explorer_cache.clear()

    r1 = run_keyword_explorer("cache_test_topic")
    r2 = run_keyword_explorer("cache_test_topic")
    assert r1 == r2
    assert call_count["n"] == 1  # LLM only called once
