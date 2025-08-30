from sellerinfo import CLAUDE_API_KEY
import logging
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

import aiohttp
from sellerinfo import CLAUDE_API_KEY

async def generate_with_claude(prompt, prefill="", retries=3):
    api_key = CLAUDE_API_KEY
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "anthropic-version": "2023-06-01",
    }
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    logger.info(f"Claude in: {prompt}")
    if prefill:
        messages.append({"role": "assistant", "content": prefill})
    data = {
        "messages": messages,
        "max_tokens": 2024,
        "model": "claude-sonnet-4-20250514"
    }
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(retries):
            try:
                async with session.post(url, headers=headers, json=data) as response:
                    response.raise_for_status()  # Raises an HTTPError for bad responses
                    response_json = await response.json()
                    generated_text = response_json["content"][0]["text"]
                    logger.info(f"Claude Generated text: {generated_text}")
                    return generated_text
            except Exception as e:
                logger.error(f"Error calling Claude API (attempt {attempt + 1}/{retries}): {str(e)}")
                if attempt == retries - 1:
                    logger.error("Max retries reached. Raising the last exception.")
                    raise
        raise Exception("Failed to generate response from Claude after multiple retries")