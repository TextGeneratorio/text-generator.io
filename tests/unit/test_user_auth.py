import os
import sys
import types
from unittest.mock import patch

from sqlalchemy.exc import OperationalError
from starlette.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["BCRYPT_PEPPER"] = "pepper"
os.environ["GOOGLE_CLOUD_PROJECT"] = "local"
os.environ["DATASTORE_EMULATOR_HOST"] = "localhost:1234"

# Use the PostgreSQL models with SQLite for testing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from questions.db_models_postgres import Base, get_db

# Create test engine with proper SQLite configuration for testing
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

sys.modules["sellerinfo"] = types.SimpleNamespace(STRIPE_LIVE_SECRET="", STRIPE_LIVE_KEY="", CLAUDE_API_KEY="")

import stripe

from main import app

stripe.Customer.create = lambda **kwargs: types.SimpleNamespace(id="cus_test")

# Create test database tables
Base.metadata.create_all(bind=engine)

# Create test session maker
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency to use our test database
def override_get_db():
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_user_signup_and_login():
    resp = client.post("/api/login", data={"email": "test@example.com", "password": "secret"}, follow_redirects=False)
    assert resp.status_code == 200
    assert "Max-Age=315360000" in resp.headers["set-cookie"]
    resp = client.post("/api/login", data={"email": "test@example.com", "password": "secret"}, follow_redirects=False)
    assert resp.status_code == 200


def test_login_database_error_is_not_reported_as_bad_password():
    with patch(
        "main.login_or_create_user",
        side_effect=OperationalError("SELECT 1", {}, Exception("closed connection")),
    ):
        resp = client.post("/api/login", data={"email": "db-error@example.com", "password": "secret"})

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Login temporarily unavailable. Please try again."
