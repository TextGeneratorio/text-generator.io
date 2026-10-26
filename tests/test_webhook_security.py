from fastapi.testclient import TestClient

from main import app


def test_webhook_fails_closed_without_stripe_signing_secret(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

    response = TestClient(app).post("/webhook", json={})

    assert response.status_code == 503
    assert response.json()["detail"] == "Stripe webhook is not configured"


def test_webhook_tracks_completed_checkout_purchase(monkeypatch):
    import main

    sent = []
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(main, "USE_POSTGRES", False)
    monkeypatch.setattr(
        main.stripe.Webhook,
        "construct_event",
        lambda **_: {
            "id": "evt_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_1",
                    "status": "complete",
                    "payment_status": "paid",
                    "mode": "subscription",
                    "customer": "cus_1",
                    "amount_total": 1900,
                    "currency": "usd",
                    "metadata": {"plan": "monthly", "surface": "subscribe", "th_cid": "cid_1", "th_sid": "sid_1"},
                }
            },
        },
    )
    monkeypatch.setattr(main.th_analytics, "send_event_background", lambda *a, **k: sent.append((a, k)))
    app.dependency_overrides[main.get_db] = lambda: None
    try:
        response = TestClient(app).post("/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=x"})
    finally:
        app.dependency_overrides.pop(main.get_db, None)

    assert response.status_code == 200
    assert sent == [
        (
            ("purchase",),
            {
                "event_id": "cs_test_1",
                "client_id": "cid_1",
                "user_id": None,
                "session_id": "sid_1",
                "props": {
                    "plan": "monthly",
                    "revenue": 19.0,
                    "currency": "USD",
                    "transaction_id": "cs_test_1",
                    "surface": "subscribe",
                },
            },
        )
    ]
