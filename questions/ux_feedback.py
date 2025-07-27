import asyncio
from typing import Optional

from .screenshot_utils import screenshot_url, process_image
from .inference_server.claude_queries import query_to_claude_image_async


async def analyze_site(url: str) -> Optional[str]:
    """Capture screenshot of a site and get UX/SEO feedback from Claude."""
    screenshot = await screenshot_url(url)
    processed = process_image(screenshot)
    prompt = f"Provide UX and SEO feedback for {url}."
    return await query_to_claude_image_async(prompt, processed)
