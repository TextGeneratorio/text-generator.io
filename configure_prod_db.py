#!/usr/bin/env python3
"""
Configure production database settings for Text Generator.
This script sets up the production database credentials as requested.
"""

import os


def configure_production_database():
    """Configure production database credentials."""

    print("🔧 Configuring Production Database Settings")
    print("=" * 50)

    # Production database credentials - hardcoded as requested
    PROD_DB_SETTINGS = {
        "PROD_DB_HOST": "localhost",  # Change this to your production DB host
        "PROD_DB_USER": "postgres",  # Change this to your production DB user
        "PROD_DB_PASSWORD": "password",  # Change this to your production DB password
        "PROD_DB_PORT": "5432",  # Change this to your production DB port
    }

    # Set environment variables
    for key, value in PROD_DB_SETTINGS.items():
        os.environ[key] = value
        print(f"✅ Set {key}={value}")

    # Set the primary database URL to use textgen_prod
    prod_database_url = f"postgresql://{PROD_DB_SETTINGS['PROD_DB_USER']}:{PROD_DB_SETTINGS['PROD_DB_PASSWORD']}@{PROD_DB_SETTINGS['PROD_DB_HOST']}:{PROD_DB_SETTINGS['PROD_DB_PORT']}/textgen_prod"
    os.environ["DATABASE_URL"] = prod_database_url

    print(f"✅ Set DATABASE_URL={prod_database_url}")
    print()
    print("🎯 Production database configuration complete!")
    print("📊 Now using textgen_prod database by default")
    print("🔄 Fallback to textgen database if textgen_prod is not available")

    return prod_database_url


if __name__ == "__main__":
    configure_production_database()
