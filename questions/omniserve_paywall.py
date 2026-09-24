"""Map OmniServe gateway 401/402 responses to the shared paywall contract."""
import os
from typing import Any, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse

SUBSCRIBE_URL = os.getenv("TEXTGEN_SUBSCRIBE_URL", "https://text-generator.io/subscribe")
LOGIN_URL = os.getenv("TEXTGEN_LOGIN_URL", "https://text-generator.io/login")

_DEFAULT_MESSAGES = {
    401: "Log in to use this feature.",
    402: "Subscribe to Text Generator to use GPU-backed features.",
}


class SubscriptionRequired(HTTPException):
    def __init__(self, status_code: int = 402, message: Optional[str] = None, subscribe_url: Optional[str] = None):
        self.subscribe_url = subscribe_url or SUBSCRIBE_URL
        self.message = message or _DEFAULT_MESSAGES.get(status_code, _DEFAULT_MESSAGES[402])
        super().__init__(status_code=status_code, detail=self.message, headers={"X-Subscribe-URL": self.subscribe_url})

    def body(self) -> dict:
        code = "authentication_required" if self.status_code == 401 else "subscription_required"
        err = {"code": code, "message": self.message, "subscribe_url": self.subscribe_url}
        if self.status_code == 401:
            err["login_url"] = LOGIN_URL
        return {"error": err, "detail": self.message}


def paywall_response(exc: SubscriptionRequired) -> JSONResponse:
    return JSONResponse(exc.body(), status_code=exc.status_code, headers=exc.headers)


async def _handler(_request, exc: SubscriptionRequired) -> JSONResponse:
    return paywall_response(exc)


def install(app) -> None:
    app.add_exception_handler(SubscriptionRequired, _handler)


def from_upstream(status_code: int, body: Any = None, headers: Any = None) -> Optional[SubscriptionRequired]:
    """Return a SubscriptionRequired for upstream 401/402, else None."""
    if status_code not in (401, 402):
        return None
    err = body.get("error") if isinstance(body, dict) else None
    err = err if isinstance(err, dict) else {}
    message = err.get("message") if isinstance(err.get("message"), str) else None
    if not message and isinstance(body, dict) and isinstance(body.get("detail"), str):
        message = body["detail"]
    upstream_url = (headers or {}).get("X-Subscribe-URL") or err.get("subscribe_url")
    # Our own subscribe page is what our users can act on; keep upstream only if it is ours.
    url = upstream_url if isinstance(upstream_url, str) and "text-generator.io" in upstream_url else SUBSCRIBE_URL
    return SubscriptionRequired(status_code, message, url)


def raise_for_upstream(response) -> None:
    """Raise SubscriptionRequired if a requests/httpx response is 401/402."""
    status = getattr(response, "status_code", 0)
    if status not in (401, 402):
        return
    try:
        body = response.json()
    except Exception:
        body = None
    exc = from_upstream(status, body, getattr(response, "headers", None))
    if exc:
        raise exc
