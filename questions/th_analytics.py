import asyncio
import os
import time
from typing import Any, Dict, Optional

import requests

from questions.logging_config import get_logger

logger = get_logger(__name__)

TH_COLLECT_URL = os.getenv("TH_COLLECT_URL", "https://twohelixes.com/v1/collect")
TH_WRITE_KEY = os.getenv("TH_WRITE_KEY", "thw_KoyqFMBVIwVqJuuxLQpQ8d9Ry6aJi4to")


def send_event(
    event: str,
    event_id: str,
    client_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    props: Optional[Dict[str, Any]] = None,
) -> None:
    if not TH_WRITE_KEY:
        return
    body: Dict[str, Any] = {
        "site_id": TH_WRITE_KEY,
        "event": event,
        "event_id": event_id,
        "client_id": client_id,
        "ts": int(time.time() * 1000),
        "page_location": "https://text-generator.io/webhook",
        "props": props or {},
    }
    if user_id:
        body["user_id"] = user_id
    if session_id:
        body["session_id"] = session_id
    try:
        requests.post(TH_COLLECT_URL, json=body, headers={"User-Agent": "text-generator.io-server/1.0"}, timeout=5)
    except Exception as exc:
        logger.warning("twohelixes %s send failed: %s", event, exc)


def send_event_background(*args: Any, **kwargs: Any) -> None:
    try:
        asyncio.get_running_loop().run_in_executor(None, lambda: send_event(*args, **kwargs))
    except RuntimeError:
        send_event(*args, **kwargs)
