"""Keyword & Glossary Explorer — combines WordNet, NLTK, embeddings, and LLM generation."""

import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import cachetools
import numpy as np

from questions.logging_config import get_logger
from questions.prompt_search import get_embedding, get_embeddings

logger = get_logger(__name__)

INFERENCE_SERVER_URL = os.getenv("INFERENCE_SERVER_URL", "https://api.text-generator.io")
USE_OPENAI = os.getenv("KEYWORD_EXPLORER_USE_OPENAI", "0") == "1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

_explorer_cache: cachetools.TTLCache = cachetools.TTLCache(maxsize=500, ttl=60 * 60)

# ---------------------------------------------------------------------------
# NLTK / WordNet helpers (lazy-loaded)
# ---------------------------------------------------------------------------

_nltk_ready = False


def _ensure_nltk():
    global _nltk_ready
    if _nltk_ready:
        return
    import nltk

    for resource, path in [
        ("wordnet", "corpora/wordnet"),
        ("omw-1.4", "corpora/omw-1.4"),
        ("stopwords", "corpora/stopwords"),
    ]:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(resource, quiet=True)
    _nltk_ready = True


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class WordNetEntry:
    word: str
    pos: str
    definition: str
    examples: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    hypernyms: List[str] = field(default_factory=list)
    hyponyms: List[str] = field(default_factory=list)


@dataclass
class KeywordExplorerResult:
    topic: str
    wordnet_entries: List[Dict[str, Any]] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    related_terms: List[str] = field(default_factory=list)
    seo_keywords: List[str] = field(default_factory=list)
    glossary_entries: List[Dict[str, str]] = field(default_factory=list)
    topic_definition: str = ""
    stems: List[str] = field(default_factory=list)
    lemmas: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# WordNet exploration
# ---------------------------------------------------------------------------

POS_MAP = {"n": "noun", "v": "verb", "a": "adjective", "r": "adverb", "s": "adjective"}


def explore_wordnet(topic: str) -> List[WordNetEntry]:
    """Return synset info (definitions, examples, hypernyms, hyponyms) for *topic*."""
    _ensure_nltk()
    from nltk.corpus import wordnet

    entries: List[WordNetEntry] = []
    seen_defs: set = set()
    for token in _tokenize_topic(topic):
        for syn in wordnet.synsets(token):
            defn = syn.definition()
            if defn in seen_defs:
                continue
            seen_defs.add(defn)
            entries.append(
                WordNetEntry(
                    word=syn.name().split(".")[0].replace("_", " "),
                    pos=POS_MAP.get(syn.pos(), syn.pos()),
                    definition=defn,
                    examples=syn.examples()[:3],
                    synonyms=[l.name().replace("_", " ") for l in syn.lemmas()][:8],
                    hypernyms=[
                        h.name().split(".")[0].replace("_", " ")
                        for h in syn.hypernyms()
                    ][:5],
                    hyponyms=[
                        h.name().split(".")[0].replace("_", " ")
                        for h in syn.hyponyms()
                    ][:8],
                )
            )
            if len(entries) >= 12:
                return entries
    return entries


def get_synonyms_from_wordnet(topic: str) -> List[str]:
    """All unique synonyms (lemma names) across all synsets for *topic*."""
    _ensure_nltk()
    from nltk.corpus import wordnet

    synonyms: set = set()
    for token in _tokenize_topic(topic):
        for syn in wordnet.synsets(token):
            for lemma in syn.lemmas():
                name = lemma.name().replace("_", " ")
                if name.lower() != token.lower():
                    synonyms.add(name)
    return sorted(synonyms)[:30]


# ---------------------------------------------------------------------------
# NLTK stemming / lemmatization
# ---------------------------------------------------------------------------


def get_stems_and_lemmas(topic: str) -> tuple:
    """Return (stems, lemmas) for the tokens in *topic*."""
    _ensure_nltk()
    from nltk.stem import PorterStemmer, WordNetLemmatizer

    stemmer = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    tokens = _tokenize_topic(topic)
    stems = sorted({stemmer.stem(t) for t in tokens})
    lemmas = sorted({lemmatizer.lemmatize(t) for t in tokens})
    return stems, lemmas


# ---------------------------------------------------------------------------
# Embedding-based related terms
# ---------------------------------------------------------------------------


def _get_wordnet_candidates(topic: str, max_candidates: int = 200) -> List[str]:
    """Walk the WordNet graph to collect candidate related terms."""
    _ensure_nltk()
    from nltk.corpus import wordnet

    candidates: set = set()
    for token in _tokenize_topic(topic):
        for synset in wordnet.synsets(token):
            for lemma in synset.lemmas():
                candidates.add(lemma.name().replace("_", " "))
            for hyper in synset.hypernyms():
                for lemma in hyper.lemmas():
                    candidates.add(lemma.name().replace("_", " "))
            for hypo in synset.hyponyms():
                for lemma in hypo.lemmas():
                    candidates.add(lemma.name().replace("_", " "))
            for hyper in synset.hypernyms():
                for sister in hyper.hyponyms():
                    for lemma in sister.lemmas():
                        candidates.add(lemma.name().replace("_", " "))
    candidates -= {t.lower() for t in _tokenize_topic(topic)}
    return list(candidates)[:max_candidates]


