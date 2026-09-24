"""Subscriber verification for the omniserve-native public auth gate.

The gateway (:8791) asks GET /internal/omniserve/verify with the caller's
credential in X-Subscriber-Credential and OMNISERVE_NATIVE_AUTH_VERIFY_SECRET
in X-Verify-Secret. 200 = paid/subscribed (tier in body), 402 = known account
without a subscription, 401 = unknown credential.

Sources: omniserve service keys (OMNISERVE_NATIVE_KEY_TIERS), text-generator.io
users (subscription or purchased credits), netwrck/ebank users
(OMNISERVE_VERIFY_NETWRCK_DSNS) and cutedsl users (OMNISERVE_VERIFY_CUTEDSL_DSN).
"""

import hashlib
import hmac
import logging
import os
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

SUBSCRIBE_URL = "https://text-generator.io/subscribe"
_TTL_OK = 300
_TTL_DENY = 60
_cache: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()


def _key_tiers() -> dict[str, str]:
    out = {}
    for entry in os.getenv("OMNISERVE_NATIVE_KEY_TIERS", "").split(","):
        key, _, tier = entry.strip().partition("=")
        if key and tier in {"paid", "sub", "free", "background"}:
            out[key] = tier
    return out


def service_key_tier(credential: Optional[str]) -> Optional[str]:
    if not credential:
        return None
    for key, tier in _key_tiers().items():
        if hmac.compare_digest(key.encode(), credential.encode()):
            return tier
    return None


def _query_one(dsn: str, sql: str, credential: str):
    import psycopg2

    conn = psycopg2.connect(dsn, connect_timeout=3)
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 3000")
            cur.execute(sql, (credential,))
            return cur.fetchone()
    finally:
        conn.close()


def _netwrck(credential: str) -> Optional[bool]:
    found = None
    for dsn in filter(None, (d.strip() for d in os.getenv("OMNISERVE_VERIFY_NETWRCK_DSNS", "").split(","))):
        row = _query_one(
            dsn,
            "SELECT COALESCE(is_subscribed, false) AND (subscription_end IS NULL OR subscription_end > now()),"
            " COALESCE(paid_credits, 0) > 0 FROM users WHERE secret = %s LIMIT 1",
            credential,
        )
        if row is not None:
            if row[0] or row[1]:
                return True
            found = False
    return found


def _cutedsl(credential: str) -> Optional[bool]:
    dsn = os.getenv("OMNISERVE_VERIFY_CUTEDSL_DSN", "").strip()
    if not dsn:
        return None
    row = _query_one(
        dsn,
        "SELECT COALESCE(subscription_status, '') IN ('active', 'trialing') OR COALESCE(unlimited_api, false)"
        " OR (COALESCE(total_deposited, 0) > 0 AND COALESCE(credits, 0) > 0) FROM users WHERE api_key = %s LIMIT 1",
        credential,
    )
    return None if row is None else bool(row[0])


def verify_credential(credential: Optional[str], textgen_check: Optional[Callable[[str], Optional[bool]]] = None) -> dict:
    """{"status": 200|401|402|503, "tier": ..., "source": ...}. Cached per credential."""
    if not credential or len(credential) > 255:
        return {"status": 401}
    tier = service_key_tier(credential)
    if tier:
        return {"status": 200, "tier": tier, "source": "service"}
    ck = ("t:" if textgen_check else "x:") + hashlib.sha256(credential.encode()).hexdigest()
    now = time.time()
    with _lock:
        hit = _cache.get(ck)
        if hit and hit[0] > now:
            return hit[1]
    found_unsubscribed = False
    errors = 0
    checks = [("textgen", textgen_check), ("netwrck", _netwrck), ("cutedsl", _cutedsl)]
    for source, check in checks:
        if check is None:
            continue
        try:
            ok = check(credential)
        except Exception as exc:
            errors += 1
            logger.warning("subscriber verify %s failed: %s", source, type(exc).__name__)
            continue
        if ok:
            result = {"status": 200, "tier": "sub", "source": source}
            break
        if ok is False:
            found_unsubscribed = True
    else:
        if found_unsubscribed:
            result = {"status": 402}
        elif errors:
            return {"status": 503}
        else:
            result = {"status": 401}
    with _lock:
        if len(_cache) > 20000:
            _cache.clear()
        _cache[ck] = (now + (_TTL_OK if result["status"] == 200 else _TTL_DENY), result)
    return result


def verify_secret_ok(presented: Optional[str]) -> bool:
    expected = os.getenv("OMNISERVE_NATIVE_AUTH_VERIFY_SECRET", "")
    return bool(expected and presented and hmac.compare_digest(expected.encode(), presented.encode()))


def subscription_error_body(status: int) -> dict:
    message = (
        "An API key from a paid or subscribed account is required."
        if status == 401
        else "This API is available to paid and subscribed accounts. Subscribe to continue."
    )
    return {"error": {"code": "subscription_required", "message": message, "subscribe_url": SUBSCRIBE_URL}}
