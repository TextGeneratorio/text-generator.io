#!/usr/bin/env python3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app, User

client = TestClient(app)

def test_checkout_mock():
    # Mock user
    mock_user = MagicMock(spec=User)
    mock_user.stripe_id = "cus_test123"
    mock_user.id = "user_test123"
    
    # Mock Stripe session
    mock_stripe_session = MagicMock()
    mock_stripe_session.url = "https://checkout.stripe.com/test-session"
    
    with patch('questions.auth.get_user_from_session') as mock_get_user, \
         patch('main.stripe.checkout.Session.create') as mock_stripe_create:
        
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_stripe_create.return_value = mock_stripe_session
        
        # Make request
        response = client.post("/create-checkout-session", data={
            "uid": "user_test123",
            "secret": "test_secret",
            "type": "monthly",
            "quantity": "1"
        })
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        print(f"Response headers: {dict(response.headers)}")

if __name__ == "__main__":
    test_checkout_mock()