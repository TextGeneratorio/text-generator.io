"""
Integration tests for Stripe customer validation scenarios.
Tests the real-world scenarios where Stripe customer IDs become invalid.
"""

import pytest
import stripe
from unittest.mock import patch, MagicMock
import logging
from questions.payments.payments import (
    validate_stripe_customer, 
    get_or_create_stripe_customer
)


class TestStripeCustomerValidation:
    """Test cases for Stripe customer validation scenarios."""

    def test_validate_stripe_customer_valid_id(self):
        """Test validation with a valid Stripe customer ID."""
        # Mock a valid customer response
        mock_customer = MagicMock()
        mock_customer.id = "cus_valid123"
        mock_customer.get.return_value = False  # not deleted
        
        with patch('stripe.Customer.retrieve', return_value=mock_customer):
            result = validate_stripe_customer("cus_valid123")
            assert result == "cus_valid123"

    def test_validate_stripe_customer_invalid_id(self):
        """Test validation with an invalid Stripe customer ID - the main issue."""
        # Mock the exact error we're seeing in production
        mock_error = stripe.error.InvalidRequestError(
            "No such customer: 'cus_SY8zaXVkrJ94Io'",
            param="id",
            code="resource_missing"
        )
        
        with patch('stripe.Customer.retrieve', side_effect=mock_error):
            result = validate_stripe_customer("cus_SY8zaXVkrJ94Io")
            assert result is None

    def test_validate_stripe_customer_invalid_id_with_email_fallback(self):
        """Test validation with invalid ID but successful email fallback."""
        # Mock the error for invalid customer ID
        mock_error = stripe.error.InvalidRequestError(
            "No such customer: 'cus_SY8zaXVkrJ94Io'",
            param="id",
            code="resource_missing"
        )
        
        # Mock successful email lookup
        mock_customer = MagicMock()
        mock_customer.id = "cus_found_by_email"
        mock_customers = MagicMock()
        mock_customers.data = [mock_customer]
        
        with patch('stripe.Customer.retrieve', side_effect=mock_error), \
             patch('stripe.Customer.list', return_value=mock_customers):
            result = validate_stripe_customer("cus_SY8zaXVkrJ94Io", email="test@example.com")
            assert result == "cus_found_by_email"

    def test_validate_stripe_customer_invalid_id_email_fallback_fails(self):
        """Test validation where both ID and email fallback fail."""
        # Mock the error for invalid customer ID
        mock_error = stripe.error.InvalidRequestError(
            "No such customer: 'cus_SY8zaXVkrJ94Io'",
            param="id",
            code="resource_missing"
        )
        
        # Mock failed email lookup
        mock_customers = MagicMock()
        mock_customers.data = []
        
        with patch('stripe.Customer.retrieve', side_effect=mock_error), \
             patch('stripe.Customer.list', return_value=mock_customers):
            result = validate_stripe_customer("cus_SY8zaXVkrJ94Io", email="test@example.com")
            assert result is None

    def test_validate_stripe_customer_deleted_customer(self):
        """Test validation with a deleted customer."""
        mock_customer = MagicMock()
        mock_customer.id = "cus_deleted123"
        mock_customer.get.return_value = True  # deleted
        
        with patch('stripe.Customer.retrieve', return_value=mock_customer):
            result = validate_stripe_customer("cus_deleted123")
            assert result is None

    def test_validate_stripe_customer_empty_id(self):
        """Test validation with empty/None customer ID."""
        result = validate_stripe_customer(None)
        assert result is None
        
        result = validate_stripe_customer("")
        assert result is None

    def test_get_or_create_stripe_customer_existing(self):
        """Test getting existing customer by email."""
        mock_customer = MagicMock()
        mock_customer.id = "cus_existing123"
        mock_customers = MagicMock()
        mock_customers.data = [mock_customer]
        
        with patch('stripe.Customer.list', return_value=mock_customers):
            result = get_or_create_stripe_customer("test@example.com")
            assert result == "cus_existing123"

    def test_get_or_create_stripe_customer_create_new(self):
        """Test creating new customer when none exists."""
        # Mock no existing customers
        mock_customers = MagicMock()
        mock_customers.data = []
        
        # Mock successful creation
        mock_new_customer = MagicMock()
        mock_new_customer.id = "cus_new123"
        
        with patch('stripe.Customer.list', return_value=mock_customers), \
             patch('stripe.Customer.create', return_value=mock_new_customer):
            result = get_or_create_stripe_customer("test@example.com", user_id="user123")
            assert result == "cus_new123"

    def test_get_or_create_stripe_customer_create_fails(self):
        """Test when customer creation fails."""
        # Mock no existing customers
        mock_customers = MagicMock()
        mock_customers.data = []
        
        # Mock creation failure
        mock_error = stripe.error.StripeError("API Error")
        
        with patch('stripe.Customer.list', return_value=mock_customers), \
             patch('stripe.Customer.create', side_effect=mock_error):
            result = get_or_create_stripe_customer("test@example.com")
            assert result is None

    def test_get_or_create_stripe_customer_no_email(self):
        """Test with no email provided."""
        result = get_or_create_stripe_customer(None)
        assert result is None
        
        result = get_or_create_stripe_customer("")
        assert result is None

    @pytest.mark.parametrize("stripe_error", [
        stripe.error.InvalidRequestError("Invalid request", None, None),
        stripe.error.AuthenticationError("Authentication failed"),
        stripe.error.PermissionError("Permission denied"),
        stripe.error.RateLimitError("Rate limit exceeded"),
        stripe.error.APIConnectionError("Connection failed"),
        stripe.error.APIError("API error"),
    ])
    def test_validate_stripe_customer_various_errors(self, stripe_error):
        """Test validation with various Stripe errors."""
        with patch('stripe.Customer.retrieve', side_effect=stripe_error):
            result = validate_stripe_customer("cus_test123")
            assert result is None

    def test_mode_mismatch_scenario(self):
        """Test the common scenario where customer ID is from different Stripe mode."""
        # This simulates test mode ID being used in live mode or vice versa
        mock_error = stripe.error.InvalidRequestError(
            "No such customer: 'cus_SY8zaXVkrJ94Io'",
            param="id",
            code="resource_missing"
        )
        
        # Mock finding customer by email in correct mode
        mock_customer = MagicMock()
        mock_customer.id = "cus_correct_mode_123"
        mock_customers = MagicMock()
        mock_customers.data = [mock_customer]
        
        with patch('stripe.Customer.retrieve', side_effect=mock_error), \
             patch('stripe.Customer.list', return_value=mock_customers):
            result = validate_stripe_customer("cus_SY8zaXVkrJ94Io", email="user@example.com")
            assert result == "cus_correct_mode_123"

    def test_concurrent_validation_requests(self):
        """Test multiple concurrent validation requests for robustness."""
        import concurrent.futures
        
        mock_customer = MagicMock()
        mock_customer.id = "cus_concurrent123"
        mock_customer.get.return_value = False
        
        with patch('stripe.Customer.retrieve', return_value=mock_customer):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(validate_stripe_customer, "cus_concurrent123")
                    for _ in range(10)
                ]
                
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
                assert all(result == "cus_concurrent123" for result in results)