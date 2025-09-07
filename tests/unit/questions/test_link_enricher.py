import logging

import pytest

bs4 = pytest.importorskip("bs4", reason="bs4 required for link enrichment tests")
from questions.link_enricher import enrich_links, get_urls
from questions.logging_config import setup_logging

pytestmark = pytest.mark.integration

setup_logging()
logger = logging.getLogger(__name__)


def test_get_urls():
    textimg = """<img src=\"https://static.text-generator.io/static/img/fairy3.jpeg\" alt=\""""
    urls = get_urls(textimg)
    assert urls == ["https://static.text-generator.io/static/img/fairy3.jpeg"]


def test_get_urls_from_text():
    textimg = """hey checkout https://static.text-generator.io/static/img/fairy3.jpeg \" alt=\""""
    urls = get_urls(textimg)
    assert urls == ["https://static.text-generator.io/static/img/fairy3.jpeg"]


def test_get_urls_w_escape_from_text():
    textimg = (
        """hey checkout https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-08-50.png"""
    )
    urls = get_urls(textimg)
    assert urls == ["https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-08-50.png"]


def test_get_urls_w_long_url():
    textimg = """ hey checkout - https://images2.minutemediacdn.com/image/upload/c_fill,w_1080,ar_16:9,f_auto,q_auto,g_auto/shape%2Fcover%2Fsport%2F516438-istock-637689912-981f23c58238ea01a6147d11f4c81765.jpg
 https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-08-50.png"""
    urls = get_urls(textimg)
    assert urls == [
        "https://images2.minutemediacdn.com/image/upload/c_fill,w_1080,ar_16:9,f_auto,q_auto,g_auto/shape%2Fcover%2Fsport%2F516438-istock-637689912-981f23c58238ea01a6147d11f4c81765.jpg",
        "https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-08-50.png",
    ]


def test_get_urls_w_no_url():
    textimg = """ hey checkout - hey.who is thi?"""
    urls = get_urls(textimg)
    assert urls == []


def test_get_urls_w_no_url_code():
    textimg = """def factorial(n):\n\tif n == 0:\n    \treturn 1\n\treturn factorial(n - 1) * n\n"""
    urls = get_urls(textimg)
    assert urls == []


def test_enrich_links_twitter():
    result = enrich_links("https://twitter.com/karpathy/status/1565578366886940672 ")
    # Twitter links might return browser not supported message or empty title
    # Just verify it returns a string
    assert isinstance(result, str)


def test_enrich_links_cache_():
    titles = enrich_links("https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-08-50.png")
    logger.info(titles)
    # same request:
    titles2 = enrich_links("https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-08-50.png")
    logger.info(titles2)
    assert titles == titles2

    # a group of people sitting at a table? TODO bail out for low probability captions
    titles = enrich_links("https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-07-42.png")
    logger.info(titles)
    titles2 = enrich_links("https://static.text-generator.io/static/img/Screenshot%20from%202022-09-12%2010-07-42.png")
    logger.info(titles2)
    assert titles == titles2

    # assert titles == [""]


def test_get_caption_with_custom_prompt():
    textimg = """https://static.text-generator.io/static/img/fairy3.jpeg"""
    result = enrich_links(textimg)
    assert "fairy" in result.lower()  # Basic check that it found a fairy


def test_get_caption_with_specific_prompt():
    textimg = """https://static.text-generator.io/static/img/fairy3.jpeg"""
    urls = get_urls(textimg)
    import requests

    from questions.link_enricher import get_caption_for_image_response

    response = requests.get(urls[0])
    caption = get_caption_for_image_response(response, prompt="What colors are most prominent in this image?")
    assert any(color in caption.lower() for color in ["blue", "red", "green", "white", "black"])
