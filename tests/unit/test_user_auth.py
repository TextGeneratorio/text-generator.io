import os
import importlib
import types
import sys
from starlette.testclient import TestClient

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['BCRYPT_ROUNDS'] = '4'
os.environ['BCRYPT_PEPPER'] = 'pepper'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'local'
os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:1234'

db_models = importlib.import_module('questions.db_models')
importlib.reload(db_models)
from questions.sql_models import Base, engine

sys.modules['sellerinfo'] = types.SimpleNamespace(
    STRIPE_LIVE_SECRET='', STRIPE_LIVE_KEY='', CLAUDE_API_KEY=''
)

from main import app

import stripe
stripe.Customer.create = lambda **kwargs: types.SimpleNamespace(id="cus_test")

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_user_signup_and_login():
    resp = client.post('/login', data={'email': 'test@example.com', 'password': 'secret'}, follow_redirects=False)
    assert resp.status_code == 303
    resp = client.post('/login', data={'email': 'test@example.com', 'password': 'secret'}, follow_redirects=False)
    assert resp.status_code == 303
