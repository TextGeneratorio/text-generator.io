"""
Integration tests for authentication flow with Stripe customer validation.
Tests the real-world scenarios where users experience Stripe customer ID issues during auth.
"""

import pytest
import os
import sys
import types
from unittest.mock import patch, MagicMock
import stripe
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import bcrypt

# Set up test environment
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['BCRYPT_ROUNDS'] = '4'
os.environ['BCRYPT_PEPPER'] = 'pepper'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'local'
os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:1234'

# Mock sellerinfo module
sys.modules['sellerinfo'] = types.SimpleNamespace(
    STRIPE_LIVE_SECRET='sk_test_mock', 
    STRIPE_LIVE_KEY='pk_test_mock', 
    CLAUDE_API_KEY='test_key'
)

from questions.db_models_postgres import Base, User
from main import app

# Create test engine
engine = create_engine(
    'sqlite:///:memory:',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)

Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

from main import get_db
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestAuthStripeIntegration:
    """Test cases for authentication with Stripe customer validation."""

    def setup_method(self):
        """Set up test data before each test."""
        self.test_email = "test@example.com"
        self.test_password = "testpassword123"
        self.invalid_stripe_id = "cus_SY8zaXVkrJ94Io"
        self.valid_stripe_id = "cus_valid123"
        
        # Clean up any existing test data
        self.teardown_method()

    def test_login_with_invalid_stripe_id_recreates_customer(self):
        """Test the exact scenario from the logs - user has invalid Stripe ID."""
        # Create user with invalid Stripe ID
        db = TestingSessionLocal()
        # Hash the password properly
        password_hash = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        user = User(
            id=f"test_user_{hash(self.test_email)}",  # Provide explicit ID
            email=self.test_email,
            password_hash=password_hash,
            stripe_id=self.invalid_stripe_id,
            secret="test_secret"
        )
        db.add(user)
        db.commit()
        user_id = user.id
        db.close()

        # Mock Stripe responses
        mock_error = stripe.error.InvalidRequestError(
            f"No such customer: '{self.invalid_stripe_id}'",
            param="id",
            code="resource_missing"
        )
        
        mock_new_customer = MagicMock()
        mock_new_customer.id = "cus_new123"
        
        with patch('stripe.Customer.retrieve', side_effect=mock_error), \
             patch('stripe.Customer.list', return_value=MagicMock(data=[])), \
             patch('stripe.Customer.create', return_value=mock_new_customer), \
             patch('questions.payments.payments.get_subscription_item_id_for_user_email', return_value=None):
            
            response = client.post('/api/login', data={
                'email': self.test_email,
                'password': self.test_password
            })
            
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
            assert response.status_code == 200  # Should be 200 for JSON response
            
            # Verify user's Stripe ID was updated
            db = TestingSessionLocal()
            updated_user = db.query(User).filter(User.id == user_id).first()
            assert updated_user.stripe_id == "cus_new123"
            db.close()

    def test_current_user_api_with_invalid_stripe_id(self):
        """Test the /api/current-user endpoint with invalid Stripe ID."""
        # Create user with invalid Stripe ID and login
        db = TestingSessionLocal()
        # Hash the password properly
        password_hash = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        user = User(
            id=f"test_user_{hash(self.test_email)}_api",  # Provide explicit ID
            email=self.test_email,
            password_hash=password_hash,
            stripe_id=self.invalid_stripe_id,
            secret="test_secret_api"
        )
        db.add(user)
        db.commit()
        db.close()

        # Mock login first
        mock_valid_customer = MagicMock()
        mock_valid_customer.id = self.valid_stripe_id
        mock_valid_customer.get.return_value = False
        
        with patch('stripe.Customer.retrieve', return_value=mock_valid_customer), \
             patch('questions.payments.payments.get_subscription_item_id_for_user_email', return_value=None):
            
            login_response = client.post('/api/login', data={
                'email': self.test_email,
                'password': self.test_password
            })
            assert login_response.status_code == 303

        # Now test current-user API with invalid Stripe ID
        mock_error = stripe.error.InvalidRequestError(
            f"No such customer: '{self.invalid_stripe_id}'",
            param="id",
            code="resource_missing"
        )
        
        mock_new_customer = MagicMock()
        mock_new_customer.id = "cus_created_from_api"
        
        with patch('stripe.Customer.retrieve', side_effect=mock_error), \
             patch('stripe.Customer.list', return_value=MagicMock(data=[])), \
             patch('stripe.Customer.create', return_value=mock_new_customer), \
             patch('questions.payments.payments.get_subscription_item_id_for_user_email', return_value=None), \
             patch('questions.payments.payments.get_self_hosted_subscription_count_for_user', return_value=0):
            
            response = client.get('/api/current-user')
            assert response.status_code == 200
            
            user_data = response.json()
            assert user_data['email'] == self.test_email

    def test_login_finds_existing_customer_by_email(self):
        """Test login when invalid Stripe ID but valid customer exists by email."""
        # Create user with invalid Stripe ID
        db = TestingSessionLocal()
        # Hash the password properly
        password_hash = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        user = User(
            id=f"test_user_{hash(self.test_email)}_email",  # Provide explicit ID
            email=self.test_email,
            password_hash=password_hash,
            stripe_id=self.invalid_stripe_id,
            secret="test_secret_email"
        )
        db.add(user)
        db.commit()
        user_id = user.id
        db.close()

        # Mock Stripe responses
        mock_error = stripe.error.InvalidRequestError(
            f"No such customer: '{self.invalid_stripe_id}'",
            param="id",
            code="resource_missing"
        )
        
        mock_existing_customer = MagicMock()
        mock_existing_customer.id = "cus_found_by_email"
        
        with patch('stripe.Customer.retrieve', side_effect=mock_error), \
             patch('stripe.Customer.list', return_value=MagicMock(data=[mock_existing_customer])), \
             patch('questions.payments.payments.get_subscription_item_id_for_user_email', return_value=None):
            
            response = client.post('/api/login', data={
                'email': self.test_email,
                'password': self.test_password
            })
            
            assert response.status_code == 303
            
            # Verify user's Stripe ID was updated to the found customer
            db = TestingSessionLocal()
            updated_user = db.query(User).filter(User.id == user_id).first()
            assert updated_user.stripe_id == "cus_found_by_email"
            db.close()

    def test_new_user_signup_creates_stripe_customer(self):
        """Test new user signup creates Stripe customer."""
        mock_new_customer = MagicMock()
        mock_new_customer.id = "cus_signup123"
        
        with patch('stripe.Customer.list', return_value=MagicMock(data=[])), \
             patch('stripe.Customer.create', return_value=mock_new_customer), \
             patch('questions.payments.payments.get_subscription_item_id_for_user_email', return_value=None):
            
            response = client.post('/api/login', data={
                'email': 'newuser@example.com',
                'password': 'newpassword123'
            })
            
            assert response.status_code == 200  # Should return 200 for JSON response
            
            # Verify user was created with Stripe ID
            db = TestingSessionLocal()
            user = db.query(User).filter(User.email == 'newuser@example.com').first()
            assert user is not None
            assert user.stripe_id == "cus_signup123"
            db.close()

    def test_stripe_customer_creation_failure_handling(self):
        """Test handling when Stripe customer creation fails."""
        # Mock Stripe creation failure
        mock_error = stripe.error.StripeError("API Error")
        
        with patch('stripe.Customer.list', return_value=MagicMock(data=[])), \
             patch('stripe.Customer.create', side_effect=mock_error):
            
            response = client.post('/api/login', data={
                'email': 'failuser@example.com',
                'password': 'failpassword123'
            })
            
            # Should still complete login even if Stripe fails
            assert response.status_code == 200  # Should return 200 for JSON response
            
            # Verify user was created but without Stripe ID
            db = TestingSessionLocal()
            user = db.query(User).filter(User.email == 'failuser@example.com').first()
            assert user is not None
            assert user.stripe_id is None
            db.close()

    def test_multiple_users_with_same_email_stripe_handling(self):
        """Test edge case with multiple Stripe customers for same email."""
        # Create user with invalid Stripe ID
        db = TestingSessionLocal()
        # Hash the password properly
        password_hash = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        user = User(
            id=f"test_user_{hash(self.test_email)}_multi",  # Provide explicit ID
            email=self.test_email,
            password_hash=password_hash,
            stripe_id=self.invalid_stripe_id,
            secret="test_secret_multi"
        )
        db.add(user)
        db.commit()
        user_id = user.id
        db.close()

        # Mock multiple customers with same email
        mock_error = stripe.error.InvalidRequestError(
            f"No such customer: '{self.invalid_stripe_id}'",
            param="id",
            code="resource_missing"
        )
        
        mock_customer1 = MagicMock()
        mock_customer1.id = "cus_first123"
        mock_customer2 = MagicMock()
        mock_customer2.id = "cus_second123"
        
        with patch('stripe.Customer.retrieve', side_effect=mock_error), \
             patch('stripe.Customer.list', return_value=MagicMock(data=[mock_customer1, mock_customer2])), \
             patch('questions.payments.payments.get_subscription_item_id_for_user_email', return_value=None):
            
            response = client.post('/api/login', data={
                'email': self.test_email,
                'password': self.test_password
            })
            
            assert response.status_code == 303
            
            # Should use the first customer found
            db = TestingSessionLocal()
            updated_user = db.query(User).filter(User.id == user_id).first()
            assert updated_user.stripe_id == "cus_first123"
            db.close()

    @pytest.mark.parametrize("stripe_error", [
        stripe.error.InvalidRequestError("Invalid request", None, None),
        stripe.error.AuthenticationError("Authentication failed"),
        stripe.error.RateLimitError("Rate limit exceeded"),
        stripe.error.APIConnectionError("Connection failed"),
    ])
    def test_various_stripe_errors_during_login(self, stripe_error):
        """Test login handles various Stripe errors gracefully."""
        # Create user with invalid Stripe ID
        db = TestingSessionLocal()
        # Hash the password properly
        password_hash = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')
        user = User(
            id=f"test_user_{hash(self.test_email)}_errors",  # Provide explicit ID
            email=self.test_email,
            password_hash=password_hash,
            stripe_id=self.invalid_stripe_id,
            secret="test_secret_errors"
        )
        db.add(user)
        db.commit()
        db.close()

        with patch('stripe.Customer.retrieve', side_effect=stripe_error), \
             patch('stripe.Customer.list', side_effect=stripe_error), \
             patch('questions.payments.payments.get_subscription_item_id_for_user_email', return_value=None):
            
            response = client.post('/api/login', data={
                'email': self.test_email,
                'password': self.test_password
            })
            
            # Should still complete login even with Stripe errors
            assert response.status_code == 303

    def teardown_method(self):
        """Clean up after each test."""
        db = TestingSessionLocal()
        db.query(User).delete()
        db.commit()
        db.close()