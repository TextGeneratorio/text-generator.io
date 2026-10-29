from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from questions import cancel_flow, token_billing, token_pricing as tp, winback
from questions.db_models_postgres import Base, CancellationSurvey, RetentionOffer, StripeCreditEvent, TokenUsage, User
from questions.inference_server import subscriber_verify as sv


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setenv("WINBACK_UNSUBSCRIBE_SECRET", "test-secret")


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    token_billing._tier_cache.clear()
    token_billing._lite_cache.clear()
    yield s
    s.close()


def test_every_lane_tier_clears_margin_floor():
    for model in ("gemma-roleplay-v2", "gpt-5.6-luna", "claude-haiku-5-5", "deepseek-v4-flash", "llama-3.1-8b-instant", "text-generator/auto-cheap"):
        for lane in (tp.lane_for(model), tp.LANE_LOCAL, tp.LANE_RUNPOD, tp.LANE_OPENROUTER):
            if lane in (tp.LANE_LOCAL, tp.LANE_RUNPOD) and tp.resolve_model(model):
                continue
            for tier, _, _ in tp.VOLUME_TIERS:
                assert tp.gross_margin(model, lane, tier) >= tp.MIN_GROSS_MARGIN - 1e-9, (model, lane, tier)


def test_openrouter_lane_floor_with_fee():
    model = tp.resolve_model("gpt-5.6-luna").id
    assert tp.gross_margin(model, tp.LANE_OPENROUTER, "volume") >= tp.MIN_GROSS_MARGIN


def test_local_lane_cheaper_than_runpod():
    li, lo = tp.GPU_LANE_LIST[tp.LANE_LOCAL]
    ri, ro = tp.GPU_LANE_LIST[tp.LANE_RUNPOD]
    assert li < ri and lo < ro


def test_tiers_and_overflow_policy():
    assert tp.tier_for_prepaid(0)[0] == "payg"
    assert tp.tier_for_prepaid(5_000)[0] == "builder"
    assert tp.tier_for_prepaid(99_999)[0] == "scale"
    assert tp.tier_for_prepaid(100_000) == ("volume", 0.08)
    assert tp.overflow_allowed("paid") and tp.overflow_allowed("sub")
    assert not tp.overflow_allowed("free") and not tp.overflow_allowed("background") and not tp.overflow_allowed(None)


def test_charge_is_per_token_not_per_call():
    micro = tp.charge_micro("local-model", tp.LANE_LOCAL, "payg", 1000, 1000)
    assert micro == pytest.approx((0.17 + 2.02) * 1000 * 100, abs=2)
    assert micro < tp.MICRO


def test_coupon_margin_boundary():
    net = tp.net_plan_revenue_cents(tp.PLAN_PRICE_CENTS, 0.5)
    assert tp.coupon_margin_negative(net + 1)
    assert not tp.coupon_margin_negative(net - 1)


def test_accrual_carries_sub_cent(db, monkeypatch):
    balances = {"cus_1": 100}
    import questions.credits as credits

    monkeypatch.setattr(credits, "get_stripe_credit_balance_cents", lambda s: balances[s])
    monkeypatch.setattr(credits, "set_stripe_credit_balance_cents", lambda s, v: balances.__setitem__(s, v) or v)
    user = SimpleNamespace(id="u1", stripe_id="cus_1", free_credits=0)
    for _ in range(10):
        token_billing.bill_usage(db, user, "local-model", None, subscribed=False, prompt_tokens=500, completion_tokens=300)
    rows = db.query(TokenUsage).all()
    assert len(rows) == 10
    total_charge = sum(r.billed_micro for r in rows)
    assert balances["cus_1"] == 100 - total_charge // tp.MICRO
    assert all(r.cost_micro > 0 and r.charge_micro > r.cost_micro for r in rows)


def test_subscriber_not_billed_within_allowance(db, monkeypatch):
    import questions.credits as credits

    monkeypatch.setattr(credits, "get_stripe_credit_balance_cents", lambda s: 50)
    monkeypatch.setattr(credits, "set_stripe_credit_balance_cents", lambda s, v: pytest.fail("billed"))
    user = SimpleNamespace(id="u2", stripe_id="cus_2", free_credits=0)
    out = token_billing.bill_usage(db, user, "local-model", None, subscribed=True, prompt_tokens=100000, completion_tokens=100000)
    assert out["charged_cents"] == 0
    assert db.query(TokenUsage).one().billed_micro == 0


