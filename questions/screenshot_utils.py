import base64
import io
from PIL import Image
from typing import Tuple


ACCEPTED_SIZES: Tuple[Tuple[int, int], ...] = (
    (1092, 1092),
    (951, 1268),
    (896, 1344),
    (819, 1456),
    (784, 1568),
)


def process_image(image_bytes: bytes) -> bytes:
    """Downscale and convert image to WebP for Claude image API."""
    im = Image.open(io.BytesIO(image_bytes))
    width, height = im.size
    aspect = width / height
    # pick closest aspect ratio size
    target = min(ACCEPTED_SIZES, key=lambda s: abs((s[0] / s[1]) - aspect))
    scale = min(target[0] / width, target[1] / height, 1.0)
    new_size = (int(width * scale), int(height * scale))
    if new_size != im.size:
        im = im.resize(new_size, Image.LANCZOS)
    output = io.BytesIO()
    im.save(output, format="WEBP", quality=85)
    return output.getvalue()


async def screenshot_url(url: str, width: int = 1200, height: int = 800) -> bytes:
    """Take a screenshot of a URL using pyppeteer."""
    from pyppeteer import launch

    browser = await launch(headless=True, args=["--no-sandbox"])
    page = await browser.newPage()
    await page.setViewport({"width": width, "height": height})
    await page.goto(url)
    data = await page.screenshot(fullPage=True)
    await browser.close()
    return data


def image_bytes_to_base64_webp(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")
