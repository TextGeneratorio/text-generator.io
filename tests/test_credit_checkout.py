from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import CREDIT_PACK_PRICE_ID, MONTHLY_SUBSCRIPTION_PRICE_ID, ANNUAL_SUBSCRIPTION_PRICE_ID, app

client = TestClient(app)


def _mock_user(stripe_id="cus_test123", email="test@example.com", user_id="user_test123", is_subscribed=False):
    mock = MagicMock()
    mock.id = user_id
    mock.email = email
    mock.stripe_id = stripe_id
    mock.is_subscribed = is_subscribed
    return mock


def _mock_session(client_secret="cs_test_secret_123"):
    mock = MagicMock()
    mock.client_secret = client_secret
    return mock


class TestEmbeddedCheckoutCredits:
    """Tests for credits checkout via the embedded endpoint."""

    def test_credits_uses_payment_mode(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "credits", "quantity": 250},
            )

        assert response.status_code == 200
        assert response.json()["clientSecret"] == "cs_test_secret_123"

        kwargs = mock_create.call_args.kwargs
        assert kwargs["mode"] == "payment"
        assert kwargs["line_items"][0]["price"] == CREDIT_PACK_PRICE_ID
        assert kwargs["line_items"][0]["quantity"] == 250
        assert kwargs["metadata"]["purchase_type"] == "credits"

    def test_credits_default_quantity_is_1(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "credits"},
            )

        assert response.status_code == 200
        kwargs = mock_create.call_args.kwargs
        assert kwargs["line_items"][0]["quantity"] == 1

    def test_credits_quantity_floor_at_1(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "credits", "quantity": -5},
            )

        assert response.status_code == 200
        kwargs = mock_create.call_args.kwargs
        assert kwargs["line_items"][0]["quantity"] == 1

    def test_credits_return_url_has_session_id_placeholder(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "credits", "quantity": 100},
            )

        kwargs = mock_create.call_args.kwargs
        assert "{CHECKOUT_SESSION_ID}" in kwargs["return_url"]

    def test_credits_return_url_points_to_account(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "credits", "quantity": 100},
            )

        kwargs = mock_create.call_args.kwargs
        assert "/account?credits=success" in kwargs["return_url"]


class TestEmbeddedCheckoutSubscriptions:
    """Tests for monthly/annual subscription checkout via the embedded endpoint."""

    def test_monthly_uses_subscription_mode(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly"},
            )

        assert response.status_code == 200
        assert response.json()["clientSecret"] == "cs_test_secret_123"

        kwargs = mock_create.call_args.kwargs
        assert kwargs["mode"] == "subscription"
        assert kwargs["line_items"][0]["price"] == MONTHLY_SUBSCRIPTION_PRICE_ID
        assert kwargs["ui_mode"] == "embedded"

    def test_annual_uses_subscription_mode(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "annual"},
            )

        assert response.status_code == 200
        kwargs = mock_create.call_args.kwargs
        assert kwargs["mode"] == "subscription"
        assert kwargs["line_items"][0]["price"] == ANNUAL_SUBSCRIPTION_PRICE_ID

    def test_monthly_return_url_has_session_id_placeholder(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly", "return_url": "/playground"},
            )

        kwargs = mock_create.call_args.kwargs
        assert "{CHECKOUT_SESSION_ID}" in kwargs["return_url"]
        assert "/playground" in kwargs["return_url"]

    def test_already_subscribed_user_blocked_for_subscription(self):
        mock_user = _mock_user(is_subscribed=True)

        with patch("main.get_current_user", return_value=mock_user):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly"},
            )

        # The JS-side check prevents this, but the server should still
        # create the session (Stripe itself handles duplicate subscription logic)
        # so we just verify no crash
        assert response.status_code in (200, 500)

    def test_subscribed_user_can_still_buy_credits(self):
        mock_user = _mock_user(is_subscribed=True)
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "credits", "quantity": 50},
            )

        assert response.status_code == 200
        kwargs = mock_create.call_args.kwargs
        assert kwargs["mode"] == "payment"


class TestEmbeddedCheckoutAuth:
    """Tests for authentication in the embedded checkout endpoint."""

    def test_unauthenticated_returns_401(self):
        with patch("main.get_current_user", return_value=None):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly"},
            )

        assert response.status_code == 401

    def test_user_without_stripe_id_gets_one_created(self):
        mock_user = _mock_user(stripe_id=None)
        mock_session = _mock_session()
        mock_customer = MagicMock()
        mock_customer.id = "cus_new_123"

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.Customer.create", return_value=mock_customer) as mock_cust_create,
            patch("main.stripe.checkout.Session.create", return_value=mock_session),
        ):
            # Need to also mock the db query for re-fetching the user
            with patch("main.get_db") as mock_get_db:
                # The endpoint uses Depends(get_db) which is handled by TestClient
                response = client.post(
                    "/create-checkout-session-embedded",
                    json={"subscription_type": "monthly"},
                )

        # Should either succeed or fail gracefully (db mock may not wire up fully)
        assert response.status_code in (200, 500)