def test_volume_tier_from_prepaid(db):
    db.add(StripeCreditEvent(event_id="e1", checkout_session_id="s1", stripe_id="cus_3", credits_cents=30_000))
    db.add(StripeCreditEvent(event_id="e2", checkout_session_id="s2", stripe_id="cus_3", credits_cents=1_000, created=datetime.utcnow() - timedelta(days=200)))
    db.commit()
    assert token_billing.volume_tier(db, "cus_3")[0] == "scale"


class FakeStripe:
    def __init__(self, sub):
        self.sub = sub
        self.modified = []
        self.Subscription = SimpleNamespace(list=lambda **kw: {"data": [self.sub]}, modify=self._modify)
        self.Customer = SimpleNamespace(retrieve=lambda i: {"metadata": {}}, modify=lambda i, **kw: None)
        self.Price = SimpleNamespace(list=lambda **kw: {"data": [{"id": "price_lite"}]})

    def _modify(self, sub_id, **kw):
        self.modified.append(kw)
        out = dict(self.sub)
        out.update({k: v for k, v in kw.items() if k == "cancel_at_period_end"})
        return out


def _sub(price=1900, cancel=False):
    return {
        "id": "sub_1",
        "status": "active",
        "cancel_at_period_end": cancel,
        "current_period_end": int((datetime.utcnow() + timedelta(days=10)).timestamp()),
        "items": {"data": [{"id": "si_1", "price": {"id": "price_x", "unit_amount": price, "recurring": {"interval": "month"}}}]},
    }


def _user():
    return SimpleNamespace(id="u9", email="a@b.co", stripe_id="cus_9")


def test_offer_coupon_for_light_user(db, monkeypatch):
    fs = FakeStripe(_sub())
    monkeypatch.setattr(cancel_flow, "stripe", fs)
    sub = cancel_flow.find_active_subscription("cus_9")
    assert cancel_flow.compute_offer(db, "cus_9", sub)["offer"] == "coupon"
    out = cancel_flow.apply_coupon(db, _user(), sub)
    assert out["success"] and fs.modified[0]["discounts"] == [{"coupon": "CHURN50_3M"}]
    with pytest.raises(HTTPException) as e:
        cancel_flow.apply_coupon(db, _user(), sub)
    assert e.value.status_code == 409


def test_heavy_user_gets_downgrade_not_coupon(db, monkeypatch):
    fs = FakeStripe(_sub())
    monkeypatch.setattr(cancel_flow, "stripe", fs)
    db.add(TokenUsage(stripe_id="cus_9", model="m", lane="local", tier="payg", cost_micro=int(1200 * tp.MICRO)))
    db.commit()
    sub = cancel_flow.find_active_subscription("cus_9")
    assert cancel_flow.compute_offer(db, "cus_9", sub)["offer"] == "downgrade"
    with pytest.raises(HTTPException):
        cancel_flow.apply_coupon(db, _user(), sub)
    assert not fs.modified
    out = cancel_flow.downgrade_plan(db, _user(), sub)
    assert out["success"] and fs.modified[0]["items"][0]["price"]
    assert db.query(RetentionOffer).filter_by(kind="downgrade").count() == 1
    assert cancel_flow.compute_offer(db, "cus_9", sub)["offer"] == "none"


def test_cancel_stores_survey_then_cancels(db, monkeypatch):
    fs = FakeStripe(_sub())
    monkeypatch.setattr(cancel_flow, "stripe", fs)
    sub = cancel_flow.find_active_subscription("cus_9")
    with pytest.raises(HTTPException) as e:
        cancel_flow.cancel_subscription(db, _user(), sub, "bogus", "", None)
    assert e.value.status_code == 400
    out = cancel_flow.cancel_subscription(db, _user(), sub, "too_expensive", "pricey", "coupon")
    assert out["success"]
    assert fs.modified[0]["cancel_at_period_end"] is True
    row = db.query(CancellationSurvey).one()
    assert row.reason == "too_expensive" and row.details == "pricey" and row.cancel_at is not None


def test_cancel_stripe_failure_keeps_survey(db, monkeypatch):
    fs = FakeStripe(_sub())
    fs.Subscription.modify = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x"))
    monkeypatch.setattr(cancel_flow, "stripe", fs)
    with pytest.raises(HTTPException) as e:
        cancel_flow.cancel_subscription(db, _user(), _sub(), "other", "", None)
    assert e.value.status_code == 502
    assert db.query(CancellationSurvey).one().cancel_at is None


def _canceled(db, days_ago):
    db.add(User(id="w1", email="w@x.co", secret="s", name="Wen"))
    db.add(CancellationSurvey(user_id="w1", email="w@x.co", stripe_id="cus_w", reason="other", cancel_at=datetime.utcnow() - timedelta(days=days_ago)))
    db.commit()


