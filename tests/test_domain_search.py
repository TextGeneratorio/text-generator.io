from __future__ import annotations

from types import SimpleNamespace

import pytest

from questions import domain_search


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            response = requests.Response()
            response.status_code = self.status_code
            response._content = self.text.encode()
            raise requests.HTTPError(response=response)

    def json(self):
        return self._payload


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://WWW.HelixScience.com/path", "helixscience.com"),
        ("two-helixes.ai", "two-helixes.ai"),
        ("bad_domain.com", None),
        ("not a domain", None),
        ("-helix.com", None),
    ],
)
def test_normalize_domain(value, expected):
    assert domain_search.normalize_domain(value) == expected


def test_generation_uses_deepseek_chat_and_json_schema():
    model_output = {
        "candidates": [
            {"domain": "HelixSignal.com", "why": "Science plus insight", "strategy": "Compound", "score": 91},
            {"domain": "bad domain", "why": "invalid", "strategy": "Invalid", "score": 5},
        ]
    }
    captured = {}

    def fake_query(prompt, schema, **kwargs):
        captured.update(prompt=prompt, schema=schema, kwargs=kwargs)
        return SimpleNamespace(data=model_output, model="deepseek-chat", provider="deepseek")

    result = domain_search.generate_domain_candidates(
        domain_search.DEFAULT_DOMAIN_SEARCH_PROMPT,
        domain_search.DEFAULT_DOMAIN_IDEAS,
        ["helixscience.com"],
        inspiration="twohelixes.com",
        count=12,
        safety_identifier="domain_test",
        query_json=fake_query,
    )

    assert result == [{"domain": "helixsignal.com", "why": "Science plus insight", "strategy": "Compound", "score": 91}]
    assert captured["kwargs"]["model"] == "deepseek-chat"
    assert captured["kwargs"]["temperature"] == 0.8
    assert captured["schema"]["additionalProperties"] is False
    assert "twohelixes.com" in captured["prompt"]


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [(200, "taken"), (404, "available"), (429, "unknown"), (500, "unknown")],
)
def test_rdap_status_mapping(status_code, expected):
    class Session:
        def get(self, url, **kwargs):
            assert url.endswith("/helixsignal.com")
            assert kwargs["allow_redirects"] is True
            return FakeResponse(status_code=status_code)

    assert domain_search.check_domain_availability("helixsignal.com", session=Session())["status"] == expected


def test_run_domain_search_includes_seed_ideas_on_first_wave(monkeypatch):
    monkeypatch.setattr(
        domain_search,
        "generate_domain_candidates",
        lambda *args, **kwargs: [
            {"domain": "helixsignal.com", "why": "Clear analytics signal", "strategy": "Compound", "score": 90}
        ],
    )
    monkeypatch.setattr(
        domain_search,
        "check_candidates",
        lambda candidates: [{**item, "status": "available", "detail": "No registry record found"} for item in candidates],
    )

    result = domain_search.run_domain_search(
        domain_search.DEFAULT_DOMAIN_SEARCH_PROMPT,
        domain_search.DEFAULT_DOMAIN_IDEAS,
        [],
    )

    assert [item["domain"] for item in result["domains"]] == [
        "helixscience.com",
        "doublehelixes.com",
        "twohelixes.com",
        "helixsignal.com",
    ]
    assert result["model"] == "deepseek-chat"
    assert result["available"] == 4
    assert result["fallback"] is False


def test_run_domain_search_uses_local_fallback_when_model_is_rate_limited(monkeypatch):
    def fake_generate(*args, **kwargs):
        raise domain_search.DomainSearchError("The naming model is temporarily unavailable.")

    checked_candidates = []

    def fake_check(candidates):
        checked_candidates.extend(candidates)
        return [{**item, "status": "available", "detail": "No registry record found"} for item in candidates]

    monkeypatch.setattr(domain_search, "generate_domain_candidates", fake_generate)
    monkeypatch.setattr(domain_search, "check_candidates", fake_check)

    result = domain_search.run_domain_search(
        "AI analytics agent for helix science research teams",
        ["helixscience.com"],
        ["helixscience.com", "helixlabs.com"],
        count=6,
    )

    assert result["fallback"] is True
    assert result["checked"] == 6
    assert result["available"] == 6
    assert len({item["domain"] for item in result["domains"]}) == 6
    assert all(item["domain"] not in {"helixscience.com", "helixlabs.com"} for item in result["domains"])
    assert all(item["status"] == "available" for item in result["domains"])
    assert [item["domain"] for item in checked_candidates] == [item["domain"] for item in result["domains"]]


def test_recursive_wave_does_not_repeat_seen_seeds(monkeypatch):
    captured = {}

    def fake_generate(description, ideas, excluded, **kwargs):
        captured.update(ideas=list(ideas), excluded=list(excluded), inspiration=kwargs["inspiration"])
        return [{"domain": "helixvector.ai", "why": "New branch", "strategy": "Technical", "score": 84}]

    monkeypatch.setattr(domain_search, "generate_domain_candidates", fake_generate)
    monkeypatch.setattr(domain_search, "check_candidates", lambda candidates: [{**candidates[0], "status": "available", "detail": "ok"}])

    result = domain_search.run_domain_search(
        "Science analytics agent",
        ["helixscience.com"],
        ["helixscience.com", "twohelixes.com"],
        inspiration="twohelixes.com",
    )

    assert [item["domain"] for item in result["domains"]] == ["helixvector.ai"]
    assert captured == {
        "ideas": ["helixscience.com"],
        "excluded": ["helixscience.com", "twohelixes.com"],
        "inspiration": "twohelixes.com",
    }
