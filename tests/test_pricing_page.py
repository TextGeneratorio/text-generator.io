#!/usr/bin/env python3
"""
Tests for the pricing page (/subscribe) functionality.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestPricingPage:
    """Test class for pricing page functionality"""

    def test_subscribe_page_loads(self):
        """Test that the subscribe/pricing page loads successfully"""
        response = client.get("/subscribe")
        assert response.status_code == 200
        assert "Cloud Text Generator" in response.text
        assert "subscription-toggle" in response.text

    def test_subscribe_page_contains_toggle_elements(self):
        """Test that the pricing page contains the toggle elements"""
        response = client.get("/subscribe")
        assert response.status_code == 200

        # Check for toggle elements
        assert 'class="subscription-toggle"' in response.text
        assert 'class="money-amount"' in response.text
        assert 'class="subscription-period"' in response.text
        # Note: discount-chip is optional and may not always be present

        # Check for JavaScript functions
        assert "setupSubscriptionToggle" in response.text

    def test_subscribe_page_contains_form(self):
        """Test that the pricing page exposes the checkout entry point.

        The inline POST form was replaced by the checkout dialog
        (static/js/checkout-dialog.js -> /create-checkout-session-embedded).
        """
        response = client.get("/subscribe")
        assert response.status_code == 200

        assert 'id="checkout-button"' in response.text
        assert 'onclick="openCheckoutDialog()"' in response.text
        assert "checkout-dialog.js" in response.text

    def test_subscribe_page_default_values(self):
        """Test that the pricing page defaults to annual billing."""
        response = client.get("/subscribe")
        assert response.status_code == 200

        # Toggle is checked by default and drives the annual pricing display.
        assert 'class="subscription-toggle" checked' in response.text
        assert "USD" in response.text  # Should show some USD pricing
        assert "Annually" in response.text  # Default should show annual period

    def test_subscribe_page_pricing_structure(self):
        """Test that the pricing page shows the correct pricing structure"""
        response = client.get("/subscribe")
        assert response.status_code == 200

        # Check for pricing elements
        assert "Cloud Text Generator" in response.text
        assert "Self Host" in response.text
        assert "Enterprise" in response.text

        # Check for features
        assert "Quick Start" in response.text
        assert "Multi-lingual generation" in response.text
        assert "Code generation" in response.text
        assert "Complete data privacy" in response.text


if __name__ == "__main__":
    pytest.main([__file__])