def test_winback_flag_default_off(monkeypatch):
    monkeypatch.delenv("TEXTGEN_WINBACK_ENABLED", raising=False)
    assert not winback.enabled()
    assert winback.start_scheduler() is False


def test_winback_dry_run_sends_nothing(db):
    _canceled(db, 3)
    sent = []
    stats = winback.run_winback(dry_run=True, db=db, send=lambda *a: sent.append(a), is_resubscribed=lambda u: False)
    assert stats["due"] == 1 and stats["sent"] == 0 and not sent


def test_winback_chain_schedule(db):
    _canceled(db, 31)
    sent = []
    now = datetime.utcnow()
    for step in range(6):
        winback.run_winback(dry_run=False, db=db, send=lambda *a: sent.append(a), is_resubscribed=lambda u: False, now=now + timedelta(days=step * 2))
    cfg = winback.load_config()["emails"]
    assert [d["delay_days"] for d in cfg] == [2, 7, 14, 21, 30]
    assert len(sent) == 5
    assert sent[0][1] == cfg[0]["subject"] and "Wen" in sent[0][2] and "{{" not in sent[0][2]


def test_winback_waits_for_schedule_and_stops_on_resubscribe(db):
    _canceled(db, 1)
    sent = []
    assert winback.run_winback(dry_run=False, db=db, send=lambda *a: sent.append(a), is_resubscribed=lambda u: False)["sent"] == 0
    _canceled_row = db.query(CancellationSurvey).one()
    _canceled_row.cancel_at = datetime.utcnow() - timedelta(days=5)
    db.commit()
    assert winback.run_winback(dry_run=False, db=db, send=lambda *a: sent.append(a), is_resubscribed=lambda u: True)["stopped"] == 1
    assert not sent


def test_winback_templates_complete():
    for entry in winback.load_config()["emails"]:
        html = (winback.EMAILS_DIR / entry["template"]).read_text()
        for ph in ("{{.Name}}", "{{.UnsubscribeURL}}", "{{.Email}}"):
            assert ph in html


def test_verifier_distinguishes_paid_and_sub(monkeypatch):
    monkeypatch.delenv("OMNISERVE_NATIVE_KEY_TIERS", raising=False)
    monkeypatch.setattr(sv, "_netwrck", lambda c: None)
    monkeypatch.setattr(sv, "_cutedsl", lambda c: None)
    sv._cache.clear()
    assert sv.verify_credential("p", lambda c: "paid")["tier"] == "paid"
    sv._cache.clear()
    assert sv.verify_credential("s", lambda c: "sub")["tier"] == "sub"
    sv._cache.clear()
    assert sv.verify_credential("t", lambda c: True)["tier"] == "sub"


def test_unsub_token_roundtrip_and_fail_closed(monkeypatch):
    t = winback.make_token("A@x.co")
    assert winback.verify_token(t) == "a@x.co"
    assert winback.verify_token(t[:-1] + ("0" if t[-1] != "0" else "1")) is None
    monkeypatch.delenv("WINBACK_UNSUBSCRIBE_SECRET")
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    assert winback.make_token("a@x.co") is None and winback.verify_token(t) is None


def test_optout_skips_and_footer_link(db):
    _canceled(db, 3)
    sent = []
    winback.run_winback(dry_run=False, db=db, send=lambda *a: sent.append(a), is_resubscribed=lambda u: False)
    assert "/api/winback/unsubscribe?token=" in sent[0][2] and sent[0][3].startswith("https://text-generator.io/api/winback/unsubscribe?token=")
    assert "reply stop" not in sent[0][2].lower()
    winback.record_optout(db, "W@x.co")
    winback.record_optout(db, "w@x.co")
    sent.clear()
    st = winback.run_winback(dry_run=False, db=db, send=lambda *a: sent.append(a), is_resubscribed=lambda u: False, now=datetime.utcnow() + timedelta(days=30))
    assert not sent and st["stopped"] == 1


def test_no_secret_sends_nothing(db, monkeypatch):
    monkeypatch.delenv("WINBACK_UNSUBSCRIBE_SECRET")
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    _canceled(db, 3)
    sent = []
    winback.run_winback(dry_run=False, db=db, send=lambda *a: sent.append(a), is_resubscribed=lambda u: False)
    assert not sent


