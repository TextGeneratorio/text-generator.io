import os
from pathlib import Path
import cachetools
import stripe
from cachetools import cached
import logging
import sellerinfo
from questions.logging_config import setup_logging

setup_logging(use_cloud=True)
logger = logging.getLogger(__name__)

debug = (
        os.environ.get("SERVER_SOFTWARE", "").startswith("Development")
        or os.environ.get("IS_DEVELOP", "") == 1
        or Path("models/debug.env").exists()
)
if debug:
    stripe_keys = {
        "secret_key": sellerinfo.STRIPE_LIVE_SECRET,
        "publishable_key": sellerinfo.STRIPE_LIVE_KEY,
    }
    GCLOUD_STATIC_BUCKET_URL = ""
else:
    stripe_keys = {
        "secret_key": sellerinfo.STRIPE_LIVE_SECRET,
        "publishable_key": sellerinfo.STRIPE_LIVE_KEY,
    }

stripe.api_key = stripe_keys["secret_key"]


# todo refactor to get all data in 1 call
# @cached(cachetools.TTLCache(maxsize=10000, ttl=60))
def get_subscription_item_id_for_user(stripe_id):
    subscriptions = get_subscription_data_for(stripe_id)
    for (i, subscription) in enumerate(subscriptions):
        if subscription["customer"] == stripe_id:
            if subscription["plan"].get("name") == "Text Generator - Self Hosted - Per Instance":
                pass
            else:
                subscription_item_id = subscription["items"].data[0]["id"]
                logger.info(subscription)
                # currently, there's only one other subscription
                return subscription_item_id


def get_subscription_item_id_for_user_email(email):
    if not email:
        logger.warning("No email provided to get_subscription_item_id_for_user_email")
        return None
    
    try:
        subscriptions = get_subscription_data_for_email(email)
        for (i, subscription) in enumerate(subscriptions):
            # if subscription["customer"] == stripe_id:
            subscription_item_id = subscription["items"].data[0]["id"]
            logger.info(subscription)
            # currently, there's only one other subscription
            return subscription_item_id
    except Exception as e:
        logger.error(f"Error getting subscription item ID for email {email}: {e}")
        return None

def create_subscription_for_user(stripe_id, price="price_0MWaBRDtz2XsjQRO51QQkAGs"):
    subscription = stripe.Subscription.create(
        customer=stripe_id,
        items=[
            {
                "price": price,
            },
        ],
        idempotency_key=stripe_id + price,
    )

    return subscription


def get_self_hosted_subscription_item_id_for_user(stripe_id):
    subscriptions = get_subscription_data_for(stripe_id)
    for (i, subscription) in enumerate(subscriptions):
        if subscription["customer"] == stripe_id:
            if subscription["plan"].get("name") == "Text Generator - Self Hosted - Per Instance":
                subscription_item_id = subscription["items"].data[0]["id"]
                logger.info(subscription)
                # currently, there's only one subscription
                return subscription_item_id
            else:
                pass


def get_self_hosted_subscription_count_for_user(stripe_id):
    if not stripe_id:
        logger.warning("No stripe_id provided to get_self_hosted_subscription_count_for_user")
        return 0
    
    try:
        subscriptions = get_subscription_data_for(stripe_id)
        count = 0
        for (i, subscription) in enumerate(subscriptions):
            if subscription["customer"] == stripe_id:
                if subscription["plan"].get("name") == "Text Generator - Self Hosted - Per Instance":
                    # check if active or not
                    if subscription["status"] == "active" or subscription["status"] == "trialing":
                        count += 1
                    else:
                        logger.info(f"subscription not active, or unknown status: {subscription['status']}")
                else:
                    pass
        return count
    except Exception as e:
        logger.error(f"Error getting self-hosted subscription count for stripe_id {stripe_id}: {e}")
        return 0


@cached(cachetools.TTLCache(maxsize=10000, ttl=60))  # 60 seconds
def get_subscription_data():
    subscriptions = []
    starting_after = None
    has_more = True

    while has_more:
        params = {
            "limit": 10000,
            "starting_after": starting_after,
        }
        response = stripe.Subscription.list(**params)
        subscriptions.extend(response["data"])
        has_more = response["has_more"]
        if has_more:
            starting_after = response["data"][-1]["id"]

    return subscriptions


@cached(cachetools.TTLCache(maxsize=10000, ttl=60))  # 60 seconds
def get_subscription_data_for(stripe_id=None):
    if not stripe_id:
        logger.warning("No stripe_id provided to get_subscription_data_for")
        return []
    
    try:
        starting_after = None
        params = {
            "limit": 100,
            "starting_after": starting_after,
            "customer": stripe_id
        }
        response = stripe.Subscription.list(**params)
        return response["data"]
    except Exception as e:
        logger.error(f"Error getting subscription data for stripe_id {stripe_id}: {e}")
        return []


@cached(cachetools.TTLCache(maxsize=10000, ttl=60))  # 60 seconds
def get_subscription_data_for_email(email):
    if not email:
        logger.warning("No email provided to get_subscription_data_for_email")
        return []
    
    try:
        # All customers with email
        customers = stripe.Customer.list(email=email)
        all_subscriptions = []
        for (i, customer) in enumerate(customers):
            if customer["email"] == email:
                stripe_id = customer["id"]
                subscriptions = get_subscription_data_for(stripe_id)
                if subscriptions:
                    all_subscriptions.append(subscriptions)
                if len(all_subscriptions) > 0:
                    return all_subscriptions[0]
        return []
    except Exception as e:
        logger.error(f"Error getting subscription data for email {email}: {e}")
        return []


def get_or_create_stripe_customer(email, user_id=None):
    """
    Get or create a Stripe customer for the given email.
    Returns the customer ID on success, None on failure.
    """
    if not email:
        logger.warning("No email provided to get_or_create_stripe_customer")
        return None
    
    try:
        # First try to find existing customer by email
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            customer = customers.data[0]
            logger.info(f"Found existing Stripe customer for {email}: {customer.id}")
            return customer.id
        
        # If no customer found, create a new one
        idempotency_key = user_id or email
        customer = stripe.Customer.create(
            email=email,
            idempotency_key=idempotency_key
        )
        logger.info(f"Created new Stripe customer for {email}: {customer.id}")
        return customer.id
    except Exception as e:
        logger.error(f"Error getting or creating Stripe customer for {email}: {e}")
        return None


def validate_stripe_customer(stripe_id, email=None):
    """
    Validate that a Stripe customer ID exists and is valid.
    If the customer ID is invalid (e.g., from different mode), try to find by email.
    Returns the valid customer ID if found, None otherwise.
    """
    if not stripe_id:
        return None
    
    try:
        customer = stripe.Customer.retrieve(stripe_id)
        if customer and customer.id and not customer.get('deleted', False):
            return customer.id
    except Exception as e:
        logger.error(f"Error validating Stripe customer {stripe_id}: {e}")
        # If validation fails and we have email, try to find existing customer by email
        if email:
            logger.info(f"Attempting to find existing Stripe customer by email: {email}")
            try:
                customers = stripe.Customer.list(email=email, limit=1)
                if customers.data:
                    customer = customers.data[0]
                    logger.info(f"Found existing Stripe customer for {email}: {customer.id}")
                    return customer.id
            except Exception as email_error:
                logger.error(f"Error finding Stripe customer by email {email}: {email_error}")
        
    return None
