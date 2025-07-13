#!/usr/bin/env python3
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_basic():
    # Test that the app loads
    response = client.get("/")
    print(f"Root response: {response.status_code}")
    
    # Test checkout endpoint directly
    response = client.post("/create-checkout-session", data={})
    print(f"Checkout response: {response.status_code}")
    print(f"Checkout text: {response.text}")

if __name__ == "__main__":
    test_basic()