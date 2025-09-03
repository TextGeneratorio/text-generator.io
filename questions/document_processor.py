from __future__ import annotations

import asyncio
from typing import Dict, Iterable

from markitdown import MarkItDown

_converter = MarkItDown()


def convert_to_markdown(source: str) -> str:
    """Convert a local file or URL to Markdown using MarkItDown."""
    if source.startswith(("http://", "https://")):
        result = _converter.convert_url(source)
    else:
        result = _converter.convert_local(source)
    return result.markdown


async def convert_documents_async(sources: Iterable[str]) -> Dict[str, str]:
    """Convert multiple documents concurrently to Markdown."""
    loop = asyncio.get_event_loop()
    tasks = {s: loop.run_in_executor(None, convert_to_markdown, s) for s in sources}
    results = {}
    for src, task in tasks.items():
        results[src] = await task
    return results
