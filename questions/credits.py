"""Text Generator prepaid credits and Stripe auto-topup helpers."""

from __future__ import annotations

import logging
import math
import os
from typing import Any, Optional

import stripe

logger = logging.getLogger(__name__)

STRIPE_CREDIT_BALANCE_METADATA_KEY = "textgen_credit_balance_cents"
STRIPE_PAYMENT_METHOD_METADATA_KEY = "textgen_payment_method_id"
STRIPE_AUTOTOPUP_ENABLED_KEY = "textgen_autotopup_enabled"
STRIPE_AUTOTOPUP_THRESHOLD_KEY = "textgen_autotopup_threshold_cents"
STRIPE_AUTOTOPUP_AMOUNT_KEY = "textgen_autotopup_amount_cents"

CREDIT_PACK_UNIT_CENTS = 1
DEFAULT_AUTOTOPUP_THRESHOLD_CENTS = 100
DEFAULT_AUTOTOPUP_AMOUNT_CENTS = 500
MIN_AUTOTOPUP_AMOUNT_CENTS = 100
MAX_AUTOTOPUP_AMOUNT_CENTS = 100_000

TTS_CHARS_PER_SECOND = 15.0
TTS_MIN_BILLED_SECONDS = 15.0
APPNZ_TTS_PRICE_PER_MINUTE = {
    "appnz-tts": 0.10,
    "fish-speech": 0.10,
    "pocket-tts": 0.06,
}


def get_stripe_credit_balance_cents(stripe_id: Optional[str]) -> int:
    if not stripe_id:
        return 0
    try:
        customer = stripe.Customer.retrieve(stripe_id)
        metadata = getattr(customer, "metadata", None) or customer.get("metadata", {}) or {}
        return max(0, int(metadata.get(STRIPE_CREDIT_BALANCE_METADATA_KEY, 0)))
    except Exception as exc:
        logger.warning("Failed to read Stripe credit balance for %s: %s", stripe_id, exc)
        return 0


def set_stripe_credit_balance_cents(stripe_id: str, balance_cents: int) -> int:
    normalized_balance = max(0, int(balance_cents))
    stripe.Customer.modify(
        stripe_id,
        metadata={STRIPE_CREDIT_BALANCE_METADATA_KEY: str(normalized_balance)},
    )
    return normalized_balance


def increment_stripe_credit_balance_cents(stripe_id: Optional[str], delta_cents: int) -> int:
    if not stripe_id or not delta_cents:
        return get_stripe_credit_balance_cents(stripe_id)
    current_balance = get_stripe_credit_balance_cents(stripe_id)
    return set_stripe_credit_balance_cents(stripe_id, current_balance + int(delta_cents))


def _customer_metadata(stripe_id: Optional[str]) -> dict[str, str]:
    if not stripe_id:
        return {}
    try:
        customer = stripe.Customer.retrieve(stripe_id)
        metadata = getattr(customer, "metadata", None) or customer.get("metadata", {}) or {}
        return {str(k): str(v) for k, v in dict(metadata).items()}
    except Exception as exc:
        logger.warning("Failed to load Stripe customer metadata for %s: %s", stripe_id, exc)
        return {}


def get_autotopup_settings(stripe_id: Optional[str]) -> dict[str, Any]:
    metadata = _customer_metadata(stripe_id)
    payment_method = metadata.get(STRIPE_PAYMENT_METHOD_METADATA_KEY, "")
    threshold = int(metadata.get(STRIPE_AUTOTOPUP_THRESHOLD_KEY, DEFAULT_AUTOTOPUP_THRESHOLD_CENTS) or DEFAULT_AUTOTOPUP_THRESHOLD_CENTS)
    amount = int(metadata.get(STRIPE_AUTOTOPUP_AMOUNT_KEY, DEFAULT_AUTOTOPUP_AMOUNT_CENTS) or DEFAULT_AUTOTOPUP_AMOUNT_CENTS)
    return {
        "enabled": metadata.get(STRIPE_AUTOTOPUP_ENABLED_KEY, "0") == "1",
        "threshold": max(0, threshold),
        "amount": max(0, amount),
        "hasCard": bool(payment_method),
    }


