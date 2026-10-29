"""Credit-billed image, video and LLM tools backed by the OpenPaths API.

Prices are OpenPaths list prices (USD). Users are charged ``cost * MARKUP`` in
credit cents (1 credit == 1 cent), rounded up, minimum 1.
"""
from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests

OPENPATHS_API_BASE = os.environ.get("OPENPATHS_API_BASE", "https://openpaths.io/v1").rstrip("/")
MARKUP = float(os.environ.get("OPENPATHS_TOOLS_MARKUP", "1.6"))
MAX_VIDEO_SECONDS = 10


def openpaths_key() -> str:
    from questions.provider_router import _sellerinfo_value  # env, sellerinfo, then ../openpaths/.env

    return _sellerinfo_value("OPENPATHS_API_KEY")


@dataclass(frozen=True)
class MediaModel:
    id: str
    name: str
    kind: str  # image | video
    mode: str  # text | image  (video input)
    usd: float  # per image, or per second at the default resolution
    resolution: str = ""
    note: str = ""


IMAGE_MODELS: tuple[MediaModel, ...] = (
    MediaModel("zimage", "Z-Image", "image", "text", 0.007, note="Fast photoreal"),
    MediaModel("grok-imagine-image", "Grok Imagine", "image", "text", 0.02, note="xAI, strong prompt following"),
    MediaModel("qwen-image-3.0", "Qwen Image 3.0", "image", "text", 0.03, note="Great text rendering"),
    MediaModel("gemini-nano-banana-2.1", "Nano Banana 2.1", "image", "text", 0.0336, note="Google Gemini image"),
    MediaModel("gpt-image-2", "GPT Image 2", "image", "text", 0.211, note="OpenAI flagship"),
)

VIDEO_MODELS: tuple[MediaModel, ...] = (
    MediaModel("minimax-h3-max", "MiniMax H3 Max", "video", "text", 0.05, "480p", "Cheapest text to video"),
    MediaModel("wan-3.0-text-to-video", "Wan 3.0", "video", "text", 0.05, "480p", "Open model, great value"),
    MediaModel("grok-imagine-video-1.5", "Grok Imagine Video", "video", "text", 0.08, "480p", "xAI video with motion"),
    MediaModel("kling-4.0-text-to-video", "Kling 4.0", "video", "text", 0.157, "720p", "Cinematic 720p"),
    MediaModel("seedance-2.0-fast-text-to-video", "Seedance 2.0 Fast", "video", "text", 0.266, "720p", "ByteDance, high fidelity"),
    MediaModel("minimax-h3-max-image-to-video", "MiniMax H3 Max", "video", "image", 0.05, "480p", "Animate an image, cheapest"),
    MediaModel("wan-3.0-image-to-video", "Wan 3.0", "video", "image", 0.05, "480p", "Animate an image"),
    MediaModel("kling-4.0-image-to-video", "Kling 4.0", "video", "image", 0.157, "720p", "Cinematic image animation"),
    MediaModel("fal-ai/veo3.1/fast/image-to-video", "Veo 3.1 Fast", "video", "image", 0.15, "720p", "Google Veo, with audio"),
    MediaModel("seedance-2.0-image-to-video", "Seedance 2.0", "video", "image", 0.33264, "720p", "ByteDance, high fidelity"),
)


@dataclass(frozen=True)
class ChatModel:
    id: str
    name: str
    usd_in: float  # per 1M tokens
    usd_out: float
    note: str = ""


CHAT_MODELS: tuple[ChatModel, ...] = (
    ChatModel("deepseek-v4-flash", "DeepSeek V4 Flash", 0.15, 0.60, "Fast and cheap"),
    ChatModel("claude-haiku-5-5", "Claude Haiku 5.5", 0.10, 0.50, "Fast Claude"),
    ChatModel("gemini-2.5-flash", "Gemini 2.5 Flash", 0.30, 2.50, "Long context, multimodal"),
    ChatModel("gpt-5.4-mini", "GPT-5.4 mini", 0.75, 4.50, "Balanced OpenAI"),
    ChatModel("deepseek-reasoner", "DeepSeek Reasoner", 0.14, 0.28, "Step-by-step reasoning"),
    ChatModel("claude-opus-5", "Claude Opus 5", 5.00, 25.00, "Deepest reasoning"),
)

IMAGE_SIZES = {"1024x1024", "1344x768", "768x1344"}
ASPECTS = {"1024x1024": "1:1", "1344x768": "16:9", "768x1344": "9:16"}
VIDEO_ASPECTS = {"16:9", "9:16", "1:1"}

