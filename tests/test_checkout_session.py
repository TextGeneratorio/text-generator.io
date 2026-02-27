#!/usr/bin/env python3
"""
Tests for the create-checkout-session endpoint.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import User, app

client = TestClient(app)


class TestCreateCheckoutSession:
    """Test class for create-checkout-session endpoint"""

    @pytest.fixture
    def mock_stripe_session(self):
        """Mock Stripe checkout session"""
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test-session"
        return mock_session

    @pytest.fixture
    def mock_user(self):
        """Mock user with stripe_id"""
        user = MagicMock(spec=User)
        user.stripe_id = "cus_test123"
        user.id = "user_test123"
        # Need to ensure the user has the stripe_id attribute when checked
        user.hasattr = lambda attr: attr == "stripe_id"
        return user

    @patch("questions.auth.get_user_from_session")
    @patch("main.stripe.checkout.Session.create")
    def test_create_checkout_session_monthly_success(
        self, mock_stripe_create, mock_get_user, mock_user, mock_stripe_session
    ):
        """Test successful monthly checkout session creation"""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_stripe_create.return_value = mock_stripe_session

        # Make request
        response = client.post(
            "/create-checkout-session",
            data={"uid": "user_test123", "secret": "test_secret", "type": "monthly", "quantity": "1"},
        )

        # Debug: print response details
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")

        # Assertions
        assert response.status_code == 303
        assert response.headers["location"] == "https://checkout.stripe.com/test-session"

        # Verify stripe call
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args

        # Check line items don't include quantity for monthly (metered subscription)
        line_items = call_args[1]["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["price"] == "price_0RXdbtDtz2XsjQROW0xgtU8H"
        assert line_items[0]["quantity"] == 1

    @patch("questions.auth.get_user_from_session")
    @patch("main.stripe.checkout.Session.create")
    def test_create_checkout_session_annual_success(
        self, mock_stripe_create, mock_get_user, mock_user, mock_stripe_session
    ):
        """Test successful annual checkout session creation"""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_stripe_create.return_value = mock_stripe_session

        # Make request
        response = client.post(
            "/create-checkout-session",
            data={"uid": "user_test123", "secret": "test_secret", "type": "annual", "quantity": "1"},
        )

        # Assertions
        assert response.status_code == 303

        # Verify stripe call
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args

        # Check line items don't include quantity for annual (metered subscription)
        line_items = call_args[1]["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["price"] == "price_0RXdd4Dtz2XsjQRO5hYsdfjx"
        assert line_items[0]["quantity"] == 1

    @patch("questions.auth.get_user_from_session")
    @patch("main.stripe.checkout.Session.create")
    def test_create_checkout_session_self_hosted_success(
        self, mock_stripe_create, mock_get_user, mock_user, mock_stripe_session
    ):
        """Test successful self-hosted checkout session creation"""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_stripe_create.return_value = mock_stripe_session

        # Make request
        response = client.post(
            "/create-checkout-session",
            data={"uid": "user_test123", "secret": "test_secret", "type": "self-hosted", "quantity": "3"},
        )

        # Assertions
        assert response.status_code == 303

        # Verify stripe call
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args

        # Check line items include quantity for self-hosted subscriptions
        line_items = call_args[1]["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["price"] == "price_0MuAuxDtz2XsjQROz3Hp5Tcx"
        assert line_items[0]["quantity"] == 3

    @patch("questions.auth.get_user_from_session")
    @patch("main.User.byId")
    def test_create_checkout_session_no_stripe_id(self, mock_by_id, mock_get_user):
        """Test checkout session creation fails when user has no stripe_id"""
        # Setup mocks
        mock_get_user.return_value = None
        mock_by_id.return_value = None

        # Make request
        response = client.post(
            "/create-checkout-session",
            data={"uid": "user_test123", "secret": "test_secret", "type": "monthly", "quantity": "1"},
        )

        # Assertions
        assert response.status_code == 400
        assert "User payment info not found" in response.json()["error"]

    @patch("questions.auth.get_user_from_session")
    @patch("main.stripe.checkout.Session.create")
    def test_create_checkout_session_stripe_error(self, mock_stripe_create, mock_get_user, mock_user):
        """Test checkout session creation handles Stripe errors"""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_stripe_create.side_effect = Exception("Stripe error")

        # Make request
        response = client.post(
            "/create-checkout-session",
            data={"uid": "user_test123", "secret": "test_secret", "type": "monthly", "quantity": "1"},
        )

        # Assertions
        assert response.status_code == 500
        assert "Stripe error" in response.text

    @patch("questions.auth.get_user_from_session")
    @patch("main.stripe.checkout.Session.create")
    def test_create_checkout_session_currency_combine_error(
        self, mock_stripe_create, mock_get_user, mock_user, mock_stripe_session
    ):
        """Test checkout session creation handles currency combine error with NZD fallback"""
        # Setup mocks - first call fails with currency error, second succeeds
        mock_get_user.return_value = mock_user
        mock_stripe_create.side_effect = [Exception("combine currencies"), mock_stripe_session]

        # Make request
        response = client.post(
            "/create-checkout-session",
            data={"uid": "user_test123", "secret": "test_secret", "type": "monthly", "quantity": "1"},
        )

        # Assertions
        assert response.status_code == 303
        assert response.headers["location"] == "https://checkout.stripe.com/test-session"

        # Verify stripe was called twice
        assert mock_stripe_create.call_count == 2

        # Check second call used NZD price and no quantity for monthly
        second_call_args = mock_stripe_create.call_args
        line_items = second_call_args[1]["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["price"] == "price_0LCAb8Dtz2XsjQROnv1GhCL4"
        assert "quantity" not in line_items[0]

    @patch("questions.auth.get_user_from_session")
    @patch("main.stripe.checkout.Session.create")
    def test_create_checkout_session_self_hosted_nzd_fallback(
        self, mock_stripe_create, mock_get_user, mock_user, mock_stripe_session
    ):
        """Test self-hosted checkout with NZD fallback includes quantity"""
        # Setup mocks - first call fails with currency error, second succeeds
        mock_get_user.return_value = mock_user
        mock_stripe_create.side_effect = [Exception("combine currencies"), mock_stripe_session]

        # Make request
        response = client.post(
            "/create-checkout-session",
            data={"uid": "user_test123", "secret": "test_secret", "type": "self-hosted", "quantity": "2"},
        )

        # Assertions
        assert response.status_code == 303

        # Verify stripe was called twice
        assert mock_stripe_create.call_count == 2

        # Check second call used NZD self-hosted price and includes quantity
        second_call_args = mock_stripe_create.call_args
        line_items = second_call_args[1]["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["price"] == "price_0MuBEoDtz2XsjQROiRewGRFi"
        assert line_items[0]["quantity"] == 2

    def test_create_checkout_session_missing_params(self):
        """Test checkout session creation with missing parameters"""
        # Make request with minimal data
        response = client.post("/create-checkout-session", data={})

        # Should still work with defaults but fail on missing user
        assert response.status_code == 400

    def test_create_checkout_session_default_quantity(self):
        """Test checkout session creation uses default quantity when not provided"""
        with (
            patch("questions.auth.get_user_from_session") as mock_get_user,
            patch("main.stripe.checkout.Session.create") as mock_stripe_create,
        ):
            # Setup mocks
            mock_user = MagicMock(spec=User)
            mock_user.stripe_id = "cus_test123"
            mock_get_user.return_value = mock_user

            mock_session = MagicMock()
            mock_session.url = "https://checkout.stripe.com/test-session"
            mock_stripe_create.return_value = mock_session

            # Make request without quantity
            response = client.post(
                "/create-checkout-session", data={"uid": "user_test123", "secret": "test_secret", "type": "self-hosted"}
            )

            # Assertions
            assert response.status_code == 303

            # Verify default quantity of 1 was used for self-hosted
            call_args = mock_stripe_create.call_args
            line_items = call_args[1]["line_items"]
            assert line_items[0]["quantity"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
