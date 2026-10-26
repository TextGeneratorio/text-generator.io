from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from questions import token_billing, token_pricing
from questions.db_models_postgres import CancellationSurvey, RetentionOffer, get_db

logger = logging.getLogger(__name__)

RETENTION_COUPON_ID = "CHURN50_3M"
LITE_LOOKUP_KEY = "textgen_lite_monthly_v1"
KIND_COUPON = "coupon"
KIND_DOWNGRADE = "downgrade"
ACTIVE_STATUSES = ("active", "trialing", "past_due")
SELF_HOSTED_PRICE_IDS = {"price_0MuAuxDtz2XsjQROz3Hp5Tcx", "price_0MuBEoDtz2XsjQROiRewGRFi"}
CANCEL_REASONS = (
    "too_expensive",
    "not_using",
    "missing_features",
    "quality",
    "switched_provider",
    "technical_issues",
    "temporary",
    "other",
)

router = APIRouter()


class CancelRequest(BaseModel):
    reason: str
    details: str = Field(default="", max_length=2000)
    offer_shown: Optional[str] = None


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _items(sub: Any) -> list:
    items = _get(sub, "items")
    data = _get(items, "data", []) if items is not None else []
    return list(data or [])


def find_active_subscription(stripe_id: str):
    subs = stripe.Subscription.list(customer=stripe_id, status="all", limit=20)
    for sub in _get(subs, "data", []):
        if _get(sub, "status") not in ACTIVE_STATUSES:
            continue
        items = _items(sub)
        if items and _get(_get(items[0], "price"), "id") in SELF_HOSTED_PRICE_IDS:
            continue
        return sub
    return None


def _plan_cents(sub: Any) -> int:
    items = _items(sub)
    if not items:
        return token_pricing.PLAN_PRICE_CENTS
    price = _get(items[0], "price") or {}
    amount = _get(price, "unit_amount")
    interval = _get(_get(price, "recurring") or {}, "interval", "month")
    if not amount:
        return token_pricing.PLAN_PRICE_CENTS
    return int(amount / 12) if interval == "year" else int(amount)


def _period_end(sub: Any) -> Optional[datetime]:
    ts = _get(sub, "current_period_end")
    if not ts:
        items = _items(sub)
        ts = _get(items[0], "current_period_end") if items else None
    return datetime.utcfromtimestamp(int(ts)) if ts else None


def _has_offer(db: Session, stripe_id: str, kind: str) -> bool:
    return db.query(RetentionOffer).filter(RetentionOffer.stripe_id == stripe_id, RetentionOffer.kind == kind).first() is not None


def _sub_has_coupon(sub: Any) -> bool:
    for d in _get(sub, "discounts", None) or []:
        if _get(_get(d, "coupon") or {}, "id") == RETENTION_COUPON_ID:
            return True
    return _get(_get(_get(sub, "discount"), "coupon") or {}, "id") == RETENTION_COUPON_ID


def _customer_flag(stripe_id: str) -> bool:
    try:
        customer = stripe.Customer.retrieve(stripe_id)
        meta = _get(customer, "metadata") or {}
        return str(_get(meta, "textgen_retention_coupon_used", "0")) == "1"
    except Exception as exc:
        logger.warning("retention flag lookup failed for %s: %s", stripe_id, exc)
        return False


def coupon_used(db: Session, stripe_id: str, sub: Any = None) -> bool:
    if _has_offer(db, stripe_id, KIND_COUPON):
        return True
    if sub is not None and _sub_has_coupon(sub):
        return True
    return _customer_flag(stripe_id)


def compute_offer(db: Session, stripe_id: str, sub: Any) -> dict[str, Any]:
    if sub is None:
        return {"offer": "none", "reason": "no_active_subscription"}
    if _get(sub, "cancel_at_period_end"):
        return {"offer": "none", "reason": "already_canceling"}
    plan = _plan_cents(sub)
    cost = token_billing.cost_30d_cents(db, stripe_id)
    on_lite = plan <= token_pricing.LITE_PLAN_PRICE_CENTS
    negative = token_pricing.coupon_margin_negative(cost, plan)
    if negative:
        if on_lite or _has_offer(db, stripe_id, KIND_DOWNGRADE):
            return {"offer": "none", "reason": "no_margin_for_offers", "cost_30d_cents": round(cost, 2)}
        return {
            "offer": "downgrade",
            "cost_30d_cents": round(cost, 2),
            "lite_price_cents": token_pricing.LITE_PLAN_PRICE_CENTS,
            "lite_included_cost_cents": token_pricing.LITE_INCLUDED_COST_CENTS,
        }
    if coupon_used(db, stripe_id, sub):
        return {"offer": "none", "reason": "coupon_already_used"}
    return {"offer": "coupon", "coupon_id": RETENTION_COUPON_ID, "percent_off": 50, "months": 3}


