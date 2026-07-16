"""Multi-provider chat routing with semantic auto-model selection and failover."""

from __future__ import annotations

import logging
import os
import sys
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests

from questions.provider_catalog import (
    MODELS,
    MODELS_BY_ID,
    PROVIDERS_BY_SLUG,
    ModelDefinition,
    ProviderDefinition,
    resolve_model,
)

logger = logging.getLogger(__name__)


AUTO_ROUTE_ENTRIES: dict[str, tuple[tuple[str, str], ...]] = {
    "balanced": (
        ("quick fact lookup classification extraction formatting translation summary simple question", "gemini-2.5-flash"),
        ("implement feature endpoint api integration database backend code refactor", "gpt-5.4-mini"),
        ("code review security architecture authentication complex debugging", "claude-sonnet-latest"),
        ("mathematics proof difficult reasoning planning strategy multi-step analysis", "deepseek-reasoner"),
        ("image screenshot chart document OCR visual understanding", "gemini-2.5-pro"),
        ("friendly conversation writing marketing email brainstorm general chat", "deepseek-chat"),
    ),
    "fast": (
        ("instant assistant conversation short response extract classify format", "deepseek-chat"),
        ("vision OCR screenshot quick image caption", "gemini-2.5-flash"),
        ("tiny code edit regex shell command git configuration", "gpt-4o-mini"),
    ),
    "cheap": (
        ("classification extraction formatting grammar translate summarize list", "gemini-2.5-flash"),
        ("short chat answer simple code edit", "gpt-4o-mini"),
        ("very fast tiny request low latency", "llama-3.1-8b-instant"),
    ),
    "code": (
        ("small edit boilerplate test regex config shell git", "gpt-4o-mini"),
        ("feature endpoint database integration refactor debug", "gpt-5.4-mini"),
        ("review security architecture authentication distributed system", "claude-sonnet-latest"),
        ("code completion repository programming implementation", "codestral-latest"),
        ("hard algorithm proof performance concurrency", "deepseek-reasoner"),
    ),
    "reasoning": (
        ("moderate analysis planning compare options explain tradeoffs", "gpt-5.4-mini"),
        ("hard mathematics proof algorithm logic puzzle", "deepseek-reasoner"),
        ("architecture security policy nuanced judgement long horizon", "claude-opus-latest"),
        ("multimodal reasoning chart scientific document", "gemini-2.5-pro"),
    ),
    "vision": (
        ("OCR screenshot thumbnail caption document receipt text image", "gemini-2.5-flash"),
        ("complex visual reasoning chart diagram scientific image", "gemini-2.5-pro"),
        ("general photo understanding visual conversation", "gpt-4o"),
        ("document image analysis European model", "pixtral-large-latest"),
    ),
}


class ProviderRoutingError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class RoutedChatResult:
    data: dict[str, Any]
    requested_model: str
    selected_model: str
    provider: str


@lru_cache(maxsize=1)
def _openpaths_environment() -> dict[str, str]:
    """Load the sibling OpenPaths env without copying or logging credentials."""
    try:
        from dotenv import dotenv_values

        default_path = Path(__file__).resolve().parents[2] / "openpaths" / ".env"
        env_path = Path(os.getenv("OPENPATHS_ENV_FILE", str(default_path)))
        if env_path.is_file():
            return {
                key: str(value)
                for key, value in dotenv_values(env_path).items()
                if value
            }
    except Exception as exc:
        logger.debug("OpenPaths provider environment was not loaded: %s", exc)
    return {}


def _sellerinfo_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import sellerinfo

        candidate = getattr(sellerinfo, name, "")
        if isinstance(candidate, str) and candidate and candidate != "toset":
            return candidate.strip()
    except Exception:
        pass
    return _openpaths_environment().get(name, "").strip()


def provider_api_key(provider: ProviderDefinition) -> str:
    for name in provider.secret_names:
        value = _sellerinfo_value(name)
        if value:
            return value
    return ""


def configured_provider_slugs() -> set[str]:
    return {
        provider.slug
        for provider in PROVIDERS_BY_SLUG.values()
        if provider_api_key(provider)
    }


