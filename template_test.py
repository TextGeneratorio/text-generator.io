#!/usr/bin/env python3
"""
Simple test to read the template directly.
"""

# Read the template file directly
template_path = "/home/lee/code/20-questions2/templates/shared/subscribe.jinja2"
with open(template_path, "r") as f:
    content = f.read()

# Check for the elements that the test is looking for
checks = ['class="subscription-toggle"', 'class="money-amount"', 'class="subscription-period"', 'class="discount-chip"']

print("Checking template file directly:")
for check in checks:
    found = check in content
    print(f"{check}: {found}")
    if found:
        # Show the line where it's found
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if check in line:
                print(f"  Line {i + 1}: {line.strip()}")
                break

print("\nChecking JavaScript functions:")
js_checks = ["setupSubscriptionToggle", '$(".subscription-toggle").change']

for check in js_checks:
    found = check in content
    print(f"{check}: {found}")
    if found:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if check in line:
                print(f"  Line {i + 1}: {line.strip()}")
                break