# LLM tool presets: each becomes a /tools/<slug> page backed by the chat endpoint.
LLM_TOOLS: dict[str, dict[str, Any]] = {
    "ai-summarizer": {
        "name": "AI Summarizer",
        "description": "Summarize articles, transcripts and documents into key points, TL;DR or executive briefs.",
        "keywords": "ai summarizer, summarize text, tldr generator, article summary",
        "icon": "short_text", "label": "Writing", "accent": "#0ea5e9",
        "placeholder": "Paste the text to summarize...",
        "system": "You summarize text faithfully. Output a one-sentence TL;DR, then 5 concise bullet points, then any action items. Never invent facts.",
        "default_model": "deepseek-v4-flash",
    },
    "ai-translator": {
        "name": "AI Translator",
        "description": "Translate text between 100+ languages with tone and context preserved.",
        "keywords": "ai translator, translate text, language translation, localisation",
        "icon": "translate", "label": "Language", "accent": "#14b8a6",
        "placeholder": "Start with the target language, e.g. 'Spanish: Hello, how are you?'",
        "system": "You are a professional translator. The user's first line names the target language followed by a colon and the text. Translate only the text, preserving tone, formatting and idioms. Output the translation only.",
        "default_model": "claude-haiku-5-5",
    },
    "ai-code-explainer": {
        "name": "AI Code Explainer",
        "description": "Explain code, find bugs and suggest improvements in any language.",
        "keywords": "code explainer, explain code, ai code review, debug code",
        "icon": "code", "label": "Code", "accent": "#6366f1",
        "placeholder": "Paste code and ask what it does or what is wrong...",
        "system": "You are a senior engineer. Explain the code clearly, call out bugs, security issues and performance problems, then give a corrected version in a fenced code block.",
        "default_model": "gpt-5.4-mini",
    },
    "ai-email-writer": {
        "name": "AI Email Writer",
        "description": "Draft clear cold emails, replies and follow-ups from a few bullet points.",
        "keywords": "ai email writer, cold email generator, email reply, follow up email",
        "icon": "mail", "label": "Writing", "accent": "#f43f5e",
        "placeholder": "Who is it for and what do you want to say? Bullet points are fine.",
        "system": "You write concise, warm, professional emails. Give a subject line and the body. Keep it under 150 words unless asked otherwise.",
        "default_model": "claude-haiku-5-5",
    },
    "ai-sql-generator": {
        "name": "AI SQL Generator",
        "description": "Turn plain English and a schema into correct, optimised SQL.",
        "keywords": "ai sql generator, text to sql, sql query builder",
        "icon": "storage", "label": "Code", "accent": "#8b5cf6",
        "placeholder": "Paste your schema, then describe the query you need...",
        "system": "You write correct, efficient SQL. Ask no questions; state any assumptions briefly, then give the query in a fenced sql block and a one-line explanation.",
        "default_model": "deepseek-v4-flash",
    },
    "ai-product-description": {
        "name": "Product Description Writer",
        "description": "Write benefit-led product descriptions and ad copy for any store.",
        "keywords": "product description generator, ecommerce copy, ad copy ai",
        "icon": "storefront", "label": "Marketing", "accent": "#f59e0b",
        "placeholder": "Product name, features, audience and tone...",
        "system": "You are an ecommerce copywriter. Produce a headline, a 60-word benefit-led description, 5 feature bullets and 3 ad copy variants.",
        "default_model": "deepseek-v4-flash",
    },
    "ai-reasoning-solver": {
        "name": "AI Reasoning Solver",
        "description": "Work hard math, logic and planning problems step by step with a reasoning model.",
        "keywords": "ai math solver, reasoning model, logic puzzle solver, step by step",
        "icon": "psychology", "label": "Reasoning", "accent": "#dc2626",
        "placeholder": "Describe the problem...",
        "system": "Solve the problem rigorously step by step, verify the result, then state the final answer clearly.",
        "default_model": "deepseek-reasoner",
    },
}


def _by_id(models, model_id: str):
    return next((m for m in models if m.id == model_id), None)


def image_model(model_id: str) -> MediaModel | None:
    return _by_id(IMAGE_MODELS, model_id)


def video_model(model_id: str) -> MediaModel | None:
    return _by_id(VIDEO_MODELS, model_id)


def chat_model(model_id: str) -> ChatModel | None:
    return _by_id(CHAT_MODELS, model_id)


def credits_for_usd(usd: float) -> int:
    """Credit cents to charge for an OpenPaths cost of ``usd``."""
    return max(1, math.ceil(usd * MARKUP * 100 - 1e-9))


def image_credits(model: MediaModel) -> int:
    return credits_for_usd(model.usd)


def video_credits(model: MediaModel, seconds: int) -> int:
    return credits_for_usd(model.usd * seconds)


def chat_reserve_credits(model: ChatModel, prompt_chars: int, max_tokens: int) -> int:
    prompt_tokens = prompt_chars // 3 + 200
    return credits_for_usd((prompt_tokens * model.usd_in + max_tokens * model.usd_out) / 1_000_000)


def chat_actual_credits(model: ChatModel, usage: dict[str, Any]) -> int:
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    return credits_for_usd((pt * model.usd_in + ct * model.usd_out) / 1_000_000)


