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
class ProviderDefinition:
    slug: str
    name: str
    description: str
    website: str
    logo: str
    secret_names: tuple[str, ...]
    chat_url: str
    api_style: str = "openai"


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
    ProviderDefinition("openai", "OpenAI", "Frontier general, coding, reasoning, vision, and image models.", "https://openai.com/", "openai.svg", ("OPENAI_API_KEY",), "https://api.openai.com/v1/chat/completions"),
    ProviderDefinition("anthropic", "Anthropic", "Long-context Claude models for reasoning, coding, and agentic work.", "https://www.anthropic.com/", "anthropic.svg", ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"), "https://api.anthropic.com/v1/messages", "anthropic"),
    ProviderDefinition("google", "Google", "Gemini models with long context, fast multimodal understanding, and embeddings.", "https://ai.google.dev/", "google.svg", ("GEMINI_API_KEY", "GOOGLE_API_KEY"), "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"),
    ProviderDefinition("xai", "xAI", "Grok chat and reasoning models through an OpenAI-compatible API.", "https://x.ai/", "xai.svg", ("XAI_API_KEY",), "https://api.x.ai/v1/chat/completions"),
    ProviderDefinition("deepseek", "DeepSeek", "Fast and cost-efficient chat, code, and reasoning models.", "https://www.deepseek.com/", "deepseek.svg", ("DEEPSEEK_API_KEY",), "https://api.deepseek.com/v1/chat/completions"),
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
    ModelDefinition("text-generator/auto", "Auto", "google", "gemini-3.5-flash", "Semantic routing across providers for a strong quality, speed, and cost balance.", "1M", 1.50, 9.00, ("auto", "chat", "vision", "tools"), ("auto", "auto-chat", "auto-text"), ("gpt-5.4-mini", "claude-sonnet-latest", "deepseek-chat"), "balanced"),
    ModelDefinition("text-generator/auto-fast", "Auto Fast", "deepseek", "deepseek-chat", "Low-latency routing for interactive assistants, extraction, and quick agent loops.", "128K", 0.14, 0.28, ("auto", "fast", "chat"), ("auto-fast",), ("gemini-2.5-flash", "gpt-4o-mini"), "fast"),
    ModelDefinition("text-generator/auto-cheap", "Auto Cheap", "google", "gemini-2.5-flash", "Lowest-cost suitable routing for formatting, classification, extraction, and simple edits.", "1M", 0.20, 1.25, ("auto", "low-cost", "chat"), ("auto-cheap", "auto-easy"), ("gpt-4o-mini", "llama-3.1-8b-instant"), "cheap"),
    ModelDefinition("text-generator/auto-code", "Auto Code", "openai", "gpt-5.4-mini", "Routes coding prompts by complexity, from small diffs through architecture and debugging.", "400K", 0.75, 4.50, ("auto", "code", "tools", "reasoning"), ("auto-code",), ("claude-sonnet-latest", "codestral-latest", "deepseek-reasoner"), "code"),
    ModelDefinition("text-generator/auto-reasoning", "Auto Reasoning", "openai", "gpt-5.4-mini", "Automatic model and thinking-level selection for planning, math, and hard decisions.", "400K", 0.75, 4.50, ("auto", "reasoning", "tools"), ("auto-reasoning", "auto-think", "autothink"), ("claude-opus-latest", "deepseek-reasoner", "gemini-2.5-pro"), "reasoning"),
    ModelDefinition("text-generator/auto-vision", "Auto Vision", "google", "gemini-2.5-flash", "Image understanding and OCR routed for latency, resolution, and task complexity.", "1M", 0.30, 2.50, ("auto", "vision", "ocr"), ("auto-vision",), ("gpt-4o", "pixtral-large-latest"), "vision"),

    ModelDefinition("gpt-5.4", "GPT-5.4", "openai", "gpt-5.4", "Frontier general reasoning and agentic work.", "1M", 2.50, 15.00, ("reasoning", "code", "tools", "vision"), ("gpt", "openai"), ("or/gpt-5.4", "gpt-4o")),
    ModelDefinition("gpt-5.4-mini", "GPT-5.4 Mini", "openai", "gpt-5.4-mini", "Efficient reasoning, coding, and tool use.", "400K", 0.75, 4.50, ("reasoning", "code", "tools", "vision"), (), ("or/gpt-5.4", "gpt-4o-mini")),
    ModelDefinition("gpt-4o", "GPT-4o", "openai", "gpt-4o", "General-purpose multimodal chat model.", "128K", 2.50, 10.00, ("chat", "vision", "tools"), (), ("gemini-2.5-pro",)),
    ModelDefinition("gpt-4o-mini", "GPT-4o Mini", "openai", "gpt-4o-mini", "Fast, affordable multimodal model.", "128K", 0.15, 0.60, ("fast", "vision", "tools"), (), ("gemini-2.5-flash",)),

    ModelDefinition("claude-opus-latest", "Claude Opus", "anthropic", "claude-opus-4-1-20250805", "Anthropic flagship for long-horizon reasoning and coding.", "200K", 15.00, 75.00, ("reasoning", "code", "vision", "tools"), ("claude", "claude-opus"), ("or/claude-opus", "gpt-5.4")),
    ModelDefinition("claude-sonnet-latest", "Claude Sonnet", "anthropic", "claude-sonnet-4-20250514", "High-quality coding, analysis, and agentic work at balanced cost.", "200K", 3.00, 15.00, ("reasoning", "code", "vision", "tools"), ("claude-sonnet",), ("or/claude-sonnet", "gpt-5.4-mini")),
    ModelDefinition("claude-haiku", "Claude Haiku", "anthropic", "claude-3-5-haiku-latest", "Fast Claude model for lightweight conversational tasks.", "200K", 0.80, 4.00, ("fast", "chat", "vision"), (), ("gemini-2.5-flash",)),

    ModelDefinition("gemini-2.5-pro", "Gemini 2.5 Pro", "google", "gemini-2.5-pro", "Long-context multimodal reasoning from Google.", "1M", 1.25, 10.00, ("reasoning", "code", "vision", "tools"), ("gemini", "gemini-latest"), ("or/gemini-pro", "gpt-4o")),
    ModelDefinition("gemini-2.5-flash", "Gemini 2.5 Flash", "google", "gemini-2.5-flash", "Low-latency multimodal model for high-throughput applications.", "1M", 0.30, 2.50, ("fast", "vision", "tools"), (), ("gpt-4o-mini",)),

    ModelDefinition("grok-4", "Grok 4", "xai", "grok-4", "xAI reasoning model with tool and vision support.", "256K", 3.00, 15.00, ("reasoning", "tools", "vision"), ("grok", "grok-latest"), ("or/grok-4", "gpt-5.4")),
    ModelDefinition("grok-3-mini", "Grok 3 Mini", "xai", "grok-3-mini", "Compact reasoning model for lower-cost tasks.", "131K", 0.30, 0.50, ("fast", "reasoning"), (), ("deepseek-reasoner",)),

    ModelDefinition("deepseek-chat", "DeepSeek Chat", "deepseek", "deepseek-chat", "Cost-efficient general chat and coding model.", "128K", 0.27, 1.10, ("fast", "chat", "code"), (), ("or/deepseek-chat", "gemini-2.5-flash")),
    ModelDefinition("deepseek-reasoner", "DeepSeek Reasoner", "deepseek", "deepseek-reasoner", "Reasoning-focused DeepSeek model.", "128K", 0.55, 2.19, ("reasoning", "code"), (), ("or/deepseek-chat", "gpt-5.4-mini")),

    ModelDefinition("mistral-large-latest", "Mistral Large", "mistral", "mistral-large-latest", "Mistral's flagship general and reasoning model.", "128K", 2.00, 6.00, ("chat", "reasoning", "tools")),
    ModelDefinition("mistral-small-latest", "Mistral Small", "mistral", "mistral-small-latest", "Fast and efficient general-purpose model.", "128K", 0.10, 0.30, ("fast", "chat", "tools")),
    ModelDefinition("codestral-latest", "Codestral", "mistral", "codestral-latest", "Code generation, completion, and repository understanding.", "256K", 0.30, 0.90, ("code", "tools"), (), ("deepseek-chat",)),
    ModelDefinition("pixtral-large-latest", "Pixtral Large", "mistral", "pixtral-large-latest", "Mistral multimodal model for image and document analysis.", "128K", 2.00, 6.00, ("vision", "chat"), (), ("gemini-2.5-flash",)),

    ModelDefinition("llama-3.3-70b-versatile", "Llama 3.3 70B", "groq", "llama-3.3-70b-versatile", "Fast Llama inference on Groq.", "128K", 0.59, 0.79, ("fast", "chat", "code")),
    ModelDefinition("llama-3.1-8b-instant", "Llama 3.1 8B Instant", "groq", "llama-3.1-8b-instant", "Very low-latency chat and extraction.", "128K", 0.05, 0.08, ("fast", "low-cost")),

    ModelDefinition("or/gpt-5.4", "GPT-5.4 via OpenRouter", "openrouter", "openai/gpt-5.4", "Alternate OpenRouter path to GPT-5.4.", "1M", 2.50, 15.00, ("reasoning", "code", "fallback")),
    ModelDefinition("or/claude-sonnet", "Claude Sonnet via OpenRouter", "openrouter", "anthropic/claude-sonnet-4", "Alternate OpenRouter path to Claude Sonnet.", "200K", 3.00, 15.00, ("reasoning", "code", "fallback")),
    ModelDefinition("or/claude-opus", "Claude Opus via OpenRouter", "openrouter", "anthropic/claude-opus-4.1", "Alternate OpenRouter path to Claude Opus.", "200K", 15.00, 75.00, ("reasoning", "fallback")),
    ModelDefinition("or/gemini-pro", "Gemini Pro via OpenRouter", "openrouter", "google/gemini-2.5-pro", "Alternate OpenRouter path to Gemini Pro.", "1M", 1.25, 10.00, ("vision", "reasoning", "fallback")),
    ModelDefinition("or/deepseek-chat", "DeepSeek via OpenRouter", "openrouter", "deepseek/deepseek-chat", "Alternate OpenRouter path to DeepSeek.", "128K", 0.27, 1.10, ("chat", "fallback")),
    ModelDefinition("or/grok-4", "Grok via OpenRouter", "openrouter", "x-ai/grok-4", "Alternate OpenRouter path to Grok.", "256K", 3.00, 15.00, ("reasoning", "fallback")),

    ModelDefinition("qwen3.5-397b", "Qwen 3.5 397B", "together", "Qwen/Qwen3.5-397B-A17B", "Large open-weight Qwen model on Together AI.", "256K", 0.80, 2.40, ("reasoning", "code", "open-weights")),
    ModelDefinition("kimi-k2.5", "Kimi K2.5", "together", "moonshotai/Kimi-K2.5", "Long-context agentic and coding model.", "256K", 0.50, 2.80, ("reasoning", "code", "open-weights")),
    ModelDefinition("minimax-m2.5", "MiniMax M2.5", "minimax", "MiniMax-M2.5", "MiniMax reasoning and coding model.", "204K", 0.30, 1.20, ("reasoning", "code"), (), ("qwen3.5-397b",)),
    ModelDefinition("glm-5", "GLM-5", "zai", "glm-5", "Z.AI flagship language and coding model.", "200K", 1.00, 3.20, ("reasoning", "code", "tools"), (), ("qwen3.5-397b",)),
    ModelDefinition("nemotron-ultra", "Nemotron Ultra", "nvidia", "nvidia/llama-3.1-nemotron-ultra-253b-v1", "NVIDIA-optimized reasoning model served through NIM.", "128K", 0.60, 1.80, ("reasoning", "open-weights")),
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
