"""Small async text generator routed directly to DeepSeek V4 Flash."""

from __future__ import annotations

import asyncio
import logging

from questions.logging_config import setup_logging
from questions.provider_router import get_provider_router
from questions.tool_ai import DEFAULT_TEXT_MODEL

setup_logging()
logger = logging.getLogger(__name__)


def _generated_text(data: dict) -> str:
    choices = data.get("choices") or []
    message = (choices[0] or {}).get("message") or {} if choices else {}
    return str(message.get("content") or "").strip()


async def generate_with_deepseek(prompt: str, prefill: str = "", retries: int = 3) -> str:
    messages = [{"role": "user", "content": prompt}]
    if prefill:
        messages.append({"role": "assistant", "content": prefill})

    logger.info(f"DeepSeek in: {prompt}")
    for attempt in range(retries):
        try:
            result = await asyncio.to_thread(
                get_provider_router().chat_completion,
                {
                    "model": DEFAULT_TEXT_MODEL,
                    "messages": messages,
                    "max_tokens": 2024,
                },
            )
            text = _generated_text(result.data)
            logger.info(f"DeepSeek generated text: {text}")
            return text
        except Exception as e:
            logger.error(f"Error calling DeepSeek API (attempt {attempt + 1}/{retries}): {e}")
            if attempt == retries - 1:
                logger.error("Max retries reached. Raising the last exception.")
                raise
    raise RuntimeError("Failed to generate response from DeepSeek after multiple retries")
