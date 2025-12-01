#!/usr/bin/env python3
"""
Test script to validate the subscribe page template content.
"""

# Read the template directly to check for all required elements
template_path = "/home/lee/code/20-questions2/templates/shared/subscribe.jinja2"

with open(template_path, "r") as f:
    content = f.read()

# Elements the test is looking for
required_elements = [
    'class="subscription-toggle"',
    'class="money-amount"',
    'class="subscription-period"',
    'class="discount-chip"',
    "setupSubscriptionToggle",
    '$(".subscription-toggle").change',
]

print("Testing template content for required elements:")
print("=" * 50)

all_found = True
for element in required_elements:
    found = element in content
    status = "✓" if found else "✗"
    print(f"{status} {element}")

    if not found:
        all_found = False
        # Show similar patterns
        if "class=" in element:
            class_name = element.split('"')[1]
            print(f"   Looking for class: {class_name}")
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if class_name in line:
                    print(f"   Found at line {i + 1}: {line.strip()}")
                    break
        elif "$" in element:
            print(f"   Looking for jQuery code similar to: {element}")
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "subscription-toggle" in line and "change" in line:
                    print(f"   Found at line {i + 1}: {line.strip()}")
                    break

print("=" * 50)
if all_found:
    print("✓ All required elements found in template!")
else:
    print("✗ Some elements are missing from template")

# Additional check - let's see if the discount-chip is actually there
print("\nDiscount chip validation:")
print("Looking for 'discount-chip' anywhere in template...")
if "discount-chip" in content:
    print("✓ discount-chip found in template")
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "discount-chip" in line:
            print(f"   Line {i + 1}: {line.strip()}")
else:
    print("✗ discount-chip not found in template")