def apply_coupon(db: Session, user: Any, sub: Any) -> dict[str, Any]:
    offer = compute_offer(db, user.stripe_id, sub)
    if offer["offer"] != "coupon":
        raise HTTPException(status_code=409, detail=offer)
    db.add(RetentionOffer(stripe_id=user.stripe_id, user_id=user.id, kind=KIND_COUPON))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={"offer": "none", "reason": "coupon_already_used"})
    try:
        stripe.Subscription.modify(_get(sub, "id"), discounts=[{"coupon": RETENTION_COUPON_ID}])
        stripe.Customer.modify(user.stripe_id, metadata={"textgen_retention_coupon_used": "1"})
    except Exception as exc:
        logger.error("retention coupon apply failed for %s: %s", user.stripe_id, exc)
        db.query(RetentionOffer).filter(
            RetentionOffer.stripe_id == user.stripe_id, RetentionOffer.kind == KIND_COUPON
        ).delete()
        db.commit()
        raise HTTPException(status_code=502, detail="Failed to apply discount")
    return {"success": True, "message": "50% discount applied for 3 months", "coupon_id": RETENTION_COUPON_ID}


def resolve_lite_price_id() -> str:
    explicit = token_billing.lite_price_id()
    if explicit:
        return explicit
    prices = stripe.Price.list(lookup_keys=[LITE_LOOKUP_KEY], active=True, limit=1)
    data = _get(prices, "data", [])
    if not data:
        raise HTTPException(status_code=503, detail="Lite plan is not configured")
    return _get(data[0], "id")


def downgrade_plan(db: Session, user: Any, sub: Any) -> dict[str, Any]:
    offer = compute_offer(db, user.stripe_id, sub)
    if offer["offer"] != "downgrade":
        raise HTTPException(status_code=409, detail=offer)
    price_id = resolve_lite_price_id()
    db.add(RetentionOffer(stripe_id=user.stripe_id, user_id=user.id, kind=KIND_DOWNGRADE))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={"offer": "none", "reason": "downgrade_already_used"})
    try:
        item = _items(sub)[0]
        stripe.Subscription.modify(
            _get(sub, "id"),
            items=[{"id": _get(item, "id"), "price": price_id}],
            proration_behavior="none",
        )
    except Exception as exc:
        logger.error("plan downgrade failed for %s: %s", user.stripe_id, exc)
        db.query(RetentionOffer).filter(
            RetentionOffer.stripe_id == user.stripe_id, RetentionOffer.kind == KIND_DOWNGRADE
        ).delete()
        db.commit()
        raise HTTPException(status_code=502, detail="Failed to change plan")
    token_billing._lite_cache.pop(user.stripe_id, None)
    return {"success": True, "message": "Switched to Lite", "price_id": price_id}


def cancel_subscription(db: Session, user: Any, sub: Any, reason: str, details: str, offer_shown: Optional[str]) -> dict[str, Any]:
    if reason not in CANCEL_REASONS:
        raise HTTPException(status_code=400, detail=f"reason must be one of {', '.join(CANCEL_REASONS)}")
    if sub is None:
        raise HTTPException(status_code=400, detail="No active subscription found")
    sub_id = _get(sub, "id")
    survey = (
        db.query(CancellationSurvey)
        .filter(CancellationSurvey.stripe_id == user.stripe_id, CancellationSurvey.subscription_id == sub_id, CancellationSurvey.cancel_at.is_(None))
        .first()
    )
    if survey is None:
        survey = CancellationSurvey(user_id=user.id, email=user.email, stripe_id=user.stripe_id, subscription_id=sub_id)
        db.add(survey)
    survey.reason = reason
    survey.details = (details or "").strip()[:2000]
    survey.offer_shown = offer_shown
    db.commit()
    try:
        updated = stripe.Subscription.modify(
            sub_id,
            cancel_at_period_end=True,
            metadata={"textgen_cancel_reason": reason},
        )
    except Exception as exc:
        logger.error("cancel at period end failed for %s: %s", user.stripe_id, exc)
        raise HTTPException(status_code=502, detail="Failed to cancel subscription")
    survey.cancel_at = _period_end(updated) or _period_end(sub) or datetime.utcnow()
    db.commit()
    try:
        from questions.subscription_utils import clear_subscription_cache

        clear_subscription_cache(user.email)
    except Exception:
        pass
    return {"success": True, "cancel_at": survey.cancel_at.isoformat(), "message": "Subscription will end at the end of the billing period"}


def _auth(request: Request, db: Session):
    from questions.auth import get_current_user

    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not user.stripe_id:
        raise HTTPException(status_code=400, detail="No subscription found")
    return user


