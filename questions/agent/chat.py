"""Chat endpoint — multi-turn conversation with tool calling.

Supports BYOK (bring your own key) and falls back to platform keys.
Uses openpaths proxy or direct provider SDKs depending on configuration.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Default to openpaths if available, else direct API calls
OPENPATHS_URL = os.getenv("OPENPATHS_URL", "http://localhost:8090")
DEFAULT_MODEL = os.getenv("CHAT_DEFAULT_MODEL", "gpt-4o-mini")
DEFAULT_PROVIDER = os.getenv("CHAT_DEFAULT_PROVIDER", "openai")

# Cost guardrails
MAX_TOKENS_PER_REQUEST = 4096
MAX_TOOL_ITERATIONS = 15


async def call_llm(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    tools: Optional[List[Dict]] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Dict[str, Any]:
    """Call an LLM via openpaths proxy or direct API.

    Args:
        messages: Chat messages in OpenAI format
        model: Model ID (default: gpt-4o-mini)
        provider: Provider name for BYOK routing
        api_key: User's own API key (BYOK) or platform key
        tools: OpenAI-format tool definitions
        temperature: Sampling temperature
        max_tokens: Max completion tokens

    Returns:
        OpenAI-format chat completion response
    """
    model = model or DEFAULT_MODEL
    max_tokens = min(max_tokens, MAX_TOKENS_PER_REQUEST)

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools

    headers = {"Content-Type": "application/json"}

    # Route through openpaths if user has BYOK key and openpaths is available
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        url = f"{OPENPATHS_URL}/v1/chat/completions"
    else:
        # Use platform's own key via openpaths
        platform_key = os.getenv("OPENPATHS_API_KEY", "")
        if platform_key:
            headers["Authorization"] = f"Bearer {platform_key}"
        url = f"{OPENPATHS_URL}/v1/chat/completions"

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def chat_with_tools(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    tools_enabled: Optional[List[str]] = None,
    skill_content: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    db=None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a full chat turn with tool calling loop.

    This is the main entry point for the /api/chat endpoint.
    It handles:
    1. Building the system prompt (with optional skill content)
    2. Getting available tools
    3. Running the tool-calling loop until the model stops
    4. Returning the final response with all tool calls made
    """
    from questions.agent.registry import registry

    # Build system prompt
    system_parts = []
    if system_prompt:
        system_parts.append(system_prompt)
    else:
        system_parts.append(
            "You are a helpful AI assistant on text-generator.io. "
            "You have access to tools that you can use to help answer questions. "
            "Use tools when they would help provide a better answer."
        )

    if skill_content:
        system_parts.append(f"\n## Active Skill\n{skill_content}")

    # Prepare messages with system prompt
    full_messages = [{"role": "system", "content": "\n\n".join(system_parts)}]
    for msg in messages:
        if isinstance(msg, dict):
            full_messages.append(msg)
        else:
            full_messages.append({"role": msg.role, "content": msg.content})

    # Get available tools
    available_tools = None
    if tools_enabled is not None:
        user_providers = set()
        if db and user_id:
            from questions.agent.byok import get_user_providers

            user_providers = get_user_providers(db, user_id)

        tool_defs = registry.get_available_tools(
            enabled_toolsets=tools_enabled if tools_enabled else None,
            user_has_byok_for=user_providers,
        )
        if tool_defs:
            available_tools = tool_defs

    tool_calls_made = []
    iterations = 0

    for _ in range(MAX_TOOL_ITERATIONS):
        iterations += 1

        response = await call_llm(
            messages=full_messages,
            model=model,
            provider=provider,
            api_key=api_key,
            tools=available_tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "stop")

        full_messages.append(message)

        # No tool calls — return final response
        if finish_reason != "tool_calls" or not message.get("tool_calls"):
            return {
                "message": {
                    "role": "assistant",
                    "content": message.get("content", ""),
                },
                "tool_calls_made": tool_calls_made,
                "usage": response.get("usage"),
                "model": response.get("model", model),
                "iterations": iterations,
            }

        # Execute tool calls
        for tc in message.get("tool_calls", []):
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                fn_args = {}

            result = registry.dispatch(fn_name, fn_args, user_secret=api_key or "")
            # Truncate large results
            if len(result) > 10000:
                result = result[:10000] + "\n...[truncated]"

            tool_calls_made.append(
                {
                    "tool_call_id": tc["id"],
                    "name": fn_name,
                    "arguments": fn_args,
                    "result": result,
                }
            )

            full_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                }
            )

    # Exhausted iterations
    return {
        "message": {
            "role": "assistant",
            "content": full_messages[-1].get("content", "Max tool iterations reached."),
        },
        "tool_calls_made": tool_calls_made,
        "usage": None,
        "model": model,
        "iterations": iterations,
    }
