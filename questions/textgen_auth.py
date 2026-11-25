"""Staged auth for money-costing text-generator.io endpoints.

TEXTGEN_AUTH_MODE = off | warn | enforce   (default: warn)
  off      no checks, no logs (the pre-existing behaviour).
  warn     every request that enforce would reject is logged as
           ``textgen_auth would_reject ...`` and then served anyway.
  enforce  rejected requests get a 401/402/429 JSON body (the shared paywall
           contract from questions.omniserve_paywall).

Accepted credentials, checked in this order:
  1. Internal service keys: TEXTGEN_INTERNAL_API_KEYS="name:key,name2:key2"
     (a bare "key" is named by a short hash) and/or TEXTGEN_INTERNAL_API_KEYS_FILE
     (one name:key per line). Every accepted request is logged with the key name.
  2. Short-lived signed tokens minted by our own backends (mint_token) with
     TEXTGEN_TOKEN_SECRET, sent as ``Authorization: Bearer tgt1.<exp>.<sub>.<sig>``.
  3. Paying-user keys (the account ``secret``), verified by the injected
     ``paid_check`` callable, which returns "sub"/"paid"/True for a paying
     account, False for a known account without a subscription/credits and
     None for an unknown key.
  4. Free tier for our own browser pages: requests whose Origin (or Referer)
     is in TEXTGEN_FREE_ORIGINS, limited to TEXTGEN_FREE_RPM requests per
     minute per client IP and TEXTGEN_FREE_MAX_LENGTH tokens. Origin is
     spoofable outside a browser, which is why the tier is small and rate
     limited. Set TEXTGEN_FREE_RPM=0 to disable it.

Credentials are never logged; callers are identified by key name or a short
hash prefix.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import urlsplit

logger = logging.getLogger("textgen_auth")

MODES = ("off", "warn", "enforce")
TOKEN_PREFIX = "tgt1"
MAX_TOKEN_TTL_S = 3600
_RELAY_HEADERS = (
    "x-forwarded-for", "x-real-ip", "cf-connecting-ip", "cf-ray", "forwarded", "via", "true-client-ip",
)
DEFAULT_FREE_ORIGINS = "https://text-generator.io,https://www.text-generator.io"


def auth_mode() -> str:
    mode = os.getenv("TEXTGEN_AUTH_MODE", "warn").strip().lower()
    return mode if mode in MODES else "warn"


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:8]


def internal_keys() -> dict[str, str]:
    """key -> name, from TEXTGEN_INTERNAL_API_KEYS and TEXTGEN_INTERNAL_API_KEYS_FILE."""
    entries = [e for e in os.getenv("TEXTGEN_INTERNAL_API_KEYS", "").split(",")]
    path = os.getenv("TEXTGEN_INTERNAL_API_KEYS_FILE", "").strip()
    if path:
        try:
            with open(path) as fh:
                entries += [line for line in fh.read().splitlines() if not line.lstrip().startswith("#")]
        except OSError as exc:
            logger.warning("textgen_auth cannot read TEXTGEN_INTERNAL_API_KEYS_FILE: %s", type(exc).__name__)
    out = {}
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        name, sep, key = entry.partition(":")
        if not sep:
            name, key = "", name
        key = key.strip()
        if len(key) >= 16:
            out[key] = name.strip() or _short_hash(key)
    return out


def internal_key_name(credential: Optional[str]) -> Optional[str]:
    if not credential:
        return None
    for key, name in internal_keys().items():
        if hmac.compare_digest(key.encode(), credential.encode()):
            return name
    return None


# --- signed tokens ---------------------------------------------------------

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _token_sig(secret: str, payload: str) -> str:
    return _b64(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())


def mint_token(subject: str, ttl_s: int = 600, secret: Optional[str] = None, now: Optional[float] = None) -> str:
    """Mint a short-lived browser token. For our backends, never for the browser itself."""
    secret = secret or os.getenv("TEXTGEN_TOKEN_SECRET", "")
    if not secret:
        raise ValueError("TEXTGEN_TOKEN_SECRET is not set")
    subject = "".join(c for c in subject if c.isalnum() or c in "-_")[:64] or "anon"
    exp = int((now or time.time()) + max(1, min(int(ttl_s), MAX_TOKEN_TTL_S)))
    payload = f"{TOKEN_PREFIX}.{exp}.{subject}"
    return f"{payload}.{_token_sig(secret, payload)}"


def verify_token(token: Optional[str], now: Optional[float] = None) -> tuple[Optional[str], str]:
    """(subject, "") when valid, else (None, reason)."""
    secret = os.getenv("TEXTGEN_TOKEN_SECRET", "")
    if not token or not token.startswith(TOKEN_PREFIX + "."):
        return None, "not_a_token"
    if not secret:
        return None, "token_secret_unset"
    parts = token.split(".")
    if len(parts) != 4:
        return None, "token_malformed"
    payload = ".".join(parts[:3])
    if not hmac.compare_digest(_token_sig(secret, payload), parts[3]):
        return None, "token_bad_signature"
    try:
        exp = int(parts[1])
    except ValueError:
        return None, "token_malformed"
    now = now or time.time()
    if exp < now:
        return None, "token_expired"
    if exp > now + MAX_TOKEN_TTL_S + 60:
        return None, "token_ttl_too_long"
    return parts[2], ""


# --- free tier -------------------------------------------------------------

class _RateLimiter:
    def __init__(self):
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_s: float = 60.0, now: Optional[float] = None) -> bool:
        if limit <= 0:
            return False
        now = now or time.monotonic()
        with self._lock:
            if len(self._hits) > 50000:
                self._hits.clear()
            q = self._hits.setdefault(key, deque())
            while q and q[0] <= now - window_s:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def reset(self):
        with self._lock:
            self._hits.clear()


free_limiter = _RateLimiter()


def free_origins() -> set[str]:
    raw = os.getenv("TEXTGEN_FREE_ORIGINS", DEFAULT_FREE_ORIGINS)
    return {o.strip().rstrip("/").lower() for o in raw.split(",") if o.strip()}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def free_rpm() -> int:
    return _int_env("TEXTGEN_FREE_RPM", 6)


def free_max_length() -> int:
    return _int_env("TEXTGEN_FREE_MAX_LENGTH", 64)


def request_origin(headers) -> str:
    origin = (headers.get("origin") or "").strip()
    if not origin or origin == "null":
        ref = (headers.get("referer") or "").strip()
        if ref:
            parts = urlsplit(ref)
            origin = f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else ""
    return origin.rstrip("/").lower()


def client_ip(request) -> str:
    h = request.headers
    ip = (h.get("cf-connecting-ip") or h.get("x-real-ip") or "").strip()
    if not ip:
        ip = (h.get("x-forwarded-for") or "").split(",")[0].strip()
    if not ip and getattr(request, "client", None):
        ip = request.client.host or ""
    return ip or "unknown"


def is_internal_request(request) -> bool:
    """Loopback peer with no relay header: the same rule as the omniserve-native gate."""
    host = request.client.host if getattr(request, "client", None) else ""
    return host in {"127.0.0.1", "::1", "localhost"} and not any(h in request.headers for h in _RELAY_HEADERS)


# --- decision --------------------------------------------------------------

def request_credential(request) -> Optional[str]:
    h = request.headers
    auth = h.get("authorization") or ""
    if auth[:7].lower() == "bearer " and auth[7:].strip():
        return auth[7:].strip()
    for name in ("secret", "x-api-key", "x-rapid-api-key"):
        value = (h.get(name) or "").strip()
        if value:
            return value
    return None


@dataclass
class Decision:
    allowed: bool
    status: int  # 200 when allowed, else 401/402/429
    reason: str
    caller: str
    free_tier: bool = False
    max_length: Optional[int] = None


def decide(request, paid_check: Callable[[str], object], *, allow_internal_peer: bool = False,
           allow_free_tier: bool = True) -> Decision:
    if allow_internal_peer and is_internal_request(request):
        return Decision(True, 200, "internal_peer", "internal-peer")
    cred = request_credential(request)
    if cred:
        name = internal_key_name(cred)
        if name:
            return Decision(True, 200, "internal_key", f"internal:{name}")
        if cred.startswith(TOKEN_PREFIX + "."):
            subject, why = verify_token(cred)
            if subject:
                return Decision(True, 200, "signed_token", f"token:{subject}")
            denied = Decision(False, 401, why, "token")
        else:
            try:
                verdict = paid_check(cred)
            except Exception as exc:  # verifier outage must not turn into free service or a hard outage
                logger.warning("textgen_auth paid_check failed: %s", type(exc).__name__)
                verdict = "error"
            if verdict == "error":
                return Decision(True, 200, "verify_error_fail_open", f"key:{_short_hash(cred)}")
            if verdict:
                return Decision(True, 200, "paid_key", f"key:{_short_hash(cred)}")
            if verdict is False:
                denied = Decision(False, 402, "not_subscribed", f"key:{_short_hash(cred)}")
            else:
                denied = Decision(False, 401, "unknown_key", f"key:{_short_hash(cred)}")
    else:
        denied = Decision(False, 401, "missing_credential", "anonymous")

    if allow_free_tier and free_rpm() > 0:
        origin = request_origin(request.headers)
        if origin and origin in free_origins():
            ip = client_ip(request)
            if free_limiter.allow(f"{ip}", free_rpm()):
                return Decision(True, 200, f"free_tier:{denied.reason}", f"free:{origin}",
                                free_tier=True, max_length=free_max_length())
            return Decision(False, 429, f"free_tier_rate_limited:{denied.reason}", f"free:{origin}")
    return denied


def _log_line(event: str, mode: str, endpoint: str, d: Decision, request) -> str:
    origin = request_origin(request.headers) or "-"
    ip_hash = _short_hash(client_ip(request))
    ua = (request.headers.get("user-agent") or "-")[:60].replace('"', "'")
    return (f"textgen_auth {event} mode={mode} endpoint={endpoint} status={d.status} reason={d.reason} "
            f"caller={d.caller} origin={origin} ip={ip_hash} ua=\"{ua}\"")


def gate(request, endpoint: str, paid_check: Callable[[str], object], **kwargs) -> Optional[Decision]:
    """Returns the Decision when the request may proceed, raises SubscriptionRequired/HTTPException
    in enforce mode when it may not, and returns None when auth is off."""
    mode = auth_mode()
    if mode == "off":
        return None
    d = decide(request, paid_check, **kwargs)
    if d.allowed:
        if d.reason in ("internal_key", "signed_token", "verify_error_fail_open") or d.free_tier:
            logger.info(_log_line("accept", mode, endpoint, d, request))
        return d
    if mode == "warn":
        logger.warning(_log_line("would_reject", mode, endpoint, d, request))
        return Decision(True, 200, f"warn:{d.reason}", d.caller)
    logger.warning(_log_line("reject", mode, endpoint, d, request))
    from fastapi import HTTPException

    if d.status == 429:
        raise HTTPException(status_code=429, detail="Free tier rate limit reached. Log in with a paid API key "
                                                    "or subscribe at https://text-generator.io/subscribe",
                            headers={"Retry-After": "60"})
    from questions.omniserve_paywall import SubscriptionRequired

    message = None
    if d.status == 401:
        message = ("A valid API key is required. Send your key from https://text-generator.io/account "
                   "as the 'secret' header or 'Authorization: Bearer <key>'.")
    raise SubscriptionRequired(d.status, message)


def clamp_max_length(params, decision: Optional[Decision]) -> None:
    """Free-tier requests get a short generation budget."""
    if decision is None or not decision.free_tier or not decision.max_length:
        return
    current = getattr(params, "max_length", None)
    if current is None or current > decision.max_length:
        params.max_length = decision.max_length
    if getattr(params, "number_of_results", None) and params.number_of_results > 1:
        params.number_of_results = 1