@router.get("/api/cancel/offer")
def cancel_offer(request: Request, db: Session = Depends(get_db)):
    user = _auth(request, db)
    sub = find_active_subscription(user.stripe_id)
    out = compute_offer(db, user.stripe_id, sub)
    out["reasons"] = list(CANCEL_REASONS)
    return out


@router.post("/api/apply-retention-coupon")
def apply_retention_coupon(request: Request, db: Session = Depends(get_db)):
    user = _auth(request, db)
    return apply_coupon(db, user, find_active_subscription(user.stripe_id))


@router.post("/api/downgrade-plan")
def downgrade(request: Request, db: Session = Depends(get_db)):
    user = _auth(request, db)
    return downgrade_plan(db, user, find_active_subscription(user.stripe_id))


@router.post("/api/cancel-subscription")
def cancel(body: CancelRequest, request: Request, db: Session = Depends(get_db)):
    user = _auth(request, db)
    return cancel_subscription(
        db, user, find_active_subscription(user.stripe_id), body.reason, body.details, body.offer_shown
    )


def _ts(v: Any) -> Optional[datetime]:
    return datetime.utcfromtimestamp(int(v)) if v else None


def record_cancellation(db: Session, sub: Any, source: str, now: Optional[datetime] = None) -> Optional[CancellationSurvey]:
    from questions.db_models_postgres import User

    now = now or datetime.utcnow()
    sub_id = _get(sub, "id")
    customer = _get(sub, "customer")
    if not sub_id or not customer:
        return None
    items = _items(sub)
    if items and _get(_get(items[0], "price"), "id") in SELF_HOSTED_PRICE_IDS:
        return None
    details = _get(sub, "cancellation_details") or {}
    feedback = _get(details, "feedback")
    if source == "portal" and _get(details, "reason") == "payment_failed":
        source = "dunning"
    if _get(sub, "status") == "canceled":
        when = _ts(_get(sub, "ended_at")) or _ts(_get(sub, "canceled_at")) or now
    else:
        when = _ts(_get(sub, "cancel_at")) or _period_end(sub) or now
    row = db.query(CancellationSurvey).filter(CancellationSurvey.subscription_id == sub_id).first()
    if row is not None:
        changed = False
        if row.cancel_at is None or (_get(sub, "status") == "canceled" and row.cancel_at != when and row.source != "app"):
            row.cancel_at = when
            changed = True
        if feedback and row.reason in ("unknown", "other") and row.source != "app":
            row.reason = feedback
            changed = True
        if changed:
            db.commit()
        return row
    user = db.query(User).filter(User.stripe_id == customer).first()
    if user is None or not user.email:
        return None
    row = CancellationSurvey(
        user_id=user.id,
        email=user.email,
        stripe_id=customer,
        subscription_id=sub_id,
        reason=feedback or ("payment_failed" if source == "dunning" else "unknown"),
        details=_get(details, "comment"),
        cancel_at=when,
        source=source,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.query(CancellationSurvey).filter(CancellationSurvey.subscription_id == sub_id).first()
    return row


def _canceling(sub: Any) -> bool:
    return bool(_get(sub, "cancel_at_period_end") or _get(sub, "cancel_at") or _get(_get(sub, "cancellation_details") or {}, "reason"))


def handle_subscription_event(db: Session, event_type: str, obj: Any) -> bool:
    if event_type == "customer.subscription.updated":
        if _get(obj, "status") == "canceled" or _canceling(obj):
            return record_cancellation(db, obj, "portal") is not None
        return False
    if event_type == "customer.subscription.deleted":
        return record_cancellation(db, obj, "portal") is not None
    if event_type == "invoice.payment_failed":
        if _get(obj, "next_payment_attempt"):
            return False
        sub_id = _get(obj, "subscription") or _get(_get(_get(obj, "parent") or {}, "subscription_details") or {}, "subscription")
        if not sub_id:
            return False
        try:
            sub = stripe.Subscription.retrieve(sub_id)
        except Exception as exc:
            logger.warning("dunning sub lookup failed for %s: %s", sub_id, exc)
            sub = {"id": sub_id, "customer": _get(obj, "customer"), "status": "past_due"}
        return record_cancellation(db, sub, "dunning") is not None
    return False


def reconcile_cancellations(db: Session, days: int = 45, now: Optional[datetime] = None) -> int:
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=days)
    count = 0
    for status in ("canceled", "active", "past_due"):
        subs = stripe.Subscription.list(status=status, limit=100, created={"gte": int((now - timedelta(days=400)).timestamp())})
        for sub in subs.auto_paging_iter():
            if status == "canceled":
                when = _ts(_get(sub, "ended_at")) or _ts(_get(sub, "canceled_at"))
                if when is None or when < cutoff:
                    continue
            elif not _get(sub, "cancel_at_period_end"):
                continue
            if record_cancellation(db, sub, "portal", now) is not None:
                count += 1
    return count
