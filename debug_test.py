#!/usr/bin/env python3
"""
Debug script to check the subscribe page response.
"""

import sys

sys.path.insert(0, ".")

try:
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    response = client.get("/subscribe")

    print(f"Status: {response.status_code}")
    print(f"Content type: {response.headers.get('content-type')}")

    # Check for the specific elements the test is looking for
    checks = [
        'class="subscription-toggle"',
        'class="money-amount"',
        'class="subscription-period"',
        'class="discount-chip"',
    ]

    for check in checks:
        found = check in response.text
        print(f"{check}: {found}")
        if not found:
            print("  - Looking for alternative patterns...")
            # Try to find similar patterns
            class_name = check.split('"')[1]
            patterns = [
                f'class="{class_name}"',
                f"class='{class_name}'",
                f'class="{class_name} ',
                f"class='{class_name} ",
                f'class=" {class_name}"',
                f"class=' {class_name}",
                f'class=" {class_name} ',
                f"class=' {class_name} ",
            ]

            for pattern in patterns:
                if pattern in response.text:
                    print(f"    Found alternative: {pattern}")
                    break
            else:
                print(f"    No alternative patterns found for {class_name}")
                # Show lines containing the class name
                lines = response.text.split("\n")
                for i, line in enumerate(lines):
                    if class_name in line:
                        print(f"    Line {i}: {line.strip()}")

    print("\nTest functions:")
    print(f"setupSubscriptionToggle: {'setupSubscriptionToggle' in response.text}")
    print(f'$(".subscription-toggle").change: {'$(".subscription-toggle").change' in response.text}')

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
