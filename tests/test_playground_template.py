#!/usr/bin/env python3
"""
Test script to verify the playground template renders correctly
"""

import os
import sys

from fastapi.templating import Jinja2Templates

# Set up environment
os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/textgen"

# Add the parent directory to the path so we can import main
sys.path.insert(0, "/home/lee/code/20-questions2")

try:
    from main import get_base_template_vars

    # Create templates
    templates = Jinja2Templates(directory=".")

    # Mock request
    class MockRequest:
        def __init__(self):
            self.headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            self.path = "/playground"
            self.url = "http://localhost:8000/playground"

    request = MockRequest()
    base_vars = get_base_template_vars(request)

    print("✓ Template variables generated successfully")
    print(f"  fixtures: {base_vars.get('fixtures')}")
    print(f"  static_url: {base_vars.get('static_url')}")

    # Try to render the template
    try:
        response = templates.TemplateResponse(
            "templates/playground.jinja2",
            base_vars,
        )
        print("✓ Template rendered successfully")
        print("Template rendering is working correctly")
    except Exception as e:
        print(f"❌ Template rendering failed: {e}")
        import traceback

        traceback.print_exc()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
