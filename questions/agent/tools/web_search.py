"""Web search tool — searches the web and returns results."""

import json
import os

from questions.agent.registry import registry


def _check_available() -> bool:
    return bool(os.getenv("SERPER_API_KEY") or os.getenv("TAVILY_API_KEY"))


def web_search_handler(args: dict, **kwargs) -> str:
    """Search the web. Uses Serper or Tavily depending on available keys."""
    query = args.get("query", "")
    max_results = args.get("max_results", 5)

    if not query:
        return json.dumps({"error": "No query provided"})

    # Try Serper first
    serper_key = kwargs.get("api_key") or os.getenv("SERPER_API_KEY")
    if serper_key:
        return _search_serper(query, max_results, serper_key)

    # Try Tavily
    tavily_key = kwargs.get("api_key") or os.getenv("TAVILY_API_KEY")
    if tavily_key:
        return _search_tavily(query, max_results, tavily_key)

    return json.dumps({"error": "No search API key configured. Add your own via BYOK."})


def _search_serper(query: str, max_results: int, api_key: str) -> str:
    import requests

    resp = requests.post(
        "https://google.serper.dev/search",
        json={"q": query, "num": max_results},
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("organic", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
        )
    return json.dumps({"results": results, "query": query})


def _search_tavily(query: str, max_results: int, api_key: str) -> str:
    import requests

    resp = requests.post(
        "https://api.tavily.com/search",
        json={"query": query, "max_results": max_results, "api_key": api_key},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("results", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:500],
            }
        )
    return json.dumps({"results": results, "query": query})


SCHEMA = {
    "name": "web_search",
    "description": "Search the web for information. Returns titles, URLs, and snippets.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

registry.register(
    name="web_search",
    toolset="web",
    schema=SCHEMA,
    handler=web_search_handler,
    description="Search the web for information",
    check_fn=_check_available,
    requires_byok=True,
)
