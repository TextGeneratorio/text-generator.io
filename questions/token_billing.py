from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Mapping, Optional

from sqlalchemy import func

from questions import token_pricing as tp
from questions.db_models_postgres import StripeCreditEvent, TokenAccrual, TokenUsage

logger = logging.getLogger(__name__)

_tier_cache: dict[str, tuple[float, tuple[str, float]]] = {}
_lite_cache: dict[str, tuple[float, bool]] = {}
CACHE_TTL = 300


def enforce_allowance() -> bool:
    return os.getenv("TEXTGEN_SUB_ALLOWANCE_ENFORCE", "0") == "1"


def lite_price_id() -> str:
    return os.getenv("TEXTGEN_LITE_PRICE_ID", "price_0UMlOkDtz2XsjQROq3UgqEw0")


def prepaid_cents_90d(db, stripe_id: str) -> int:
    since = datetime.utcnow() - timedelta(days=90)
    total = (
        db.query(func.coalesce(func.sum(StripeCreditEvent.credits_cents), 0))
        .filter(StripeCreditEvent.stripe_id == stripe_id, StripeCreditEvent.created >= since)
        .scalar()
    )
    return int(total or 0)


def volume_tier(db, stripe_id: str) -> tuple[str, float]:
    now = time.time()
    hit = _tier_cache.get(stripe_id)
    if hit and hit[0] > now:
        return hit[1]
    result = tp.tier_for_prepaid(prepaid_cents_90d(db, stripe_id))
    _tier_cache[stripe_id] = (now + CACHE_TTL, result)
    return result


def cost_30d_cents(db, stripe_id: str) -> float:
    since = datetime.utcnow() - timedelta(days=30)
    micro = (
        db.query(func.coalesce(func.sum(TokenUsage.cost_micro), 0))
        .filter(TokenUsage.stripe_id == stripe_id, TokenUsage.created >= since)
        .scalar()
    )
    return float(micro or 0) / tp.MICRO


def is_lite_subscriber(stripe_id: str) -> bool:
    price = lite_price_id()
    if not price or not stripe_id:
        return False
    now = time.time()
    hit = _lite_cache.get(stripe_id)
    if hit and hit[0] > now:
        return hit[1]
    result = False
    try:
        from questions.payments.payments import get_subscription_data_for

        for sub in get_subscription_data_for(stripe_id):
            if sub.get("status") not in ("active", "trialing", "past_due"):
                continue
            for item in (sub.get("items") or {}).get("data", []):
                if (item.get("price") or {}).get("id") == price:
                    result = True
    except Exception as exc:
        logger.warning("lite plan lookup failed for %s: %s", stripe_id, exc)
    _lite_cache[stripe_id] = (now + CACHE_TTL, result)
    return result


def allowance_cents(stripe_id: str) -> int:
    plan = tp.LITE_PLAN_PRICE_CENTS if is_lite_subscriber(stripe_id) else tp.PLAN_PRICE_CENTS
    return tp.included_cost_cents(plan)


def allowance_blocked(db, stripe_id: str, balance_cents: int) -> bool:
    if not enforce_allowance() or balance_cents >= 1:
        return False
    return cost_30d_cents(db, stripe_id) >= allowance_cents(stripe_id)


def _accrue(db, stripe_id: str, micro: int) -> int:
    row = db.query(TokenAccrual).filter(TokenAccrual.stripe_id == stripe_id).with_for_update().first()
    if row is None:
        row = TokenAccrual(stripe_id=stripe_id, micro=0)
        db.add(row)
    total = int(row.micro or 0) + micro
    whole = total // tp.MICRO
    row.micro = total - whole * tp.MICRO
    return whole


def bill_usage(
    db,
    user: Any,
    model_id: str,
    usage: Optional[Mapping[str, Any]],
    *,
    subscribed: bool,
    lane: Optional[str] = None,
    overflowed: bool = False,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
) -> dict[str, Any]:
    from questions.credits import get_stripe_credit_balance_cents, set_stripe_credit_balance_cents

    stripe_id = getattr(user, "stripe_id", None)
    if not stripe_id:
        return {"charged_cents": 0, "recorded": False}
    p, c = tp.usage_tokens(usage)
    if prompt_tokens is not None:
        p = prompt_tokens
    if completion_tokens is not None:
        c = completion_tokens
    lane = lane or tp.lane_for(model_id, overflowed)
    tier_name, _ = volume_tier(db, stripe_id)
    cost = tp.cost_micro(model_id, lane, p, c)
    charge = tp.charge_micro(model_id, lane, tier_name, p, c)
    bill = charge
    if subscribed:
        within = cost_30d_cents(db, stripe_id) < allowance_cents(stripe_id)
        bill = 0 if (within or not enforce_allowance()) else charge
    whole = 0
    try:
        if bill:
            whole = _accrue(db, stripe_id, bill)
        db.add(
            TokenUsage(
                stripe_id=stripe_id,
                user_id=getattr(user, "id", None),
                model=model_id,
                lane=lane,
                tier=tier_name,
                prompt_tokens=p,
                completion_tokens=c,
                cost_micro=cost,
                charge_micro=charge,
                billed_micro=bill,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("token usage ledger write failed for %s", stripe_id)
        return {"charged_cents": 0, "recorded": False}
    if whole:
        balance = get_stripe_credit_balance_cents(stripe_id)
        new_balance = set_stripe_credit_balance_cents(stripe_id, max(0, balance - whole))
        try:
            user.free_credits = new_balance
            db.commit()
        except Exception:
            db.rollback()
    return {"charged_cents": whole, "billed_micro": bill, "cost_micro": cost, "lane": lane, "tier": tier_name, "recorded": True}
