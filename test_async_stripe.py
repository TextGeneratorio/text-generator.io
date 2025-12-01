#!/usr/bin/env python3
"""Test script for async Stripe functionality."""

import asyncio

from questions.payments.payments import (
    get_or_create_stripe_customer_async,
    get_self_hosted_subscription_count_for_user_async,
    get_subscription_item_id_for_user_email_async,
    validate_stripe_customer_async,
)


async def test_async_stripe():
    """Test the async Stripe functions."""
    test_email = "test@example.com"

    print(f"Testing async Stripe functionality with email: {test_email}")

    try:
        # Test customer creation/retrieval
        print("\n1. Testing customer creation/retrieval...")
        customer_id = await get_or_create_stripe_customer_async(test_email)
        print(f"Customer ID: {customer_id}")

        if customer_id:
            # Test customer validation
            print("\n2. Testing customer validation...")
            valid_id = await validate_stripe_customer_async(customer_id, test_email)
            print(f"Valid customer ID: {valid_id}")

            # Test subscription item ID retrieval
            print("\n3. Testing subscription item ID retrieval...")
            subscription_item_id = await get_subscription_item_id_for_user_email_async(test_email)
            print(f"Subscription item ID: {subscription_item_id}")

            # Test self-hosted subscription count
            print("\n4. Testing self-hosted subscription count...")
            count = await get_self_hosted_subscription_count_for_user_async(customer_id)
            print(f"Self-hosted subscription count: {count}")

        print("\n✅ All async Stripe tests completed successfully!")

    except Exception as e:
        print(f"❌ Error during async Stripe test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_async_stripe())