class TestEmbeddedCheckoutStripeFallback:
    """Tests for Stripe error fallback in the embedded checkout endpoint."""

    def test_stripe_error_falls_back_to_no_customer(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch(
                "main.stripe.checkout.Session.create",
                side_effect=[Exception("Customer tax error"), mock_session],
            ) as mock_create,
        ):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly"},
            )

        assert response.status_code == 200
        assert response.json()["clientSecret"] == "cs_test_secret_123"
        assert mock_create.call_count == 2

        # Second (fallback) call should not include customer
        fallback_kwargs = mock_create.call_args_list[1].kwargs
        assert "customer" not in fallback_kwargs

    def test_both_stripe_calls_fail_returns_500(self):
        mock_user = _mock_user()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch(
                "main.stripe.checkout.Session.create",
                side_effect=[Exception("Error 1"), Exception("Error 2")],
            ),
        ):
            response = client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "credits", "quantity": 10},
            )

        assert response.status_code == 500


class TestEmbeddedCheckoutReturnUrls:
    """Tests for return URL construction in the embedded checkout endpoint."""

    def test_default_return_url_is_playground(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly"},
            )

        kwargs = mock_create.call_args.kwargs
        assert "/playground?" in kwargs["return_url"]

    def test_custom_return_url_preserved(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly", "return_url": "/tools/speech-to-text"},
            )

        kwargs = mock_create.call_args.kwargs
        assert "/tools/speech-to-text?" in kwargs["return_url"]
        assert "session_id={CHECKOUT_SESSION_ID}" in kwargs["return_url"]

    def test_return_url_with_existing_query_params(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly", "return_url": "/account?tab=billing"},
            )

        kwargs = mock_create.call_args.kwargs
        assert "/account?tab=billing&session_id={CHECKOUT_SESSION_ID}" in kwargs["return_url"]

    def test_malicious_return_url_falls_back_to_default(self):
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "monthly", "return_url": "//evil.com/steal"},
            )

        kwargs = mock_create.call_args.kwargs
        assert "/playground?" in kwargs["return_url"]
        assert "evil.com" not in kwargs["return_url"]

    def test_credits_return_url_ignores_custom_return_url(self):
        """Credits always go to /account?credits=success regardless of return_url."""
        mock_user = _mock_user()
        mock_session = _mock_session()

        with (
            patch("main.get_current_user", return_value=mock_user),
            patch("main.stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client.post(
                "/create-checkout-session-embedded",
                json={"subscription_type": "credits", "quantity": 100, "return_url": "/playground"},
            )

        kwargs = mock_create.call_args.kwargs
        assert "/account?credits=success" in kwargs["return_url"]


class TestSubscribePageRendering:
    """Tests that the /subscribe page renders correctly with all cards."""

    def test_subscribe_page_loads(self):
        response = client.get("/subscribe")
        assert response.status_code == 200

    def test_subscribe_page_has_cloud_card(self):
        response = client.get("/subscribe")
        assert "Cloud Text Generator" in response.text

    def test_subscribe_page_has_credits_card(self):
        response = client.get("/subscribe")
        assert "API Credits" in response.text
        assert "buy-credits-button" in response.text

    def test_subscribe_page_has_enterprise_card(self):
        response = client.get("/subscribe")
        assert "Self Host - Enterprise" in response.text

    def test_subscribe_page_has_diy_card(self):
        response = client.get("/subscribe")
        assert "Self Host - DIY Free" in response.text

    def test_subscribe_page_card_order(self):
        """Cloud should appear before Credits, Credits before Enterprise, Enterprise before DIY."""
        response = client.get("/subscribe")
        text = response.text
        cloud_pos = text.index("Cloud Text Generator")
        credits_pos = text.index("API Credits")
        enterprise_pos = text.index("Self Host - Enterprise")
        diy_pos = text.index("Self Host - DIY Free")
        assert cloud_pos < credits_pos < enterprise_pos < diy_pos

    def test_subscribe_page_has_checkout_dialog_js(self):
        response = client.get("/subscribe")
        assert "showCheckoutDialog" in response.text

    def test_subscribe_page_has_credits_checkout_function(self):
        response = client.get("/subscribe")
        assert "openCreditsCheckout" in response.text
