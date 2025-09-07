#!/usr/bin/env python3
"""
Simple test to verify the subscribe page elements are present.
"""

import sys

sys.path.insert(0, ".")


# Mock the missing modules with dummy objects
class MockAuth:
    def get_user_from_session(self, secret):
        return None


class MockStripe:
    def create_checkout_session(self, **kwargs):
        return {"id": "test_session_id"}

    def create_customer(self, **kwargs):
        return {"id": "test_customer_id"}


# Mock the modules that might not be available
sys.modules["questions.auth"] = MockAuth()
sys.modules["stripe"] = MockStripe()

try:
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    response = client.get("/subscribe")

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        # Check for the specific elements the test is looking for
        checks = [
            ('class="subscription-toggle"', "subscription-toggle"),
            ('class="money-amount"', "money-amount"),
            ('class="subscription-period"', "subscription-period"),
            ('class="discount-chip"', "discount-chip"),
        ]

        all_passed = True
        for check, name in checks:
            found = check in response.text
            print(f"{name}: {'✓' if found else '✗'}")
            if not found:
                all_passed = False

        # Check for JavaScript functions
        js_checks = [
            ("setupSubscriptionToggle", "setupSubscriptionToggle function"),
            ('$(".subscription-toggle").change', "subscription toggle change handler"),
        ]

        for check, name in js_checks:
            found = check in response.text
            print(f"{name}: {'✓' if found else '✗'}")
            if not found:
                all_passed = False

        print(f"\nOverall test result: {'✓ PASS' if all_passed else '✗ FAIL'}")

        if not all_passed:
            print("\nDebug info:")
            print(f"Response length: {len(response.text)} chars")
            print(f"First 500 chars: {response.text[:500]}")

    else:
        print(f"Request failed with status: {response.status_code}")
        print(response.text)

except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages: pip install fastapi")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
