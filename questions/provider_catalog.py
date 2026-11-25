"""Public provider and model catalogue for Text Generator's unified router.

Credentials deliberately do not live here.  Each provider only declares the
environment/sellerinfo names that may contain its key, allowing the catalogue
to be safely used by the website and the OpenAI-compatible inference service.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProviderServiceDefinition:
    name: str
    description: str
    endpoint: str
    url: str
    price: str
    billing_unit: str
    method: str = "POST"


@dataclass(frozen=True)
class ProviderDefinition:
    slug: str
    name: str
    description: str
    website: str
    logo: str
    secret_names: tuple[str, ...]
    chat_url: str
    api_style: str = "openai"
    capabilities: tuple[str, ...] = ("chat",)
    first_party: bool = False
    services: tuple[ProviderServiceDefinition, ...] = ()


@dataclass(frozen=True)
class ModelDefinition:
    id: str
    name: str
    provider: str
    provider_model_id: str
    description: str
    context_window: str
    input_price: float
    output_price: float
    tags: tuple[str, ...] = ("chat",)
    aliases: tuple[str, ...] = ()
    fallback_models: tuple[str, ...] = ()
    auto_profile: str | None = None


PROVIDERS: tuple[ProviderDefinition, ...] = (
    ProviderDefinition(
        "netwrck",
        "Netwrck",
        "First-party image generation, style transfer, and inpainting on the open-source Stable Diffusion Server.",
        "https://netwrck.com/",
        "netwrck.svg",
        ("NETWRCK_API_KEY",),
        "https://images2.netwrck.com/create_and_upload_image",
        capabilities=("image generation", "style transfer", "inpainting"),
        first_party=True,
        services=(
            ProviderServiceDefinition("Fast SDXL", "Proteus SDXL text-to-image with a fast 8-step pipeline.", "/v1/images/generations", "/tools/text-to-image", "$0.003", "per image"),
            ProviderServiceDefinition("Style transfer", "Canny-guided redraws that preserve the source composition.", "/v1/images/generations", "https://app.nz/models/sdxl-style-transfer", "$0.003", "per image"),
            ProviderServiceDefinition("Inpainting", "Mask-based image editing backed by the same first-party image server.", "/v1/images/generations", "https://app.nz/models/sd-inpaint", "Usage based", "per image"),
        ),
    ),
    ProviderDefinition(
        "appnz",
        "App.nz",
        "First-party research, speech, media, and scale-to-zero Cog endpoints with usage metering on shared infrastructure.",
        "https://app.nz/",
        "appnz.svg",
        ("APPNZ_API_KEY", "APP_NZ_KEY"),
        "https://app.nz/v1/chat/completions",
        capabilities=("chat", "research search", "speech", "images", "audio", "video", "3D", "GPU cogs"),
        first_party=True,
        services=(
            ProviderServiceDefinition("Papers Search", "Search papers, methods, datasets, GitHub code, repositories, and the live web.", "https://papers.app.nz/api/search", "https://app.nz/papers", "$1", "per 1,000 searches", "GET"),
            ProviderServiceDefinition("App.nz TTS", "Fish Speech voices with stored or inline reference voices.", "/v1/audio/speech", "/text-to-speech", "$0.10", "per audio minute"),
            ProviderServiceDefinition("Pocket TTS", "A lightweight open TTS model with 26 voices across six languages.", "/v1/audio/speech", "/text-to-speech", "$0.06", "per audio minute"),
            ProviderServiceDefinition("Scale-to-zero Cogs", "Deploy open Cog images and call dedicated or serverless GPU endpoints.", "/api/cogs/{model_id}/predict", "https://app.nz/cogs", "Hardware rate", "per running second"),
            ProviderServiceDefinition("Media APIs", "Transcription, video encoding, source separation, upscaling, and background removal.", "/api/cogs/{model_id}/predict", "https://app.nz/cogs", "Usage based", "per prediction"),
        ),
    ),
    ProviderDefinition("openai", "OpenAI", "Frontier general, coding, reasoning, vision, and image models.", "https://openai.com/", "openai.svg", ("OPENAI_API_KEY",), "https://api.openai.com/v1/chat/completions"),
    ProviderDefinition("anthropic", "Anthropic", "Long-context Claude models for reasoning, coding, and agentic work.", "https://www.anthropic.com/", "anthropic.svg", ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"), "https://api.anthropic.com/v1/messages", "anthropic"),
    ProviderDefinition("google", "Google", "Gemini models with long context, fast multimodal understanding, and embeddings.", "https://ai.google.dev/", "google.svg", ("GEMINI_API_KEY", "GOOGLE_API_KEY"), "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"),
    ProviderDefinition("xai", "xAI", "Grok chat and reasoning models through an OpenAI-compatible API.", "https://x.ai/", "xai.svg", ("XAI_API_KEY",), "https://api.x.ai/v1/chat/completions"),
    ProviderDefinition("moonshot", "Moonshot AI", "Kimi K3 flagship and long-context Kimi models through an OpenAI-compatible API.", "https://platform.moonshot.ai/", "moonshot.svg", ("MOONSHOT_API_KEY",), "https://api.moonshot.ai/v1/chat/completions"),
    ProviderDefinition("deepseek", "DeepSeek", "Fast and cost-efficient chat, code, reasoning, and vision models.", "https://www.deepseek.com/", "deepseek.svg", ("DEEPSEEK_API_KEY",), "https://api.deepseek.com/chat/completions", capabilities=("chat", "code", "reasoning", "vision")),
    ProviderDefinition("mistral", "Mistral AI", "European open and commercial models for chat, code, and vision.", "https://mistral.ai/", "mistral.svg", ("MISTRAL_API_KEY",), "https://api.mistral.ai/v1/chat/completions"),
    ProviderDefinition("groq", "Groq", "Low-latency inference for popular open-weight language models.", "https://groq.com/", "groq.svg", ("GROQ_API_KEY",), "https://api.groq.com/openai/v1/chat/completions"),
    ProviderDefinition("openrouter", "OpenRouter", "A broad model marketplace and an additional resilient provider path.", "https://openrouter.ai/", "openrouter.svg", ("OPENROUTER_API_KEY",), "https://openrouter.ai/api/v1/chat/completions"),
    ProviderDefinition("together", "Together AI", "Hosted open-weight models for chat, reasoning, code, and generation.", "https://www.together.ai/", "together.svg", ("TOGETHER_API_KEY",), "https://api.together.xyz/v1/chat/completions"),
    ProviderDefinition("minimax", "MiniMax", "MiniMax reasoning and high-speed text models.", "https://www.minimax.io/", "minimax.svg", ("MINIMAX_API_KEY",), "https://api.minimax.io/v1/chat/completions"),
    ProviderDefinition("zai", "Z.AI", "GLM language and vision models, including coding-plan endpoints.", "https://z.ai/", "zai.svg", ("Z_API_KEY", "ZAI_API_KEY"), "https://api.z.ai/api/paas/v4/chat/completions"),
    ProviderDefinition("nvidia", "NVIDIA", "NIM-hosted Nemotron and open models optimized for accelerated inference.", "https://build.nvidia.com/", "nvidia.svg", ("NVIDIA_API_KEY",), "https://integrate.api.nvidia.com/v1/chat/completions"),
    ProviderDefinition("fireworks", "Fireworks AI", "Fast serverless inference for production open-weight models.", "https://fireworks.ai/", "fireworks.svg", ("FIREWORKS_API_KEY",), "https://api.fireworks.ai/inference/v1/chat/completions"),
    ProviderDefinition("nous", "Nous Research", "Hermes models for steerable assistants and agent workflows.", "https://nousresearch.com/", "nous.svg", ("NOUS_API_KEY",), "https://inference-api.nousresearch.com/v1/chat/completions"),
)


MODELS: tuple[ModelDefinition, ...] = (
    # Text Generator semantic auto-router profiles.
    ModelDefinition("text-generator/auto", "Auto", "google", "gemini-3.5-flash", "Semantic routing across providers for a strong quality, speed, and cost balance.", "1M", 1.50, 9.00, ("auto", "chat", "vision", "tools"), ("auto", "auto-chat", "auto-text"), ("gpt-5.4-mini", "deepseek-v4-flash", "claude-haiku-5-5"), "balanced"),
    ModelDefinition("text-generator/auto-fast", "Auto Fast", "deepseek", "deepseek-flash", "Low-latency routing for interactive assistants, extraction, and quick agent loops.", "1M", 0.30, 1.20, ("auto", "fast", "chat"), ("auto-fast",), ("deepseek-chat", "gemini-2.5-flash", "gpt-4o-mini"), "fast"),
    ModelDefinition("text-generator/auto-cheap", "Auto Cheap", "google", "gemini-2.5-flash", "Lowest-cost suitable routing for formatting, classification, extraction, and simple edits.", "1M", 0.20, 1.25, ("auto", "low-cost", "chat"), ("auto-cheap", "auto-easy"), ("gpt-4o-mini", "llama-3.1-8b-instant"), "cheap"),
    ModelDefinition("text-generator/auto-code", "Auto Code", "openai", "gpt-5.4-mini", "Routes coding prompts by complexity, from small diffs through architecture and debugging.", "400K", 0.75, 4.50, ("auto", "code", "tools", "reasoning"), ("auto-code",), ("claude-haiku-5-5", "codestral-latest", "deepseek-reasoner"), "code"),
    ModelDefinition("text-generator/auto-reasoning", "Auto Reasoning", "openai", "gpt-5.4-mini", "Automatic model and thinking-level selection for planning, math, and hard decisions.", "400K", 0.75, 4.50, ("auto", "reasoning", "tools"), ("auto-reasoning", "auto-think", "autothink"), ("claude-opus-latest", "deepseek-reasoner", "gemini-2.5-pro"), "reasoning"),
    ModelDefinition("text-generator/auto-vision", "Auto Vision", "google", "gemini-2.5-flash", "Image understanding and OCR routed for latency, resolution, and task complexity.", "1M", 0.30, 2.50, ("auto", "vision", "ocr"), ("auto-vision",), ("gpt-4o", "pixtral-large-latest"), "vision"),

    ModelDefinition("appnz/auto", "App.nz Auto", "appnz", "appnz/auto", "App.nz semantic routing across hosted providers with one metered API key.", "1M", 1.50, 9.00, ("chat", "reasoning", "code", "vision", "tools"), ("app-auto",), ("text-generator/auto",)),

    ModelDefinition("gpt-5.6-luna", "GPT-5.6 Luna", "openai", "gpt-5.6-luna", "Low-cost GPT-5.6 route for high-volume continuation, chat, and tool use.", "1M", 1.00, 6.00, ("fast", "reasoning", "code", "tools", "vision"), ("luna", "gpt-5-6-luna", "gpt56-luna"), ("gpt-5.4-mini", "gemini-2.5-flash", "deepseek-chat")),
    ModelDefinition("gpt-5.4", "GPT-5.4", "openai", "gpt-5.4", "Frontier general reasoning and agentic work.", "1M", 2.50, 15.00, ("reasoning", "code", "tools", "vision"), ("gpt", "openai"), ("or/gpt-5.4", "gpt-4o")),
    ModelDefinition("gpt-5.4-mini", "GPT-5.4 Mini", "openai", "gpt-5.4-mini", "Efficient reasoning, coding, and tool use.", "400K", 0.75, 4.50, ("reasoning", "code", "tools", "vision"), (), ("or/gpt-5.4", "gpt-4o-mini")),
    ModelDefinition("gpt-4o", "GPT-4o", "openai", "gpt-4o", "General-purpose multimodal chat model.", "128K", 2.50, 10.00, ("chat", "vision", "tools"), (), ("gemini-2.5-pro",)),
    ModelDefinition("gpt-4o-mini", "GPT-4o Mini", "openai", "gpt-4o-mini", "Fast, affordable multimodal model.", "128K", 0.15, 0.60, ("fast", "vision", "tools"), (), ("gemini-2.5-flash",)),

    ModelDefinition("claude-opus-latest", "Claude Opus", "anthropic", "claude-opus-5", "Anthropic flagship for long-horizon reasoning, agentic coding, and knowledge work.", "1M", 5.00, 25.00, ("reasoning", "code", "vision", "tools"), ("claude", "claude-opus", "opus"), ("claude-opus-4-8", "or/claude-opus", "gpt-5.4")),
    ModelDefinition("claude-opus-5", "Claude Opus 5", "anthropic", "claude-opus-5", "Latest Claude Opus. Deep reasoning, agentic coding, and 1M-token context.", "1M", 5.00, 25.00, ("reasoning", "code", "vision", "tools"), ("opus-5",), ("claude-opus-4-8", "or/claude-opus")),
    ModelDefinition("claude-opus-4-8", "Claude Opus 4.8", "anthropic", "claude-opus-4-8", "Previous-generation Claude Opus for reasoning and long-horizon agentic work.", "1M", 5.00, 25.00, ("reasoning", "code", "vision", "tools"), ("opus-4.8",), ("or/claude-opus", "gpt-5.4")),
    ModelDefinition("claude-haiku-5-5", "Claude Haiku 5.5", "anthropic", "claude-haiku-5-5", "Fast, low-cost Claude model for high-volume chat, writing, coding, and vision.", "1M", 0.10, 0.50, ("fast", "chat", "code", "vision", "tools"), ("claude-haiku", "claude-haiku-latest", "haiku", "haiku-5.5", "haiku-5-5", "haiku55"), ("deepseek-v4-flash", "gemini-2.5-flash")),

    ModelDefinition("gemini-2.5-pro", "Gemini 2.5 Pro", "google", "gemini-2.5-pro", "Long-context multimodal reasoning from Google.", "1M", 1.25, 10.00, ("reasoning", "code", "vision", "tools"), ("gemini", "gemini-latest"), ("or/gemini-pro", "gpt-4o")),
    ModelDefinition("gemini-2.5-flash", "Gemini 2.5 Flash", "google", "gemini-2.5-flash", "Low-latency multimodal model for high-throughput applications.", "1M", 0.30, 2.50, ("fast", "vision", "tools"), (), ("gpt-4o-mini",)),

    ModelDefinition("grok-4.5", "Grok 4.5", "xai", "grok-4.5", "xAI flagship for coding, agentic tasks, and knowledge work with vision and configurable reasoning effort.", "500K", 2.00, 6.00, ("reasoning", "tools", "vision"), ("grok", "grok-latest", "grok-4.5-latest"), ("or/grok-4", "gpt-5.4")),
    ModelDefinition("grok-4.3", "Grok 4.3", "xai", "grok-4.3", "xAI 1M-context reasoning model with tool and vision support at low cost.", "1M", 1.25, 2.50, ("reasoning", "tools", "vision"), ("grok-4", "grok-4.3-latest"), ("or/grok-4", "gpt-5.4")),
    ModelDefinition("grok-4.20-0309-non-reasoning", "Grok 4.20 Non-Reasoning", "xai", "grok-4.20-0309-non-reasoning", "Fast 1M-context Grok for direct responses and tool-calling workloads.", "1M", 1.25, 2.50, ("fast", "tools", "vision"), ("grok-fast", "grok-non-reasoning"), ("grok-4.3",)),
    ModelDefinition("grok-build-0.1", "Grok Build 0.1", "xai", "grok-build-0.1", "xAI coding and build model for software engineering agents.", "256K", 1.00, 2.00, ("code", "agentic", "tools"), ("grok-build", "grok-code"), ("grok-4.3",)),
    ModelDefinition("grok-3-mini", "Grok 3 Mini", "xai", "grok-3-mini", "Compact reasoning model for lower-cost tasks.", "131K", 0.30, 0.50, ("fast", "reasoning"), ("grok-mini",), ("deepseek-reasoner",)),

    ModelDefinition("deepseek-chat", "DeepSeek Chat", "deepseek", "deepseek-chat", "Cost-efficient general chat and coding model.", "128K", 0.27, 1.10, ("fast", "chat", "code"), (), ("or/deepseek-chat", "gemini-2.5-flash")),
    ModelDefinition("deepseek-reasoner", "DeepSeek Reasoner", "deepseek", "deepseek-reasoner", "Reasoning-focused DeepSeek model.", "128K", 0.55, 2.19, ("reasoning", "code"), (), ("or/deepseek-chat", "gpt-5.4-mini")),
    # DeepSeek's V4-Flash-Vision-Exp has peak/off-peak upstream rates. The
    # catalogue has one rate, so use the peak V4-Flash rate to avoid
    # undercharging during peak hours while keeping vision at V4-Flash pricing.
    ModelDefinition("deepseek-v4-flash-vision-exp", "DeepSeek V4 Flash Vision Exp", "deepseek", "deepseek-v4-flash-vision-exp", "Experimental DeepSeek V4 Flash vision model for mixed text and image input, including base64 URLs, external URLs, and Files API parts.", "1M", 0.44, 1.32, ("fast", "chat", "code", "reasoning", "vision"), ("deepseek-vision", "deepseek-v4-vision-exp")),
    # DeepSeek V4.1 Flash bills peak and off-peak. The catalogue has one rate
    # per model, so list the peak rate to avoid undercharging peak traffic.
    ModelDefinition("deepseek-v4-flash", "DeepSeek V4 Flash", "deepseek", "deepseek-flash", "Direct DeepSeek V4.1 Flash text model for fast chat, writing, and coding.", "1M", 0.30, 1.20, ("fast", "chat", "writing", "code", "tools"), ("deepseek-flash", "deepseek-v4", "deepseek-v4.1-flash", "deepseek-v4-flash-1017", "deepseek-v4.1-flash-1017")),

    ModelDefinition("mistral-large-latest", "Mistral Large", "mistral", "mistral-large-latest", "Mistral's flagship general and reasoning model.", "128K", 2.00, 6.00, ("chat", "reasoning", "tools")),
    ModelDefinition("mistral-small-latest", "Mistral Small", "mistral", "mistral-small-latest", "Fast and efficient general-purpose model.", "128K", 0.10, 0.30, ("fast", "chat", "tools")),
    ModelDefinition("codestral-latest", "Codestral", "mistral", "codestral-latest", "Code generation, completion, and repository understanding.", "256K", 0.30, 0.90, ("code", "tools"), (), ("deepseek-chat",)),
    ModelDefinition("pixtral-large-latest", "Pixtral Large", "mistral", "pixtral-large-latest", "Mistral multimodal model for image and document analysis.", "128K", 2.00, 6.00, ("vision", "chat"), (), ("gemini-2.5-flash",)),

    ModelDefinition("llama-3.3-70b-versatile", "Llama 3.3 70B", "groq", "llama-3.3-70b-versatile", "Fast Llama inference on Groq.", "128K", 0.59, 0.79, ("fast", "chat", "code")),
    ModelDefinition("llama-3.1-8b-instant", "Llama 3.1 8B Instant", "groq", "llama-3.1-8b-instant", "Very low-latency chat and extraction.", "128K", 0.05, 0.08, ("fast", "low-cost")),

    ModelDefinition("or/gpt-5.4", "GPT-5.4 via OpenRouter", "openrouter", "openai/gpt-5.4", "Alternate OpenRouter path to GPT-5.4.", "1M", 2.50, 15.00, ("reasoning", "code", "fallback")),
    ModelDefinition("or/claude-opus", "Claude Opus via OpenRouter", "openrouter", "anthropic/claude-opus-5", "Alternate OpenRouter path to Claude Opus.", "1M", 5.00, 25.00, ("reasoning", "fallback")),
    ModelDefinition("or/gemini-pro", "Gemini Pro via OpenRouter", "openrouter", "google/gemini-2.5-pro", "Alternate OpenRouter path to Gemini Pro.", "1M", 1.25, 10.00, ("vision", "reasoning", "fallback")),
    ModelDefinition("or/deepseek-chat", "DeepSeek via OpenRouter", "openrouter", "deepseek/deepseek-chat", "Alternate OpenRouter path to DeepSeek.", "128K", 0.27, 1.10, ("chat", "fallback")),
    ModelDefinition("or/grok-4", "Grok via OpenRouter", "openrouter", "x-ai/grok-4.3", "Alternate OpenRouter path to Grok.", "1M", 3.00, 15.00, ("reasoning", "fallback")),

    ModelDefinition("qwen3.5-397b", "Qwen 3.5 397B", "together", "Qwen/Qwen3.5-397B-A17B", "Large open-weight Qwen model on Together AI.", "256K", 0.80, 2.40, ("reasoning", "code", "open-weights")),
    ModelDefinition("kimi-k3", "Kimi K3", "moonshot", "kimi-k3", "Moonshot flagship: 2.8T-parameter open-weights model with 1M context, vision, tool use, and deep reasoning.", "1M", 3.00, 15.00, ("reasoning", "code", "vision", "tools", "open-weights"), ("kimi", "kimi-k3-1m", "moonshot-kimi-k3"), ("or/kimi-k3", "kimi-k2.5")),
    ModelDefinition("or/kimi-k3", "Kimi K3 via OpenRouter", "openrouter", "moonshotai/kimi-k3", "Alternate OpenRouter path to Kimi K3.", "1M", 3.00, 15.00, ("reasoning", "code", "fallback"), (), ("kimi-k2.5",)),
    ModelDefinition("kimi-k2.5", "Kimi K2.5", "together", "moonshotai/Kimi-K2.5", "Long-context agentic and coding model.", "256K", 0.50, 2.80, ("reasoning", "code", "open-weights")),
    ModelDefinition("minimax-m2.5", "MiniMax M2.5", "minimax", "MiniMax-M2.5", "MiniMax reasoning and coding model.", "204K", 0.30, 1.20, ("reasoning", "code"), (), ("qwen3.5-397b",)),
    ModelDefinition("glm-5", "GLM-5", "zai", "glm-5", "Z.AI flagship language and coding model.", "200K", 1.00, 3.20, ("reasoning", "code", "tools"), (), ("qwen3.5-397b",)),
    ModelDefinition("nemotron-ultra", "Nemotron 3 Ultra", "nvidia", "nvidia/nemotron-3-ultra-550b-a55b", "NVIDIA flagship 550B MoE reasoning model served through NIM.", "128K", 0.80, 3.20, ("reasoning", "open-weights"), ("nemotron-3-ultra",), ("nemotron-3-super",)),
    ModelDefinition("nemotron-3-super", "Nemotron 3 Super", "nvidia", "nvidia/nemotron-3-super-120b-a12b", "Mid-size NVIDIA Nemotron MoE for reasoning and agents on NIM.", "128K", 0.25, 1.00, ("reasoning", "tools", "open-weights"), (), ("nemotron-3-nano",)),
    ModelDefinition("nemotron-3-nano", "Nemotron 3 Nano", "nvidia", "nvidia/nemotron-3-nano-30b-a3b", "Low-cost NVIDIA Nemotron MoE for fast chat and extraction on NIM.", "128K", 0.06, 0.24, ("fast", "low-cost", "open-weights")),
    ModelDefinition("nemotron-super-49b", "Llama Nemotron Super 49B", "nvidia", "nvidia/llama-3.3-nemotron-super-49b-v1.5", "Llama-based Nemotron tuned for reasoning, served through NIM.", "128K", 0.12, 0.36, ("reasoning", "open-weights"), (), ("nemotron-3-nano",)),
    ModelDefinition("nvidia-gpt-oss-120b", "GPT-OSS 120B on NVIDIA", "nvidia", "openai/gpt-oss-120b", "OpenAI open-weights 120B served through NIM.", "128K", 0.10, 0.40, ("chat", "code", "open-weights"), ("gpt-oss-120b-nim",)),
    ModelDefinition("fireworks-llama-70b", "Llama 70B on Fireworks", "fireworks", "accounts/fireworks/models/llama-v3p1-70b-instruct", "Production Llama inference on Fireworks AI.", "128K", 0.90, 0.90, ("chat", "open-weights")),
    ModelDefinition("hermes-4", "Hermes 4", "nous", "Hermes-4-405B", "Steerable Nous assistant model for tools and agents.", "128K", 1.00, 3.00, ("agentic", "tools", "open-weights")),
)


PROVIDERS_BY_SLUG = {provider.slug: provider for provider in PROVIDERS}
MODELS_BY_ID = {model.id: model for model in MODELS}
MODEL_ALIASES = {
    alias: model.id
    for model in MODELS
    for alias in model.aliases
}


def resolve_model(model_id: str) -> ModelDefinition | None:
    return MODELS_BY_ID.get(MODEL_ALIASES.get(model_id, model_id))


def provider_models(provider_slug: str) -> list[ModelDefinition]:
    return [model for model in MODELS if model.provider == provider_slug]


def provider_to_dict(provider: ProviderDefinition) -> dict:
    data = asdict(provider)
    data.pop("secret_names", None)
    data.pop("chat_url", None)
    data["model_count"] = len(provider_models(provider.slug))
    data["url"] = f"/providers/{provider.slug}"
    data["logo_url"] = f"/static/img/providers/{provider.logo}"
    return data


def model_to_dict(model: ModelDefinition) -> dict:
    data = asdict(model)
    from questions.token_pricing import lane_for, list_price_per_mtok

    data["provider_input_price"] = model.input_price
    data["provider_output_price"] = model.output_price
    data["input_price"], data["output_price"] = list_price_per_mtok(model.id, lane_for(model.id))
    data["url"] = f"/models/{model.id}"
    provider = PROVIDERS_BY_SLUG[model.provider]
    if model.auto_profile:
        data["provider_name"] = "Text Generator"
        data["provider_url"] = "/models"
        data["logo_url"] = "/static/img/text-generator-brain.png"
    else:
        data["provider_name"] = provider.name
        data["provider_url"] = f"/providers/{provider.slug}"
        data["logo_url"] = f"/static/img/providers/{provider.logo}"
    return data


def usage_cost_cents(model_id: str, usage: Mapping[str, Any] | None) -> int:
    """Estimate a routed request's credit charge from catalog token prices."""
    model = resolve_model(model_id)
    if model is None:
        return 1
    usage = usage or {}
    prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    if not prompt_tokens and not completion_tokens:
        completion_tokens = int(usage.get("total_tokens") or 0)
    cost_cents = (
        prompt_tokens * model.input_price
        + completion_tokens * model.output_price
    ) / 10_000
    return max(1, math.ceil(cost_cents))


def openai_model_list(models: Iterable[ModelDefinition] = MODELS) -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": model.id,
                "object": "model",
                "created": 0,
                "owned_by": model.provider,
                "context_window": model.context_window,
                "tags": list(model.tags),
            }
            for model in models
        ],
    }
