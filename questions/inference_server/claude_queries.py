import asyncio
from typing import FrozenSet, List, Optional

from anthropic import AsyncAnthropic
import aiohttp
import json

import logging
logger = logging.getLogger(__name__)

from questions.utils import log_time

from sellerinfo import CLAUDE_API_KEY

# Initialize client
claude_client = AsyncAnthropic(api_key=CLAUDE_API_KEY)


async def query_to_claude_async(
    prompt: str,
    stop_sequences: Optional[FrozenSet[str]] = None,
    extra_data: Optional[dict] = None,
    prefill: Optional[str] = None,
    system_message: Optional[str] = None,
    model: Optional[str] = "claude-sonnet-4-20250514",
) -> Optional[str]:
    """Async Claude query with caching"""
    
    if extra_data and type(extra_data) != dict:
        extra_data = dict(extra_data)
    else:
        extra_data = {}
    try:
        # Truncate prompt if it's too long (Claude has ~100k context limit, but we'll be conservative)
        truncated_prompt = truncate_to_max_tokens(prompt, max_tokens=80000)
        if truncated_prompt != prompt:
            logger.warning("Prompt was truncated due to token limit")
        
        messages = [
            {
                "role": "user",
                "content": truncated_prompt.strip(),
            }
        ]
        if prefill:
            messages.append(
                {
                    "role": "assistant",
                    "content": prefill.strip(),
                }
            )

        timeout = extra_data.get("timeout", 30) if extra_data else 30
        
        # Possibly truncate system message if too long
        truncated_system = ""
        if system_message:
            truncated_system = truncate_to_max_tokens(system_message, max_tokens=2000).strip()
            if truncated_system != system_message.strip():
                logger.warning("System message was truncated due to token limit")

        with log_time("Claude async query"):
            logger.info(f"Querying Claude with prompt length: {len(truncated_prompt)}")

            try:
                message = await asyncio.wait_for(
                    claude_client.messages.create(
                        max_tokens=2024,
                        messages=messages,
                        model=model,
                        system=truncated_system,
                        stop_sequences=[s for s in list(stop_sequences) if s and s.strip()]
                        if stop_sequences
                        else [],
                    ),
                    timeout=timeout,
                )

                if message.content:
                    generated_text = message.content[0].text
                    logger.info(f"Claude Generated text length: {len(generated_text)}")
                    return generated_text
                return None
            
            except Exception as token_error:
                if isinstance(token_error, (asyncio.TimeoutError)):
                    # Just re-raise timeout errors
                    raise
                
                # Check if this is a token limit error from Anthropic 
                if "too many tokens" in str(token_error).lower():
                    logger.error(f"Token limit exceeded in Claude async query: {token_error}")
                    # Try again with more aggressive truncation
                    more_truncated_prompt = truncate_to_max_tokens(prompt, max_tokens=40000)
                    messages = [
                        {
                            "role": "user",
                            "content": more_truncated_prompt.strip(),
                        }
                    ]
                    if prefill:
                        messages.append(
                            {
                                "role": "assistant",
                                "content": prefill.strip(),
                            }
                        )
                    
                    logger.info(f"Retrying with more aggressive truncation, prompt length: {len(more_truncated_prompt)}")
                    message = await asyncio.wait_for(
                        claude_client.messages.create(
                            max_tokens=2024,
                            messages=messages,
                            model=model,
                            system=truncated_system,
                            stop_sequences=[s for s in list(stop_sequences) if s and s.strip()]
                            if stop_sequences
                            else [],
                        ),
                        timeout=timeout,
                    )
                    
                    if message.content:
                        generated_text = message.content[0].text
                        logger.info(f"Claude Generated text (after retry): {len(generated_text)}")
                        return generated_text
                    return None
                else:
                    # Re-raise other errors
                    raise

    except Exception as e:
        logger.error(f"Error in Claude query: {e}")
        return None


async def query_to_claude_json_async(
    prompt: str,
    schema: dict,
    system_message: Optional[str] = None,
    model: Optional[str] = "claude-sonnet-4-20250514",
) -> dict:
    """Query Claude in JSON mode using tool use."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    messages = [{"role": "user", "content": prompt}]
    data = {
        "messages": messages,
        "model": model,
        "max_tokens": 1024,
        "system": system_message or "",
        "tools": [
            {
                "name": "structured_output",
                "description": "Return the response in JSON form.",
                "input_schema": schema,
            }
        ],
        "tool_choice": {"type": "tool", "name": "structured_output"},
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            resp.raise_for_status()
            result = await resp.json()

    content = result.get("content", [])
    if content and content[0].get("type") == "tool_use":
        return content[0].get("input", {})
    if content and content[0].get("text"):
        try:
            return json.loads(content[0]["text"].strip())
        except Exception:
            return {"text": content[0]["text"]}
    return {}

def truncate_to_max_tokens(text, max_tokens):
    """
    Truncate text to approximately fit within max_tokens.
    Uses a simple character-to-token ratio estimation (roughly 4 characters per token).
    Middle-out truncation approach that preserves the beginning and end of the text.
    
    Args:
        text (str): The text to truncate
        max_tokens (int): Maximum number of tokens to allow
        
    Returns:
        str: Truncated text that should fit within the token limit
    """
    # Estimate 4 characters per token as a rough approximation
    char_per_token = 4
    max_chars = max_tokens * char_per_token
    
    if len(text) <= max_chars:
        return text
    
    # Split into words to do middle-out truncation
    words = text.split()
    
    if len(words) <= 2:
        return text[:max_chars]
    
    # Calculate how many words to keep from beginning and end
    total_words_to_keep = int(max_chars / (sum(len(w) for w in words) / len(words)))
    words_per_side = total_words_to_keep // 2
    
    # Ensure we keep at least some words from each side
    words_per_side = max(1, min(words_per_side, len(words) // 2 - 1))
    
    # Get beginning and ending portions
    beginning = ' '.join(words[:words_per_side])
    ending = ' '.join(words[-words_per_side:])
    
    # Add an ellipsis to indicate truncation
    result = beginning + " ... " + ending
    
    # If still too long, just truncate the end
    if len(result) > max_chars:
        return result[:max_chars]
    
    return result