class SemanticAutoRouter:
    """Lazy pybed selector with a deterministic lexical fallback.

    pybed's model owns a reusable int16 token buffer, so embedding calls are
    serialized.  The catalogue is tiny and the lock is held for microseconds.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loaded = False
        self._model = None
        self._indexes: dict[str, Any] = {}
        self._entries: dict[str, tuple[tuple[str, str], ...]] = AUTO_ROUTE_ENTRIES

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            try:
                from pybed import CagraIndex, EmbedModel
            except ImportError:
                # Convenient for a source checkout where lee101/pybed is a
                # sibling; production installs pybed from requirements.txt.
                sibling = Path(__file__).resolve().parents[2] / "pybed"
                if sibling.exists():
                    sys.path.insert(0, str(sibling))
                from pybed import CagraIndex, EmbedModel

            import numpy as np

            default_model_dir = Path(__file__).resolve().parents[2] / "pybed" / "model"
            model_dir = Path(os.getenv("PYBED_MODEL_DIR", str(default_model_dir)))
            self._model = EmbedModel.from_dir(model_dir)
            for profile, entries in self._entries.items():
                vectors = np.stack([
                    self._model.embed_quantized(description)[0]
                    for description, _ in entries
                ])
                degree = max(2, min(8, len(entries) - 1))
                self._indexes[profile] = CagraIndex(vectors, degree=degree)
            logger.info("Provider auto-router initialized with pybed CAGRA indexes")
        except Exception as exc:
            self._model = None
            self._indexes = {}
            logger.warning("pybed auto-router unavailable; using lexical routing: %s", exc)

    @staticmethod
    def _lexical_score(prompt: str, description: str) -> int:
        prompt_terms = set(prompt.lower().replace("/", " ").replace("_", " ").split())
        return sum(term in prompt_terms for term in description.split())

    def select(self, profile: str, prompt: str) -> str:
        entries = self._entries.get(profile) or self._entries["balanced"]
        with self._lock:
            self._load()
            if self._model is not None and profile in self._indexes:
                query, _, norm = self._model.embed_quantized(prompt or "general assistant chat")
                result = self._indexes[profile].search(query, norm, top_k=1)
                if result:
                    return entries[result[0].doc_idx][1]

        return max(entries, key=lambda entry: self._lexical_score(prompt, entry[0]))[1]


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces: list[str] = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
                if text:
                    pieces.append(str(text))
                elif part.get("type") in {"image_url", "image", "input_image"}:
                    pieces.append("image visual screenshot OCR")
        return " ".join(pieces)
    return str(content or "")


def _anthropic_content(content: Any) -> str | list[dict[str, Any]]:
    """Translate OpenAI text/image content parts to Anthropic's native shape."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return _message_text(content)

    translated: list[dict[str, Any]] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        part_type = part.get("type")
        if part_type in {"text", "input_text"} and part.get("text") is not None:
            translated.append({"type": "text", "text": str(part["text"])})
            continue
        if part_type == "image" and isinstance(part.get("source"), dict):
            translated.append({"type": "image", "source": part["source"]})
            continue
        if part_type not in {"image_url", "input_image", "image"}:
            continue
        image_value = part.get("image_url") or part.get("url")
        if isinstance(image_value, dict):
            image_value = image_value.get("url")
        if not isinstance(image_value, str) or not image_value:
            continue
        if image_value.startswith("data:") and ";base64," in image_value:
            metadata, data = image_value.split(",", 1)
            media_type = metadata[5:].split(";", 1)[0] or "image/jpeg"
            source = {"type": "base64", "media_type": media_type, "data": data}
        else:
            source = {"type": "url", "url": image_value}
        translated.append({"type": "image", "source": source})
    return translated or _message_text(content)


def prompt_from_messages(messages: list[dict[str, Any]]) -> str:
    user_messages = [
        _message_text(message.get("content"))
        for message in messages
        if message.get("role") == "user"
    ]
    return "\n".join(user_messages[-2:])[-12000:]


def _is_reasoning_model(model_id: str) -> bool:
    return model_id.startswith(("o1", "o3", "o4", "gpt-5")) and not model_id.startswith("gpt-5-chat")


