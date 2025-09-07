from typing import Optional

from .inference_server.claude_queries import query_to_claude_image_async
from .screenshot_utils import process_image, screenshot_url


async def analyze_site(url: str) -> Optional[str]:
    """Capture screenshot of a site and get UX/SEO feedback from Claude."""
    screenshot = await screenshot_url(url)
    processed = process_image(screenshot)
    prompt = f"Provide UX and SEO feedback for {url}."
    return await query_to_claude_image_async(prompt, processed)
