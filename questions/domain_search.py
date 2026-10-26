"""AI-assisted domain discovery with server-side availability checks."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Iterable
from urllib.parse import quote

import requests

from questions.tool_ai import DEFAULT_TOOL_MODEL, ToolAIError, query_tool_json

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN_SEARCH_PROMPT = (
    "An AI research assistant for scientists working with complex data. Find memorable .com names "
    "that suggest discovery, clarity, and science."
)
DEFAULT_DOMAIN_IDEAS = ("helixscience.com", "doublehelixes.com", "twohelixes.com")
DEFAULT_DOMAIN_MODEL = DEFAULT_TOOL_MODEL
RDAP_DOMAIN_URL = os.getenv("DOMAIN_RDAP_URL", "").strip()
FALLBACK_TLDS = ("com", "ai", "io", "science", "bio", "net")
FALLBACK_SUFFIXES = (
    "labs",
    "signal",
    "scope",
    "pilot",
    "forge",
    "wise",
    "base",
    "arc",
    "flow",
    "spark",
    "works",
    "hub",
)
FALLBACK_STOPWORDS = {
    "about",
    "after",
    "agent",
    "also",
    "and",
    "are",
    "business",
    "clear",
    "complex",
    "data",
    "decisions",
    "domain",
    "explore",
    "from",
    "helps",
    "into",
    "name",
    "product",
    "research",
    "that",
    "the",
    "this",
    "turn",
    "want",
    "with",
    "you",
}
RDAP_SERVERS = {
    "com": "https://rdap.verisign.com/com/v1/domain/",
    "net": "https://rdap.verisign.com/net/v1/domain/",
    "org": "https://rdap.publicinterestregistry.org/rdap/org/domain/",
    # Identity Digital is the authoritative RDAP service for .ai and many of
    # the descriptive TLDs the naming model commonly proposes.
    "ai": "https://rdap.identitydigital.services/rdap/domain/",
    "bio": "https://rdap.identitydigital.services/rdap/domain/",
    "science": "https://rdap.identitydigital.services/rdap/domain/",
}

DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}\.?$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


class DomainSearchError(RuntimeError):
    """Raised when domain generation cannot return a usable result."""


def normalize_domain(value: str) -> str | None:
    """Return a safe ASCII domain or ``None`` for invalid user/model output."""
    candidate = str(value or "").strip().lower()
    candidate = re.sub(r"^https?://", "", candidate).split("/", 1)[0]
    candidate = candidate.split("?", 1)[0].split("#", 1)[0].rstrip(".")
    if candidate.startswith("www."):
        candidate = candidate[4:]
    try:
        candidate = candidate.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    return candidate if DOMAIN_PATTERN.fullmatch(candidate) else None


def normalize_domains(values: Iterable[str], *, limit: int = 80) -> list[str]:
    domains: list[str] = []
    seen: set[str] = set()
    for value in values:
        domain = normalize_domain(value)
        if not domain or domain in seen:
            continue
        seen.add(domain)
        domains.append(domain)
        if len(domains) >= limit:
            break
    return domains


def _fallback_keywords(
    description: str,
    current_ideas: Iterable[str],
    inspiration: str,
    *,
    limit: int = 10,
) -> list[str]:
    raw_terms: list[str] = []
    for domain in normalize_domains(current_ideas, limit=30):
        root = domain.rsplit(".", 1)[0]
        raw_terms.extend(root.split("-"))
    raw_terms.extend(re.findall(r"[a-z0-9]{3,18}", str(inspiration or "").lower()))
    raw_terms.extend(re.findall(r"[a-z0-9]{3,18}", str(description or "").lower()))

    keywords: list[str] = []
    seen: set[str] = set()
    for term in raw_terms:
        term = re.sub(r"[^a-z0-9]", "", term)[:14]
        if len(term) < 3 or term in FALLBACK_STOPWORDS or term in seen:
            continue
        seen.add(term)
        keywords.append(term)
        if len(keywords) >= limit:
            break
    return keywords or ["brand", "signal", "labs"]


def generate_fallback_domain_candidates(
    description: str,
    current_ideas: Iterable[str],
    excluded_domains: Iterable[str],
    *,
    inspiration: str = "",
    count: int = 18,
) -> list[dict[str, Any]]:
    """Return useful deterministic candidates when the naming model is rate limited."""
    count = max(6, min(int(count), 24))
    excluded = set(normalize_domains(excluded_domains, limit=200))
    keywords = _fallback_keywords(description, current_ideas, inspiration)
    seed = hashlib.sha256(
        json.dumps(
            {
                "description": str(description or "")[:3000],
                "ideas": list(current_ideas),
                "excluded": sorted(excluded),
                "inspiration": str(inspiration or "")[:300],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    roots: list[tuple[str, str]] = []
    for index, keyword in enumerate(keywords):
        suffix = FALLBACK_SUFFIXES[(int(seed[index % len(seed)], 16) + index) % len(FALLBACK_SUFFIXES)]
        roots.extend(
            [
                (f"{keyword}{suffix}", "Keyword blend"),
                (f"{suffix}{keyword}", "Positioning twist"),
            ]
        )
    for left_index, left in enumerate(keywords[:5]):
        for right in keywords[left_index + 1 : left_index + 4]:
            roots.append((f"{left}{right}", "Compound"))
            roots.append((f"{right}{left}", "Compound"))

    candidates: list[dict[str, Any]] = []
    seen = set(excluded)
    for root, strategy in roots:
        root = re.sub(r"[^a-z0-9-]", "", root)[:50].strip("-")
        if len(root) < 3:
            continue
        for tld in FALLBACK_TLDS:
            domain = normalize_domain(f"{root}.{tld}")
            if not domain or domain in seen:
                continue
            seen.add(domain)
            score_seed = int(hashlib.sha256(f"{seed}:{domain}".encode("utf-8")).hexdigest()[:2], 16)
            candidates.append(
                {
                    "domain": domain,
                    "why": "Generated from your brief while the naming model is busy.",
                    "strategy": strategy,
                    "score": 60 + (score_seed % 31),
                }
            )
            if len(candidates) >= count:
                return candidates
    return candidates


def _candidate_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string"},
                        "why": {"type": "string"},
                        "strategy": {"type": "string"},
                        "score": {"type": "integer", "minimum": 1, "maximum": 100},
                    },
                    "required": ["domain", "why", "strategy", "score"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["candidates"],
        "additionalProperties": False,
    }


def build_generation_prompt(
    description: str,
    current_ideas: Iterable[str],
    excluded_domains: Iterable[str],
    inspiration: str,
    count: int,
) -> str:
    ideas = normalize_domains(current_ideas, limit=30)
    excluded = normalize_domains(excluded_domains, limit=120)
    inspiration_text = str(inspiration or "").strip()[:300]
    return (
        "Create a fresh wave of brandable domain candidates. This is an iterative search: "
        "the user may ask for more waves or explore one promising candidate recursively.\n\n"
        f"Business brief:\n{description.strip()[:3000]}\n\n"
        f"Current ideas to learn from (include strong variants, but do not merely add hyphens):\n"
        f"{', '.join(ideas) or 'None'}\n\n"
        f"Explore more like:\n{inspiration_text or 'No single candidate; diversify the first wave.'}\n\n"
        f"Never repeat these already-seen domains:\n{', '.join(excluded) or 'None'}\n\n"
        f"Return exactly {count} candidates. Prefer short, pronounceable names with defensible spelling. "
        "Use .com most often, but include a few relevant alternatives such as .ai, .science, .bio, or .io "
        "when they strengthen the name. Do not claim availability; a separate check will verify it. "
        "Keep each why under 90 characters and each strategy to a 1-3 word label. Return JSON only."
    )


def generate_domain_candidates(
    description: str,
    current_ideas: Iterable[str],
    excluded_domains: Iterable[str],
    *,
    inspiration: str = "",
    count: int = 18,
    safety_identifier: str = "",
    query_json=query_tool_json,
) -> list[dict[str, Any]]:
    count = max(6, min(int(count), 24))
    try:
        result = query_json(
            build_generation_prompt(description, current_ideas, excluded_domains, inspiration, count),
            _candidate_schema(),
            system_message=(
                "You are a naming strategist. Produce distinct, useful domain ideas. "
                "Never claim that a domain is available."
            ),
            model=DEFAULT_DOMAIN_MODEL,
            max_tokens=4200,
            temperature=0.8,
        )
        parsed = result.data
    except ToolAIError as exc:
        logger.warning("Domain generation request failed: %s", exc)
        raise DomainSearchError("We couldn't create names right now.") from exc
    except (ValueError, TypeError, KeyError) as exc:
        raise DomainSearchError("We couldn't read the generated names.") from exc

    excluded = set(normalize_domains(excluded_domains, limit=200))
    candidates: list[dict[str, Any]] = []
    seen = set(excluded)
    for item in parsed.get("candidates") or []:
        if not isinstance(item, dict):
            continue
        domain = normalize_domain(item.get("domain", ""))
        if not domain or domain in seen:
            continue
        seen.add(domain)
        try:
            score = int(float(item.get("score") or 50))
        except (TypeError, ValueError):
            score = 50
        candidates.append(
            {
                "domain": domain,
                "why": str(item.get("why") or "Distinctive, memorable naming direction.")[:160],
                "strategy": str(item.get("strategy") or "Brandable")[:40],
                "score": max(1, min(score, 100)),
            }
        )
        if len(candidates) >= count:
            break
    if not candidates:
        raise DomainSearchError("The naming model did not return any valid new domains.")
    return candidates


def check_domain_availability(
    domain: str,
    *,
    session: requests.Session | None = None,
    timeout: float = 12,
) -> dict[str, str]:
    normalized = normalize_domain(domain)
    if not normalized:
        return {"status": "unknown", "detail": "Invalid domain format"}

    http = session or requests
    tld = normalized.rsplit(".", 1)[-1]
    base_url = RDAP_DOMAIN_URL or RDAP_SERVERS.get(tld, "https://rdap.org/domain/")
    try:
        response = http.get(
            f"{base_url.rstrip('/')}/{quote(normalized, safe='')}",
            headers={"Accept": "application/rdap+json, application/json", "User-Agent": "text-generator-domain-search/1.0"},
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException:
        return {"status": "unknown", "detail": "Registry check unavailable"}

    if response.status_code == 200:
        return {"status": "taken", "detail": "Found in registry"}
    if response.status_code == 404:
        return {"status": "available", "detail": "No registry record found"}
    if response.status_code == 429:
        return {"status": "unknown", "detail": "Registry rate limited the check"}
    return {"status": "unknown", "detail": f"Registry returned HTTP {response.status_code}"}


def check_candidates(candidates: list[dict[str, Any]], *, workers: int = 10) -> list[dict[str, Any]]:
    checked: list[dict[str, Any] | None] = [None] * len(candidates)
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(candidates) or 1))) as pool:
        futures = {
            pool.submit(check_domain_availability, candidate["domain"]): index
            for index, candidate in enumerate(candidates)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                availability = future.result()
            except Exception:
                availability = {"status": "unknown", "detail": "Registry check failed"}
            checked[index] = {**candidates[index], **availability}
    return [item for item in checked if item is not None]


def safety_identifier_for(value: str) -> str:
    salt = os.getenv("DOMAIN_SEARCH_SAFETY_SALT", "text-generator-domain-search")
    return "domain_" + hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:32]


def run_domain_search(
    description: str,
    current_ideas: Iterable[str],
    excluded_domains: Iterable[str],
    *,
    inspiration: str = "",
    count: int = 18,
    safety_identifier: str = "",
) -> dict[str, Any]:
    description = str(description or "").strip()
    if not description:
        raise DomainSearchError("Describe the business or product you want to name.")

    ideas = normalize_domains(current_ideas, limit=30)
    excluded = normalize_domains(excluded_domains, limit=120)
    used_fallback = False
    try:
        generated = generate_domain_candidates(
            description,
            ideas,
            excluded,
            inspiration=inspiration,
            count=count,
            safety_identifier=safety_identifier,
        )
    except DomainSearchError as exc:
        logger.warning("Using local domain candidate fallback after model failure: %s", exc)
        generated = generate_fallback_domain_candidates(
            description,
            ideas,
            excluded,
            inspiration=inspiration,
            count=count,
        )
        used_fallback = True
        if not generated:
            raise

    # On the first wave, include the user's seeds so the output immediately answers
    # whether their existing ideas are worth keeping.
    if not excluded:
        generated_domains = {item["domain"] for item in generated}
        seed_items = [
            {
                "domain": domain,
                "why": "Starting idea supplied by you.",
                "strategy": "Seed idea",
                "score": 50,
            }
            for domain in ideas
            if domain not in generated_domains
        ]
        generated = seed_items + generated

    results = check_candidates(generated)
    return {
        "domains": results,
        "model": DEFAULT_DOMAIN_MODEL,
        "checked": len(results),
        "available": sum(item["status"] == "available" for item in results),
        "fallback": used_fallback,
    }
