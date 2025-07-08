import os
import re
import traceback
from io import BytesIO
from pathlib import Path
from typing import FrozenSet

import bs4
import cachetools
from PIL import Image
from cachetools import cached
import logging
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
from requests_futures.sessions import FuturesSession
try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    torch = None
from transformers import pipeline
from questions.inference_server.model_cache import ModelCache

# change into OFA dir
from questions.image_utils.scaler import scale_down
from questions.ocr_tess import ocr_tess
from questions.utils import log_time, debug


session = FuturesSession(max_workers=10)

# link_regex = re.compile('((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)', re.DOTALL)
# link_regex = "(?P<url>https?://[A-Za-z0-9_.~!*'();:@&=+$,/?#[%-]]+)"
# link_regex=r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[%\w\.-]*)*/?)\b"
link_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
# captures groups :/
def get_urls(string):
    urls = re.findall(link_regex, string)
    return [url[0] for url in urls]  # because this regex has capture groups/too afraid to change it


def find_value(soup, value):
    result = soup.find(value)
    if result:
        return result.value


def find_text(soup, text):
    result = soup.find(text)
    if result:
        return result.text


def get_title_from_html(html, long_description=False):
    soup = bs4.BeautifulSoup(html, "html.parser")
    title = find_text(soup, "title") or find_text(soup, "h1")
    if long_description:
        title += (
            " - " + find_value(soup, 'meta[name="description"]')
            or find_value(soup, 'meta[property="og:description"]')
            or find_value(soup, 'meta[name="twitter:description"]')
        )
        if len(title) < 20:
            title += (
                " - " + find_value(soup, 'meta[name="keywords"]')
                or find_value(soup, 'meta[property="og:keywords"]')
                or find_value(soup, 'meta[name="twitter:keywords"]')
            )
    if not long_description and len(title) > 200:
        title = title[:200]
    return title


image_mime_types = [
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/tiff",
    "image/x-icon",
    "image/svg+xml",
    "image/svg",
    "image/x-ms-bmp",
    "image/x-icon",
    "image/x-bmp",
    "image/x-xbitmap",
    "image/x-win-bitmap",
    "image/x-windows-bmp",
    "image/x-ms-bmp",
]

audio_mime_types = [
    "audio/mp3",
]

ocr_tags = ["receipt", 'screenshot', 'licence', 'document', 'paper', 'sign', 'advert', 'book', 'logo', 'screen']

LINK_MODEL_CACHE = ModelCache()

def load_gemma_pipe():
    """Load the Gemma model for image captioning and text generation."""
    model_id = os.getenv("GEMMA_MODEL_ID", "google/gemma-3n-e4b-it")
    device_env = os.getenv("GEMMA_DEVICE")
    if device_env is not None:
        device = int(device_env)
    else:
        device = 0 if torch and torch.cuda.is_available() else -1
    return pipeline(
        "image-text-to-text",
        model=model_id,
        device=device,
        torch_dtype=torch.bfloat16 if torch and torch.cuda.is_available() else None,
    )

def get_caption_for_image_response(response, prompt="Describe this image."):
    """Generate a caption for an image using Gemma."""
    response.raw.decode_content = True
    img = Image.open(BytesIO(response.content))

    with log_time("image captioning"):
        pipe = LINK_MODEL_CACHE.add_or_get("gemma_pipe", load_gemma_pipe)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": prompt},
                ],
            },
        ]
        output = pipe(text=messages, max_new_tokens=100)
        caption = output[0]["generated_text"][-1]["content"]

        if debug:
            logger.info(f"Image description: {caption}")

        if any(ocr_tag in caption.lower() for ocr_tag in ocr_tags):
            with log_time("OCR"):
                ocr_data = ocr_tess(img)
                caption += " " + ocr_data

    return caption


@cached(cachetools.TTLCache(maxsize=1000, ttl=60 * 60 * 3))
def cached_request_get(url):
    return session.get(url, timeout=3)


model_to_swap = None


@cached(cachetools.TTLCache(maxsize=10000, ttl=60 * 60 * 3))
def get_titles_from_urls(urls: FrozenSet[str], long_description=False):  # todo set based caching?
    """
    visit all the urls in parallel and get the titles with bs4
    """
    futures = []
    urls = list(urls)[:10]
    for url in urls:
        futures.append(cached_request_get(url))
    titles = []
    for future in futures:
        try:
            response = future.result()
            # if its text/html
            if (
                response.status_code == 200
                and "text/html" in response.headers["Content-Type"]
                or "text/html" in response.headers["content-type"]
            ):
                title = get_title_from_html(response.text, long_description)
                titles.append(title)
            # if its an image use azure captioning to get text
            elif (
                response.status_code == 200 and response.headers["Content-Type"] in image_mime_types
            ):
                with log_time("image captioning"):
                    title = get_caption_for_image_response(response)

                titles.append(title)
            elif (
                    response.status_code == 200 and response.headers["Content-Type"] in audio_mime_types
            ):
                # todo audio analysis
                # failed
                titles.append(None)
            else:
                # failed
                titles.append(None)

        except Exception as e:
            logger.error(e)
            # traceback
            traceback.print_exc()
            titles.append(None)
            continue
    return titles


def enrich_links(text: str):
    """
    Takes a string with potential http links and returns a string with the extra context added to any links found e.g.
    enrich_links("https://www.google.com/img.jpg") -> "fairy holding wand https://www.google.com/img.jpg"
    returns text if there are no links to enrich or no enrichment has succeeded
    """
    urls = get_urls(text)
    if not urls:
        return text

    titles = get_titles_from_urls(frozenset(urls))
    for url, title in zip(urls, titles):
        if title:
            text = text.replace(url, title + " " + url)
    # detect if it hasn't changed?
    return text


def enrich_links_remove_links(text: str):
    """
    Takes a string with potential http links and returns a string with the extra context added to any links found e.g.
    enrich_links("https://www.google.com/img.jpg") -> "fairy holding wand"
    returns text if there are no links to enrich or no enrichment has succeeded
    """
    urls = get_urls(text)
    if not urls:
        return text

    titles = get_titles_from_urls(frozenset(urls))
    for url, title in zip(urls, titles):
        if title:
            text = text.replace(url, title)
    # detect if it hasn't changed?
    return text
