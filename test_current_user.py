#!/usr/bin/env python3
"""
Test script to check the /api/current-user endpoint
"""

import requests


def test_current_user_endpoint():
    """Test the current user endpoint"""
    url = "http://0.0.0.0:8083/api/current-user"

    try:
        print(f"Testing endpoint: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print(f"Response body: {response.json()}")
        else:
            print(f"Response text: {response.text}")

    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
    except Exception as e:
        print(f"Other error: {e}")


def test_health_endpoint():
    """Test a simple health check"""
    url = "http://0.0.0.0:8083/"

    try:
        print(f"\nTesting health endpoint: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response length: {len(response.text)} chars")

    except Exception as e:
        print(f"Health check error: {e}")


if __name__ == "__main__":
    test_health_endpoint()
    test_current_user_endpoint()
