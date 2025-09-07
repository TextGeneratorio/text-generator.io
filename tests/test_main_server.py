#!/usr/bin/env python3
"""
Test script to verify the main server can start without errors.
"""

import os
import sys

# Set up environment
os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/textgen"

try:
    # Try to import the main module
    print("Testing main.py imports...")

    # Test basic imports
    from questions.db_models_postgres import User, get_db

    print("✓ Basic imports successful")

    # Test database connection
    print("Testing database connection...")
    db = next(get_db())
    user_count = db.query(User).count()
    print(f"✓ Database connection successful (found {user_count} users)")
    db.close()

    # Test main.py import
    print("Testing main.py import...")
    import main

    print("✓ main.py imported successfully")

    # Test FastAPI app
    print("Testing FastAPI app...")
    app = main.app
    print(f"✓ FastAPI app created: {app}")

    print("\n🎉 All tests passed! Main server should be able to start.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
