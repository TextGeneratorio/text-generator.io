import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from questions.logging_config import get_logger

logger = get_logger(__name__)

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_PLANNER_MODEL = os.getenv("DEEP_RESEARCH_PLANNER_MODEL", "gpt-5-nano")
DEFAULT_ANALYST_MODEL = os.getenv("DEEP_RESEARCH_ANALYST_MODEL", "gpt-5-mini")
DEFAULT_WRITER_MODEL = os.getenv("DEEP_RESEARCH_WRITER_MODEL", "gpt-5.4")
DEFAULT_MAX_SOURCES = int(os.getenv("DEEP_RESEARCH_MAX_SOURCES", "6"))
USER_AGENT = os.getenv(
    "DEEP_RESEARCH_USER_AGENT",
    (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
)

class DeepResearchError(RuntimeError):
    pass


@dataclass
class ResearchTrace:
    label: str
    details: str


@dataclass
class ResearchSource:
    title: str
    url: str
    domain: str
    query: str
    snippet: str
    image_url: Optional[str] = None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def trim_text(value: str, limit: int) -> str:
    value = clean_text(value)
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def extract_json_object(raw_text: str) -> Dict[str, Any]:
    if not raw_text:
        raise DeepResearchError("Model returned an empty response.")

    candidate = raw_text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
        candidate = re.sub(r"```$", "", candidate).strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise DeepResearchError("Model response did not contain a JSON object.")

    return json.loads(candidate[start : end + 1])


def render_history(messages: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    for message in messages[-6:]:
        role = clean_text(message.get("role", "user")).lower() or "user"
        content = trim_text(message.get("content", ""), 2200)
        if not content:
            continue
        lines.append(f"{role.upper()}: {content}")
    return "\n\n".join(lines)


def call_openai_text(
    *,
    model: str,
    instructions: str,
    prompt: str,
    max_output_tokens: int,
    reasoning_effort: Optional[str] = None,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise DeepResearchError("OPENAI_API_KEY is not configured on the server.")

    kwargs: Dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "store": False,
    }
    if reasoning_effort:
        kwargs["reasoning"] = {"effort": reasoning_effort}

    response = requests.post(
        OPENAI_RESPONSES_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=kwargs,
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()

    output_text = clean_text(payload.get("output_text", ""))
    if not output_text:
        output_parts: List[str] = []
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for content_item in item.get("content", []):
                if content_item.get("type") == "output_text":
                    output_parts.append(content_item.get("text", ""))
        output_text = "\n".join(part for part in output_parts if part).strip()

    if not output_text.strip():
        raise DeepResearchError(f"{model} returned no text output.")
    return output_text


def build_plan(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    history = render_history(messages)
    planner_prompt = (
        "You are planning a web research job for a general-purpose research assistant.\n"
        "Return JSON only with this exact shape:\n"
        "{\n"
        '  "title": "short report title",\n'
        '  "user_question": "restated question",\n'
        '  "complexity": "low|medium|high",\n'
        '  "angle": "what the report should emphasize",\n'
        '  "search_queries": ["query 1", "query 2", "query 3"],\n'
        '  "must_cover": ["point 1", "point 2"],\n'
        '  "answer_format": "preferred report shape"\n'
        "}\n"
        "Keep it concise and practical. Use 2-4 search queries. Optimize for trustworthy web research."
        "\n\nConversation:\n"
        f"{history}"
    )
    raw = call_openai_text(
        model=DEFAULT_PLANNER_MODEL,
        instructions="Return JSON only. Do not wrap it in markdown fences.",
        prompt=planner_prompt,
        max_output_tokens=900,
        reasoning_effort="low",
    )
    plan = extract_json_object(raw)
    queries = [clean_text(item) for item in plan.get("search_queries", []) if clean_text(item)]
    latest_user = next((msg.get("content", "") for msg in reversed(messages) if msg.get("role") == "user"), "").strip()
    if latest_user and latest_user not in queries:
        queries.insert(0, latest_user)
    plan["search_queries"] = queries[:4] if queries else [latest_user]
    plan["title"] = clean_text(plan.get("title", "")) or "Deep Research Report"
    plan["user_question"] = clean_text(plan.get("user_question", "")) or latest_user
    plan["complexity"] = clean_text(plan.get("complexity", "medium")).lower() or "medium"
    plan["angle"] = clean_text(plan.get("angle", "Answer directly and cite reliable sources."))
    plan["must_cover"] = [clean_text(item) for item in plan.get("must_cover", []) if clean_text(item)]
    plan["answer_format"] = clean_text(plan.get("answer_format", "Executive summary followed by evidence-backed sections."))
    return plan


def normalize_search_result_url(raw_url: str) -> Optional[str]:
    if not raw_url:
        return None
    candidate = raw_url.strip()
    if candidate.startswith("//"):
        candidate = "https:" + candidate
    if candidate.startswith("/l/?"):
        candidate = "https://duckduckgo.com" + candidate
    if "duckduckgo.com/l/?" in candidate:
        parsed = urlparse(candidate)
        params = parse_qs(parsed.query)
        uddg = params.get("uddg", [])
        if uddg:
            return unquote(uddg[0])
    if candidate.startswith("http://") or candidate.startswith("https://"):
        return candidate
    return None


def search_web(query: str, max_results: int) -> List[Dict[str, str]]:
    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results: List[Dict[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.select("a.result__a"):
        url = normalize_search_result_url(anchor.get("href", ""))
        title = clean_text(anchor.get_text(" ", strip=True))
        if not url or not title or url in seen:
            continue
        seen.add(url)
        results.append({"title": title, "url": url})
        if len(results) >= max_results:
            break
    return results


def fetch_with_lynx(url: str) -> str:
    if not shutil.which("lynx"):
        return ""
    try:
        result = subprocess.run(
            ["lynx", "-dump", "-nolist", url],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        logger.warning("lynx failed for %s: %s", url, exc)
        return ""

    if result.returncode != 0:
        return ""
    return result.stdout or ""


def extract_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "footer", "nav", "header"]):
        tag.decompose()
    return clean_text(soup.get_text(" "))


def extract_image_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    for selector in (
        'meta[property="og:image"]',
        'meta[name="twitter:image"]',
        'meta[property="og:image:url"]',
    ):
        tag = soup.select_one(selector)
        if tag and tag.get("content"):
            return urljoin(base_url, tag["content"])
    return None


def fetch_source(result: Dict[str, str], query: str) -> Optional[ResearchSource]:
    try:
        response = requests.get(
            result["url"],
            headers={"User-Agent": USER_AGENT},
            timeout=20,
            allow_redirects=True,
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", result.get("url"), exc)
        return None

    content_type = response.headers.get("content-type", "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return None

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    title = clean_text(result.get("title") or (soup.title.get_text(" ", strip=True) if soup.title else ""))
    text = fetch_with_lynx(response.url) or extract_html_text(html)
    snippet = trim_text(text, 560)
    if len(snippet) < 120:
        return None

    return ResearchSource(
        title=title or urlparse(response.url).netloc,
        url=response.url,
        domain=urlparse(response.url).netloc,
        query=query,
        snippet=snippet,
        image_url=extract_image_url(soup, response.url),
    )


def collect_sources(plan: Dict[str, Any], max_sources: int) -> List[ResearchSource]:
    sources: List[ResearchSource] = []
    seen: set[str] = set()
    for query in plan.get("search_queries", []):
        try:
            search_results = search_web(query, max_results=max_sources)
        except Exception as exc:
            logger.warning("Search failed for %s: %s", query, exc)
            continue

        for result in search_results:
            source = fetch_source(result, query)
            if not source or source.url in seen:
                continue
            seen.add(source.url)
            sources.append(source)
            if len(sources) >= max_sources:
                return sources
    return sources


def distill_sources(plan: Dict[str, Any], sources: List[ResearchSource]) -> Dict[str, Any]:
    analyst_payload = {
        "question": plan.get("user_question"),
        "angle": plan.get("angle"),
        "must_cover": plan.get("must_cover", []),
        "sources": [
            {
                "source_index": index + 1,
                "title": source.title,
                "url": source.url,
                "domain": source.domain,
                "query": source.query,
                "snippet": source.snippet,
            }
            for index, source in enumerate(sources)
        ],
    }
    raw = call_openai_text(
        model=DEFAULT_ANALYST_MODEL,
        instructions="Return JSON only. Keep summaries factual and grounded in the provided source snippets.",
        prompt=(
            "Review the research sources and return JSON only in this shape:\n"
            "{\n"
            '  "overview": "1-2 sentence synthesis",\n'
            '  "key_findings": [{"finding": "...", "source_indices": [1,2]}],\n'
            '  "open_questions": ["gap or caveat"],\n'
            '  "recommended_images": [1,2]\n'
            "}\n\n"
            f"{json.dumps(analyst_payload, ensure_ascii=True)}"
        ),
        max_output_tokens=1400,
        reasoning_effort="medium",
    )
    analysis = extract_json_object(raw)
    analysis["overview"] = clean_text(analysis.get("overview", ""))
    return analysis


def build_report(plan: Dict[str, Any], analysis: Dict[str, Any], sources: List[ResearchSource]) -> str:
    writer_payload = {
        "title": plan.get("title"),
        "question": plan.get("user_question"),
        "angle": plan.get("angle"),
        "answer_format": plan.get("answer_format"),
        "must_cover": plan.get("must_cover", []),
        "analysis": analysis,
        "sources": [
            {
                "source_index": index + 1,
                "title": source.title,
                "url": source.url,
                "domain": source.domain,
                "snippet": source.snippet,
            }
            for index, source in enumerate(sources)
        ],
    }
    return call_openai_text(
        model=DEFAULT_WRITER_MODEL,
        instructions=(
            "Write a rigorous markdown research report. Use only the evidence provided. "
            "Cite sources inline as [Source N](url). If evidence is thin or conflicting, say so plainly. "
            "Do not include markdown images."
        ),
        prompt=(
            "Create a polished report with these sections when relevant:\n"
            "- Title\n"
            "- TL;DR\n"
            "- Key Findings\n"
            "- Important Context / Caveats\n"
            "- Practical Takeaways or Next Steps\n"
            "- Sources\n\n"
            f"{json.dumps(writer_payload, ensure_ascii=True)}"
        ),
        max_output_tokens=2400,
        reasoning_effort="medium",
    ).strip()


def select_image_urls(sources: List[ResearchSource], analysis: Dict[str, Any]) -> List[str]:
    preferred = analysis.get("recommended_images", [])
    selected: List[str] = []
    seen: set[str] = set()

    def maybe_add(source_index: int) -> None:
        if source_index < 1 or source_index > len(sources):
            return
        image_url = sources[source_index - 1].image_url
        if image_url and image_url not in seen:
            seen.add(image_url)
            selected.append(image_url)

    for source_index in preferred:
        if isinstance(source_index, int):
            maybe_add(source_index)

    for source in sources:
        if source.image_url and source.image_url not in seen:
            seen.add(source.image_url)
            selected.append(source.image_url)
        if len(selected) >= 6:
            break

    return selected[:6]


def run_deep_research(messages: List[Dict[str, str]], max_sources: int = DEFAULT_MAX_SOURCES) -> Dict[str, Any]:
    if not messages:
        raise DeepResearchError("No messages were provided.")

    plan = build_plan(messages)
    sources = collect_sources(plan, max_sources=max(2, min(max_sources, 8)))
    if not sources:
        raise DeepResearchError("No useful web sources were found for that research request.")

    analysis = distill_sources(plan, sources)
    report_markdown = build_report(plan, analysis, sources)

    trace = [
        ResearchTrace(
            label="Plan",
            details=f"{plan['title']} | queries: " + "; ".join(plan.get("search_queries", [])),
        ),
        ResearchTrace(
            label="Evidence",
            details=analysis.get("overview", "Collected and distilled the top web sources."),
        ),
        ResearchTrace(
            label="Writeup",
            details=f"Drafted report with {len(sources)} cited sources using {DEFAULT_WRITER_MODEL}.",
        ),
    ]

    images = select_image_urls(sources, analysis)
    return {
        "question": plan.get("user_question"),
        "title": plan.get("title"),
        "report_markdown": report_markdown,
        "sources": [asdict(source) for source in sources],
        "images": images,
        "trace": [asdict(item) for item in trace],
        "models": {
            "planner": DEFAULT_PLANNER_MODEL,
            "analyst": DEFAULT_ANALYST_MODEL,
            "writer": DEFAULT_WRITER_MODEL,
        },
    }