def find_related_by_embedding(topic: str, top_k: int = 20) -> List[str]:
    """Find the most semantically related terms using embeddings over WordNet candidates."""
    candidates = _get_wordnet_candidates(topic)
    if not candidates:
        return []

    try:
        topic_vec = get_embedding(topic)
        cand_vecs = get_embeddings(candidates)
        scores = cand_vecs @ topic_vec
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [candidates[i] for i in top_indices]
    except Exception as exc:
        logger.warning("Embedding-based related terms failed: %s", exc)
        return candidates[:top_k]


# ---------------------------------------------------------------------------
# LLM content generation
# ---------------------------------------------------------------------------

_KEYWORD_SYSTEM = (
    "You are an SEO and linguistics expert. "
    "Return valid JSON only. No markdown fences, no extra text."
)

_KEYWORD_PROMPT = (
    'For the topic "{topic}", provide:\n'
    "1. A clear 2-3 sentence definition\n"
    "2. 15-20 SEO keyword phrases a content writer should target\n"
    "3. 5-8 glossary entries (term + short definition) for related concepts\n\n"
    "Return JSON with this exact shape:\n"
    "{{\n"
    '  "definition": "...",\n'
    '  "seo_keywords": ["keyword 1", "keyword 2"],\n'
    '  "glossary": [{{"term": "...", "definition": "..."}}]\n'
    "}}"
)


def _call_inference_server(prompt: str, system_message: str, max_tokens: int = 1024) -> str:
    """Call the local inference server's OpenAI-compatible chat endpoint."""
    import requests

    response = requests.post(
        f"{INFERENCE_SERVER_URL}/v1/chat/completions",
        json={
            "model": "best",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_openai(prompt: str, system_message: str, max_tokens: int = 800) -> str:
    """Call OpenAI Responses API (same pattern as deep_research.py)."""
    import requests

    api_key = OPENAI_API_KEY.strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-5-nano",
            "instructions": system_message,
            "input": prompt,
            "max_output_tokens": max_tokens,
            "store": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("output_text", "") or ""


def _extract_json(raw: str) -> Dict[str, Any]:
    """Best-effort JSON extraction from potentially messy LLM output."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def generate_llm_content(topic: str) -> Dict[str, Any]:
    """Generate SEO keywords, glossary, and definition via LLM.

    Falls back gracefully if the inference server is unavailable.
    """
    prompt = _KEYWORD_PROMPT.format(topic=topic)
    try:
        if USE_OPENAI:
            raw = _call_openai(prompt, _KEYWORD_SYSTEM)
        else:
            raw = _call_inference_server(prompt, _KEYWORD_SYSTEM)
        result = _extract_json(raw)
        return {
            "definition": str(result.get("definition", "")),
            "seo_keywords": [str(k) for k in result.get("seo_keywords", []) if k],
            "glossary": [
                {"term": str(g.get("term", "")), "definition": str(g.get("definition", ""))}
                for g in result.get("glossary", [])
                if isinstance(g, dict) and g.get("term")
            ],
        }
    except Exception as exc:
        logger.warning("LLM content generation failed for '%s': %s", topic, exc)
        return {"definition": "", "seo_keywords": [], "glossary": []}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _tokenize_topic(topic: str) -> List[str]:
    """Split topic into individual words for WordNet lookup."""
    return [w for w in re.findall(r"[a-zA-Z]+", topic.lower()) if len(w) >= 2]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_keyword_explorer(topic: str) -> Dict[str, Any]:
    """Orchestrate all keyword exploration sources and return combined result."""
    cache_key = topic.strip().lower()
    cached = _explorer_cache.get(cache_key)
    if cached is not None:
        return cached

    wordnet_entries = explore_wordnet(topic)
    synonyms = get_synonyms_from_wordnet(topic)
    stems, lemmas = get_stems_and_lemmas(topic)
    related_terms = find_related_by_embedding(topic)
    llm_content = generate_llm_content(topic)

    result = asdict(
        KeywordExplorerResult(
            topic=topic,
            wordnet_entries=[asdict(e) for e in wordnet_entries],
            synonyms=synonyms,
            related_terms=related_terms,
            seo_keywords=llm_content.get("seo_keywords", []),
            glossary_entries=llm_content.get("glossary", []),
            topic_definition=llm_content.get("definition", ""),
            stems=stems,
            lemmas=lemmas,
        )
    )

    _explorer_cache[cache_key] = result
    return result
