"""Small JSON-generation helper for first-party AI tools."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any

from questions.provider_router import ProviderRoutingError, get_provider_router


DEFAULT_TOOL_MODEL = "deepseek-chat"

# Default for plain text continuation endpoints. Routed through the provider
# router, so a caller can still name any catalogue model (including Claude).
DEFAULT_TEXT_MODEL = "gpt-5.6-luna"


class ToolAIError(RuntimeError):
    """Raised when a tool model cannot return usable structured output."""


@dataclass(frozen=True)
class ToolJSONResult:
    data: dict[str, Any]
    model: str
    provider: str


@dataclass(frozen=True)
class ToolTextResult:
    text: str
    model: str
    provider: str


def _message_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(part.get("text") or "")
            for part in content
            if isinstance(part, dict) and part.get("text")
        ).strip()
    return str(content or "").strip()


def _parse_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ToolAIError("The AI returned an invalid response.") from exc
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as nested_exc:
            raise ToolAIError("The AI returned an invalid response.") from nested_exc
    if not isinstance(parsed, dict):
        raise ToolAIError("The AI returned an invalid response.")
    return parsed


def query_tool_json(
    prompt: str,
    schema: dict[str, Any],
    *,
    system_message: str,
    model: str = DEFAULT_TOOL_MODEL,
    max_tokens: int = 4096,
    temperature: float = 0.5,
) -> ToolJSONResult:
    schema_text = json.dumps(schema, separators=(",", ":"), ensure_ascii=False)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"{system_message}\nReturn only one JSON object matching this schema: {schema_text}"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": max(128, min(int(max_tokens), 8192)),
        "temperature": max(0.0, min(float(temperature), 1.5)),
    }
    try:
        result = get_provider_router().chat_completion(payload)
    except ProviderRoutingError as exc:
        raise ToolAIError("The AI service is busy. Please try again.") from exc

    content = _message_content(result.data)
    if not content:
        raise ToolAIError("The AI returned an empty response.")
    return ToolJSONResult(
        data=_parse_json_object(content),
        model=result.selected_model,
        provider=result.provider,
    )


async def query_tool_json_async(*args, **kwargs) -> ToolJSONResult:
    return await asyncio.to_thread(query_tool_json, *args, **kwargs)


def query_text(
    prompt: str,
    *,
    system_message: str,
    model: str = DEFAULT_TEXT_MODEL,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    stop_sequences: Any = None,
) -> ToolTextResult:
    """Free-form continuation through the provider router.

    Unlike query_tool_json this imposes no response format, so it suits the
    public text-continuation endpoints. The router resolves the model from the
    catalogue and walks its fallback chain, so any provider (OpenAI, Anthropic,
    Google, ...) is reachable by model id alone.
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max(16, min(int(max_tokens), 128000)),
        "temperature": max(0.0, min(float(temperature), 1.5)),
    }
    stops = [str(s) for s in (stop_sequences or []) if str(s)]
    if stops:
        payload["stop"] = stops[:4]
    try:
        result = get_provider_router().chat_completion(payload)
    except ProviderRoutingError as exc:
        raise ToolAIError("The AI service is busy. Please try again.") from exc

    content = _message_content(result.data)
    if not content:
        raise ToolAIError("The AI returned an empty response.")
    return ToolTextResult(text=content, model=result.selected_model, provider=result.provider)


async def query_text_async(*args, **kwargs) -> ToolTextResult:
    return await asyncio.to_thread(query_text, *args, **kwargs)
