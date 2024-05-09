import os
from pathlib import Path

import cachetools
import stripe
from cachetools import cached
from loguru import logger

import stripe

import sellerinfo

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
            if subscription["plan"]["name"] == "Text Generator - Self Hosted - Per Instance":
                pass
            else:
                subscription_item_id = subscription["items"].data[0]["id"]
                logger.info(subscription)
                # currently, there's only one other subscription
                return subscription_item_id


def get_subscription_item_id_for_user_email(email):
    subscriptions = get_subscription_data_for_email(email)
    for (i, subscription) in enumerate(subscriptions):
        # if subscription["customer"] == stripe_id:
        subscription_item_id = subscription["items"].data[0]["id"]
        logger.info(subscription)
        # currently, there's only one other subscription
        return subscription_item_id

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
            if subscription["plan"]["name"] == "Text Generator - Self Hosted - Per Instance":
                subscription_item_id = subscription["items"].data[0]["id"]
                logger.info(subscription)
                # currently, there's only one subscription
                return subscription_item_id
            else:
                pass


def get_self_hosted_subscription_count_for_user(stripe_id):
    subscriptions = get_subscription_data_for(stripe_id)
    count = 0
    for (i, subscription) in enumerate(subscriptions):
        if subscription["customer"] == stripe_id:
            if subscription["plan"]["name"] == "Text Generator - Self Hosted - Per Instance":
                # check if active or not
                if subscription["status"] == "active" or subscription["status"] == "trialing":
                    count += 1
                else:
                    logger.info(f"subscription not active, or unknown status: {subscription['status']}")
            else:
                pass
    return count


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
    starting_after = None

    params = {
        "limit": 100,
        "starting_after": starting_after,
        "customer": stripe_id
    }
    response = stripe.Subscription.list(**params)
    return response["data"]


@cached(cachetools.TTLCache(maxsize=10000, ttl=60))  # 60 seconds
def get_subscription_data_for_email(email):
    starting_after = None

    params = {
        "limit": 100,
        "starting_after": starting_after,
    }
    #all customers with email
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
    # response = stripe.Subscription.list(**params)
    # return response["data"]