def set_autotopup_settings(
    stripe_id: str,
    *,
    enabled: bool,
    threshold: int,
    amount: int,
) -> dict[str, Any]:
    threshold = max(0, min(int(threshold), MAX_AUTOTOPUP_AMOUNT_CENTS))
    amount = max(0, min(int(amount), MAX_AUTOTOPUP_AMOUNT_CENTS))
    if enabled and amount < MIN_AUTOTOPUP_AMOUNT_CENTS:
        raise ValueError(f"amount must be at least {MIN_AUTOTOPUP_AMOUNT_CENTS} credits")
    metadata = _customer_metadata(stripe_id)
    if enabled and not metadata.get(STRIPE_PAYMENT_METHOD_METADATA_KEY):
        raise ValueError("Buy credits once to save a card before enabling auto-topup")
    stripe.Customer.modify(
        stripe_id,
        metadata={
            STRIPE_AUTOTOPUP_ENABLED_KEY: "1" if enabled else "0",
            STRIPE_AUTOTOPUP_THRESHOLD_KEY: str(threshold),
            STRIPE_AUTOTOPUP_AMOUNT_KEY: str(amount),
        },
    )
    return get_autotopup_settings(stripe_id)


def store_payment_method_id(stripe_id: Optional[str], payment_method_id: Optional[str]) -> None:
    if not stripe_id or not payment_method_id:
        return
    try:
        stripe.Customer.modify(
            stripe_id,
            metadata={STRIPE_PAYMENT_METHOD_METADATA_KEY: payment_method_id},
        )
    except Exception as exc:
        logger.warning("Failed to store payment method for %s: %s", stripe_id, exc)


def payment_method_from_checkout_session(session: dict[str, Any]) -> Optional[str]:
    payment_intent_id = session.get("payment_intent")
    if not payment_intent_id:
        return None
    try:
        if isinstance(payment_intent_id, dict):
            return payment_intent_id.get("payment_method")
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return getattr(intent, "payment_method", None) or intent.get("payment_method")
    except Exception as exc:
        logger.warning("Failed to load payment method from checkout session: %s", exc)
        return None


def maybe_autotopup(stripe_id: Optional[str]) -> Optional[int]:
    """Charge the saved card when balance is at/below threshold. Returns new balance or None."""
    if not stripe_id:
        return None
    settings = get_autotopup_settings(stripe_id)
    if not settings["enabled"] or not settings["hasCard"] or settings["amount"] <= 0:
        return None
    balance = get_stripe_credit_balance_cents(stripe_id)
    if balance > settings["threshold"]:
        return None
    metadata = _customer_metadata(stripe_id)
    payment_method = metadata.get(STRIPE_PAYMENT_METHOD_METADATA_KEY)
    if not payment_method:
        return None
    amount_cents = int(settings["amount"]) * CREDIT_PACK_UNIT_CENTS
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            customer=stripe_id,
            payment_method=payment_method,
            off_session=True,
            confirm=True,
            description=f"Text Generator auto-topup {settings['amount']} credits",
            metadata={
                "purchase_type": "credits",
                "credit_unit_cents": str(CREDIT_PACK_UNIT_CENTS),
                "quantity": str(settings["amount"]),
                "source": "autotopup",
            },
        )
    except Exception as exc:
        logger.warning("Auto-topup failed for %s: %s", stripe_id, exc)
        return None
    status = getattr(intent, "status", None) or intent.get("status")
    if status != "succeeded":
        logger.warning("Auto-topup intent status=%s for %s", status, stripe_id)
        return None
    return increment_stripe_credit_balance_cents(stripe_id, settings["amount"])


def estimate_appnz_tts_credits(model: str, text: str) -> int:
    price_per_minute = APPNZ_TTS_PRICE_PER_MINUTE.get((model or "").strip().lower(), 0.10)
    seconds = max(TTS_MIN_BILLED_SECONDS, len(text or "") / TTS_CHARS_PER_SECOND)
    dollars = price_per_minute * seconds / 60.0
    return max(1, int(math.ceil(dollars * 100)))


def appnz_tts_upstream_url() -> str:
    cog = os.getenv("APPNZ_TTS_COG_URL", "").strip().rstrip("/")
    if cog:
        return f"{cog}/v1/audio/speech"
    base = os.getenv("APPNZ_TTS_URL", "https://app.nz").strip().rstrip("/")
    return f"{base}/v1/audio/speech"


def appnz_api_key() -> str:
    from questions.provider_catalog import PROVIDERS_BY_SLUG
    from questions.provider_router import provider_api_key

    return provider_api_key(PROVIDERS_BY_SLUG["appnz"])