class ProviderRouter:
    def __init__(self, *, timeout: float | None = None, session: requests.Session | None = None) -> None:
        self.timeout = timeout or float(os.getenv("PROVIDER_ROUTER_TIMEOUT", "300"))
        self.session = session or requests.Session()
        self.auto_router = SemanticAutoRouter()

    def can_route(self, model_id: str) -> bool:
        return resolve_model(model_id) is not None

    def configured_providers(self) -> set[str]:
        return configured_provider_slugs()

    def resolve(self, model_id: str, messages: list[dict[str, Any]]) -> tuple[str, list[ModelDefinition]]:
        requested = resolve_model(model_id)
        if requested is None:
            raise ProviderRoutingError(f"Unknown routed model: {model_id}", status_code=404)

        selected = requested
        if requested.auto_profile:
            selected_id = self.auto_router.select(requested.auto_profile, prompt_from_messages(messages))
            selected = MODELS_BY_ID.get(selected_id, requested)

        candidates: list[ModelDefinition] = []
        seen: set[str] = set()

        def add(model: ModelDefinition | None) -> None:
            if model is None or model.id in seen or model.auto_profile:
                return
            seen.add(model.id)
            candidates.append(model)
            for fallback_id in model.fallback_models:
                add(resolve_model(fallback_id))

        add(selected)
        if selected.id != requested.id:
            for fallback_id in requested.fallback_models:
                add(resolve_model(fallback_id))
        return selected.id, candidates

    def chat_completion(self, payload: dict[str, Any]) -> RoutedChatResult:
        requested_model = str(payload.get("model") or "text-generator/auto")
        messages = list(payload.get("messages") or [])
        selected_model, candidates = self.resolve(requested_model, messages)
        configured = self.configured_providers()
        attempted: list[str] = []
        last_error: ProviderRoutingError | None = None

        for candidate in candidates:
            if candidate.provider not in configured:
                continue
            provider = PROVIDERS_BY_SLUG[candidate.provider]
            attempted.append(f"{provider.name}/{candidate.id}")
            try:
                data = self._request_provider(provider, candidate, payload)
                data["model"] = candidate.id
                data["provider"] = provider.slug
                data["routing"] = {
                    "requested_model": requested_model,
                    "selected_model": candidate.id,
                    "auto_selected_model": selected_model,
                }
                return RoutedChatResult(data, requested_model, candidate.id, provider.slug)
            except ProviderRoutingError as exc:
                last_error = exc
                if exc.status_code not in {402, 408, 409, 429, 500, 502, 503, 504}:
                    raise
                logger.warning("Provider route %s failed: %s", attempted[-1], exc)

        if not attempted:
            raise ProviderRoutingError(
                "No configured provider is available for this model. Add a provider API key to the environment.",
                status_code=503,
            )
        raise last_error or ProviderRoutingError(f"All provider routes failed: {', '.join(attempted)}")

    def _request_provider(
        self,
        provider: ProviderDefinition,
        model: ModelDefinition,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        api_key = provider_api_key(provider)
        if provider.api_style == "anthropic":
            return self._request_anthropic(provider, model, payload, api_key)
        return self._request_openai_compatible(provider, model, payload, api_key)

    def _request_openai_compatible(
        self,
        provider: ProviderDefinition,
        model: ModelDefinition,
        payload: dict[str, Any],
        api_key: str,
    ) -> dict[str, Any]:
        body = dict(payload)
        body["model"] = model.provider_model_id
        body["stream"] = False
        for field in ("system_message", "system_prompt", "top_k", "enable_thinking", "routing_strategy", "task_tier"):
            body.pop(field, None)
        if _is_reasoning_model(model.provider_model_id):
            if body.get("max_tokens") and not body.get("max_completion_tokens"):
                body["max_completion_tokens"] = body.pop("max_tokens")
            for field in ("temperature", "top_p", "presence_penalty", "frequency_penalty"):
                body.pop(field, None)

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if provider.slug == "openrouter":
            headers["HTTP-Referer"] = os.getenv("OPENROUTER_APP_REFERER", "https://text-generator.io")
            headers["X-Title"] = os.getenv("OPENROUTER_APP_TITLE", "Text Generator")

        return self._post_json(provider, provider.chat_url, body, headers)

    def _request_anthropic(
        self,
        provider: ProviderDefinition,
        model: ModelDefinition,
        payload: dict[str, Any],
        api_key: str,
    ) -> dict[str, Any]:
        system_parts: list[str] = []
        messages: list[dict[str, Any]] = []
        for message in payload.get("messages") or []:
            if message.get("role") == "system":
                system_parts.append(_message_text(message.get("content")))
            else:
                messages.append({
                    "role": message.get("role", "user"),
                    "content": _anthropic_content(message.get("content", "")),
                })

        body: dict[str, Any] = {
            "model": model.provider_model_id,
            "messages": messages,
            "max_tokens": payload.get("max_tokens") or 4096,
        }
        if system_parts:
            body["system"] = "\n\n".join(system_parts)
        for field in ("temperature", "top_p", "stop_sequences", "tools", "tool_choice"):
            if payload.get(field) is not None:
                body[field] = payload[field]

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        native = self._post_json(provider, provider.chat_url, body, headers)
        text_parts = [part.get("text", "") for part in native.get("content", []) if part.get("type") == "text"]
        return {
            "id": native.get("id", ""),
            "object": "chat.completion",
            "created": 0,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "".join(text_parts)},
                "finish_reason": native.get("stop_reason") or "stop",
            }],
            "usage": {
                "prompt_tokens": (native.get("usage") or {}).get("input_tokens", 0),
                "completion_tokens": (native.get("usage") or {}).get("output_tokens", 0),
                "total_tokens": (
                    (native.get("usage") or {}).get("input_tokens", 0)
                    + (native.get("usage") or {}).get("output_tokens", 0)
                ),
            },
        }

    def _post_json(
        self,
        provider: ProviderDefinition,
        url: str,
        body: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        try:
            response = self.session.post(url, json=body, headers=headers, timeout=self.timeout)
        except requests.Timeout as exc:
            raise ProviderRoutingError(f"{provider.name} timed out", status_code=504) from exc
        except requests.RequestException as exc:
            raise ProviderRoutingError(f"{provider.name} is unavailable", status_code=502) from exc

        if response.status_code >= 400:
            message = ""
            try:
                error_data = response.json()
                error = error_data.get("error", error_data)
                message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            except Exception:
                message = (response.text or response.reason or "upstream error")[:500]
            raise ProviderRoutingError(
                f"{provider.name}: {message}",
                status_code=response.status_code,
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderRoutingError(f"{provider.name} returned invalid JSON", status_code=502) from exc
        if not isinstance(data, dict):
            raise ProviderRoutingError(f"{provider.name} returned an invalid response", status_code=502)
        return data


_provider_router: ProviderRouter | None = None
_provider_router_lock = threading.Lock()


def get_provider_router() -> ProviderRouter:
    global _provider_router
    if _provider_router is None:
        with _provider_router_lock:
            if _provider_router is None:
                _provider_router = ProviderRouter()
    return _provider_router