def test_claim_concurrent_exactly_one(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/c.db", connect_args={"timeout": 30})
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine)
    import threading

    results, barrier = [], threading.Barrier(12)

    def work():
        s = maker()
        barrier.wait()
        results.append(winback.claim_send(s, "a@x.co", 0))
        s.close()

    ts = [threading.Thread(target=work) for _ in range(12)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert results.count("claimed") == 1


def test_claim_lease_retry_only_when_unsent(db):
    now = datetime.utcnow()
    assert winback.claim_send(db, "a@x.co", 1, now) == "claimed"
    assert winback.claim_send(db, "a@x.co", 1, now + timedelta(minutes=10)) == "busy"
    assert winback.claim_send(db, "a@x.co", 1, now + timedelta(minutes=31)) == "claimed"
    winback.mark_sent(db, "a@x.co", 1, now)
    assert winback.claim_send(db, "a@x.co", 1, now + timedelta(hours=2)) == "sent"


def test_scheduler_lock_exclusive(tmp_path, monkeypatch):
    monkeypatch.setattr(winback, "LOCK_FILE", str(tmp_path / "l"))
    with winback.scheduler_lock() as a:
        with winback.scheduler_lock() as b:
            assert a is True and b is False
    with winback.scheduler_lock() as c:
        assert c is True


def _stripe_sub(**kw):
    base = {"id": "sub_p", "customer": "cus_p", "status": "active", "cancel_at_period_end": True, "current_period_end": int((datetime.utcnow() + timedelta(days=5)).timestamp()), "items": {"data": []}}
    base.update(kw)
    return base


def test_portal_cancel_recorded_idempotent(db):
    db.add(User(id="p1", email="p@x.co", secret="s", stripe_id="cus_p"))
    db.commit()
    sub = _stripe_sub(cancellation_details={"feedback": "too_expensive", "reason": "cancellation_requested"})
    assert cancel_flow.handle_subscription_event(db, "customer.subscription.updated", sub)
    cancel_flow.handle_subscription_event(db, "customer.subscription.updated", sub)
    r = db.query(CancellationSurvey).one()
    assert (r.source, r.reason, r.cancel_at is not None) == ("portal", "too_expensive", True)
    cancel_flow.handle_subscription_event(db, "customer.subscription.deleted", _stripe_sub(status="canceled", canceled_at=int(datetime.utcnow().timestamp())))
    assert db.query(CancellationSurvey).count() == 1


def test_noncancel_update_ignored_and_dunning(db, monkeypatch):
    db.add(User(id="p1", email="p@x.co", secret="s", stripe_id="cus_p"))
    db.commit()
    assert not cancel_flow.handle_subscription_event(db, "customer.subscription.updated", _stripe_sub(cancel_at_period_end=False))
    assert db.query(CancellationSurvey).count() == 0
    assert not cancel_flow.handle_subscription_event(db, "invoice.payment_failed", {"subscription": "sub_p", "customer": "cus_p", "next_payment_attempt": 123})
    monkeypatch.setattr(cancel_flow.stripe.Subscription, "retrieve", lambda i: _stripe_sub(status="past_due", cancel_at_period_end=False))
    assert cancel_flow.handle_subscription_event(db, "invoice.payment_failed", {"subscription": "sub_p", "customer": "cus_p", "next_payment_attempt": None})
    assert db.query(CancellationSurvey).one().source == "dunning"


def test_app_cancel_not_overwritten_by_webhook(db):
    db.add(User(id="p1", email="p@x.co", secret="s", stripe_id="cus_p"))
    db.add(CancellationSurvey(user_id="p1", email="p@x.co", stripe_id="cus_p", subscription_id="sub_p", reason="quality", cancel_at=datetime.utcnow(), source="app"))
    db.commit()
    cancel_flow.handle_subscription_event(db, "customer.subscription.updated", _stripe_sub())
    r = db.query(CancellationSurvey).one()
    assert (r.source, r.reason) == ("app", "quality")


def test_reconcile(db, monkeypatch):
    db.add(User(id="p1", email="p@x.co", secret="s", stripe_id="cus_p"))
    db.commit()

    class L:
        def __init__(self, d):
            self.d = d

        def auto_paging_iter(self):
            return iter(self.d)

    now = int(datetime.utcnow().timestamp())
    data = {"canceled": [_stripe_sub(status="canceled", ended_at=now), _stripe_sub(id="sub_old", status="canceled", ended_at=now - 90 * 86400)], "active": [_stripe_sub(id="sub_a")], "past_due": []}
    monkeypatch.setattr(cancel_flow.stripe.Subscription, "list", lambda **k: L(data[k["status"]]))
    assert cancel_flow.reconcile_cancellations(db) == 2
    assert cancel_flow.reconcile_cancellations(db) == 2
    assert db.query(CancellationSurvey).count() == 2