def catalog() -> dict[str, Any]:
    def media(m: MediaModel, per: str) -> dict[str, Any]:
        return {
            "id": m.id, "name": m.name, "mode": m.mode, "note": m.note,
            "resolution": m.resolution, "usd": m.usd, per: credits_for_usd(m.usd),
        }

    return {
        "markup": MARKUP,
        "images": [media(m, "credits_per_image") for m in IMAGE_MODELS],
        "videos": [media(m, "credits_per_second") for m in VIDEO_MODELS],
        "chat": [
            {"id": m.id, "name": m.name, "note": m.note, "credits_per_1k_tokens_out": credits_for_usd(m.usd_out / 1000)}
            for m in CHAT_MODELS
        ],
        "tools": {
            slug: {"name": t["name"], "placeholder": t["placeholder"], "default_model": t["default_model"]}
            for slug, t in LLM_TOOLS.items()
        },
        "max_video_seconds": MAX_VIDEO_SECONDS,
    }


class OpenPathsError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


def _headers() -> dict[str, str]:
    key = openpaths_key()
    if not key:
        raise OpenPathsError("OpenPaths is not configured on this server.", 503)
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _error_message(resp: requests.Response) -> str:
    try:
        err = resp.json().get("error")
        return (err.get("message") if isinstance(err, dict) else err) or "The model provider rejected this request."
    except Exception:
        return "The model provider could not complete this request."


def _post(path: str, body: dict[str, Any], timeout: int, session=requests) -> requests.Response:
    try:
        resp = session.post(f"{OPENPATHS_API_BASE}{path}", headers=_headers(), json=body, timeout=timeout)
    except requests.RequestException as exc:
        raise OpenPathsError("The model provider is temporarily unavailable.") from exc
    if not resp.ok:
        raise OpenPathsError(_error_message(resp), 502 if resp.status_code >= 500 else 400)
    return resp


def generate_image(model: MediaModel, prompt: str, size: str, session=requests) -> str:
    resp = _post(
        "/images/generations",
        {"model": model.id, "prompt": prompt, "n": 1, "size": size, "aspect_ratio": ASPECTS[size]},
        timeout=180,
        session=session,
    )
    data = (resp.json().get("data") or [{}])[0]
    if data.get("url"):
        return data["url"]
    if data.get("b64_json"):
        mime = "image/jpeg" if data["b64_json"].startswith("/9j/") else "image/png"
        return f"data:{mime};base64," + data["b64_json"]
    raise OpenPathsError("The model returned no image.")


def start_video(model: MediaModel, prompt: str, seconds: int, aspect: str, image_url: str = "", session=requests) -> str:
    body: dict[str, Any] = {
        "model": model.id, "prompt": prompt, "duration": seconds, "aspect_ratio": aspect, "async": True,
    }
    if model.resolution:
        body["resolution"] = model.resolution
    if model.mode == "image":
        body["image_url"] = image_url
    job = _post("/videos/generations", body, timeout=60, session=session).json()
    if not job.get("id"):
        raise OpenPathsError("The video provider did not start a job.")
    return job["id"]


def video_job(job_id: str, session=requests) -> dict[str, Any]:
    try:
        resp = session.get(f"{OPENPATHS_API_BASE}/videos/generations/{job_id}", headers=_headers(), timeout=30)
    except requests.RequestException as exc:
        raise OpenPathsError("The video provider is temporarily unavailable.") from exc
    if not resp.ok:
        raise OpenPathsError(_error_message(resp), 502)
    body = resp.json()
    status = body.get("status", "")
    out: dict[str, Any] = {"status": "completed" if status == "completed" else "failed" if status == "failed" else "running"}
    if out["status"] == "completed":
        out["video_url"] = (body.get("result") or {}).get("video_url", "")
    if out["status"] == "failed":
        out["error"] = (body.get("error") or {}).get("message", "Video generation failed.")
    return out


def chat(model: ChatModel, system: str, messages: list[dict[str, str]], max_tokens: int, session=requests) -> tuple[str, dict[str, Any]]:
    resp = _post(
        "/chat/completions",
        {"model": model.id, "messages": [{"role": "system", "content": system}, *messages], "max_tokens": max_tokens, "temperature": 0.4},
        timeout=120,
        session=session,
    )
    body = resp.json()
    text = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    if not text.strip():
        raise OpenPathsError("The model returned an empty response.")
    return text, body.get("usage") or {}


@dataclass
class VideoJobs:
    """In-memory ledger of paid video jobs so failures can be refunded once."""

    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    ttl: int = 6 * 3600

    def add(self, job_id: str, user_id: Any, credits: int) -> None:
        now = time.time()
        for k in [k for k, v in self.jobs.items() if now - v["at"] > self.ttl]:
            self.jobs.pop(k, None)
        self.jobs[job_id] = {"user": user_id, "credits": credits, "at": now, "refunded": False}

    def get(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)


VIDEO_LEDGER = VideoJobs()
