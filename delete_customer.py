#!/usr/bin/env python3
"""
Customer Deletion Migration Script

This script deletes a customer from both PostgreSQL databases (dev and prod)
and from Stripe based on email address.

Usage:
    python delete_customer.py spam_admirer@protonmail.com

The script will:
1. Delete the customer from the development database (textgen)
2. Delete the customer from the production database (textgen_prod)
3. Delete the customer from Stripe
"""

import asyncio
import logging
import os
import sys

import stripe
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from questions.logging_config import setup_logging

# Import project modules
from questions.payments.payments import stripe_keys

# Setup logging
setup_logging(use_cloud=True)
logger = logging.getLogger(__name__)

# Database credentials
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_PORT = os.getenv("DB_PORT", "5432")


def create_database_session(db_name: str):
    """Create a database session for the specified database."""
    database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine


def delete_customer_from_database(email: str, db_name: str) -> bool:
    """Delete customer from the specified PostgreSQL database."""
    logger.info(f"Attempting to delete customer {email} from database {db_name}")

    try:
        session, engine = create_database_session(db_name)

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"✅ Connected to database {db_name}")

        # Use raw SQL to avoid SQLAlchemy ORM schema issues
        # First check if user exists
        result = session.execute(
            text("SELECT id, stripe_id FROM users WHERE email = :email"), {"email": email}
        ).fetchone()

        if not result:
            logger.warning(f"❌ User with email {email} not found in database {db_name}")
            return False

        user_id, stripe_id = result
        logger.info(f"Found user {email} with ID {user_id} and stripe_id {stripe_id} in {db_name}")

        # Delete related records first to avoid foreign key issues
        # Delete documents
        session.execute(text("DELETE FROM documents WHERE user_id = :user_id"), {"user_id": user_id})

        # Delete chat messages (if table exists)
        try:
            session.execute(text("DELETE FROM chat_messages WHERE user_id = :user_id"), {"user_id": user_id})
        except Exception:
            pass  # Table might not exist in older schema

        # Delete chat rooms (if table exists)
        try:
            session.execute(text("DELETE FROM chat_rooms WHERE user_id = :user_id"), {"user_id": user_id})
        except Exception:
            pass  # Table might not exist in older schema

        # Delete save games (if table exists)
        try:
            session.execute(text("DELETE FROM save_games WHERE user_id = :user_id"), {"user_id": user_id})
        except Exception:
            pass  # Table might not exist in older schema

        # Finally delete the user
        session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})

        session.commit()
        logger.info(f"✅ Successfully deleted user {email} from database {db_name}")
        return True

    except Exception as e:
        logger.error(f"❌ Error deleting customer from database {db_name}: {e}")
        if "session" in locals():
            session.rollback()
        return False
    finally:
        if "session" in locals():
            session.close()


async def delete_customer_from_stripe(email: str) -> bool:
    """Delete customer from Stripe."""
    logger.info(f"Attempting to delete customer {email} from Stripe")

    try:
        # Set Stripe API key
        stripe.api_key = stripe_keys["secret_key"]

        # Find customers by email
        customers = stripe.Customer.list(email=email)

        if not customers.data:
            logger.warning(f"❌ No Stripe customers found for email {email}")
            return False

        deleted_count = 0
        for customer in customers.data:
            if customer.email == email:
                logger.info(f"Deleting Stripe customer {customer.id} for email {email}")

                # Cancel all active subscriptions first
                subscriptions = stripe.Subscription.list(customer=customer.id)
                for subscription in subscriptions.data:
                    if subscription.status in ["active", "trialing", "past_due"]:
                        logger.info(f"Canceling subscription {subscription.id}")
                        stripe.Subscription.cancel(subscription.id)

                # Delete the customer
                stripe.Customer.delete(customer.id)
                deleted_count += 1
                logger.info(f"✅ Successfully deleted Stripe customer {customer.id}")

        if deleted_count > 0:
            logger.info(f"✅ Successfully deleted {deleted_count} Stripe customer(s) for email {email}")
            return True
        else:
            logger.warning(f"❌ No Stripe customers deleted for email {email}")
            return False

    except Exception as e:
        logger.error(f"❌ Error deleting customer from Stripe: {e}")
        return False


async def main():
    """Main function to orchestrate customer deletion."""
    if len(sys.argv) not in [2, 3]:
        print("Usage: python delete_customer.py <email> [--force]")
        print("Example: python delete_customer.py spam_admirer@protonmail.com --force")
        print("Use --force to skip confirmation prompt")
        sys.exit(1)

    email = sys.argv[1].strip()
    force = len(sys.argv) == 3 and sys.argv[2] == "--force"

    logger.info(f"🎯 Starting customer deletion process for email: {email}")

    if not email or "@" not in email:
        logger.error("❌ Invalid email address provided")
        sys.exit(1)

    # Confirm deletion (unless forced)
    if not force:
        print(f"⚠️  WARNING: This will permanently delete customer '{email}' from:")
        print("   - Development database (textgen)")
        print("   - Production database (textgen_prod)")
        print("   - Stripe")
        print("")
        try:
            confirm = input("Are you sure you want to proceed? (type 'DELETE' to confirm): ")
            if confirm != "DELETE":
                print("❌ Deletion cancelled.")
                sys.exit(0)
        except EOFError:
            print("❌ No input received. Use --force flag for non-interactive mode.")
            sys.exit(1)
    else:
        logger.info("🚀 Force mode enabled - skipping confirmation")

    results = {"dev_db": False, "prod_db": False, "stripe": False}

    # Delete from development database
    logger.info("🔧 Deleting from development database (textgen)")
    results["dev_db"] = delete_customer_from_database(email, "textgen")

    # Delete from production database
    logger.info("🎯 Deleting from production database (textgen_prod)")
    results["prod_db"] = delete_customer_from_database(email, "textgen_prod")

    # Delete from Stripe
    logger.info("💳 Deleting from Stripe")
    results["stripe"] = await delete_customer_from_stripe(email)

    # Summary
    print("\n" + "=" * 50)
    print("DELETION SUMMARY")
    print("=" * 50)
    print(f"Email: {email}")
    print(f"Development DB: {'✅ DELETED' if results['dev_db'] else '❌ FAILED/NOT FOUND'}")
    print(f"Production DB:  {'✅ DELETED' if results['prod_db'] else '❌ FAILED/NOT FOUND'}")
    print(f"Stripe:         {'✅ DELETED' if results['stripe'] else '❌ FAILED/NOT FOUND'}")

    if all(results.values()):
        print("\n🎉 Customer successfully deleted from all systems!")
        return 0
    elif any(results.values()):
        print("\n⚠️  Customer partially deleted. Check logs for details.")
        return 1
    else:
        print("\n❌ Customer deletion failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
