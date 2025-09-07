import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import cachetools
import stripe
from cachetools import cached
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

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


class AsyncStripeClient:
    """Async Stripe client with robust error handling and retry logic."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        self.base_url = "https://api.stripe.com/v1"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def _make_request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make an async HTTP request to Stripe API with retry logic."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        url = f"{self.base_url}/{endpoint}"
        request_id = f"{method}:{endpoint}"

        logger.info(f"Starting Stripe API request: {request_id}")
        logger.debug(f"Stripe API request details - URL: {url}, Method: {method}, Data: {data}")

        start_time = asyncio.get_event_loop().time()

        try:
            if method.upper() == "GET":
                logger.debug(f"Making GET request to Stripe: {endpoint}")
                async with self.session.get(url, params=data) as response:
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    logger.info(f"Stripe API GET response: {response.status} in {elapsed_time:.2f}s for {endpoint}")

                    if response.status == 200:
                        response_data = await response.json()
                        logger.debug(f"Stripe API GET success: {endpoint} returned {len(str(response_data))} chars")
                        return response_data
                    else:
                        error_text = await response.text()
                        logger.error(f"Stripe API GET error: {response.status} - {error_text} for {endpoint}")
                        return None
            elif method.upper() == "POST":
                logger.debug(f"Making POST request to Stripe: {endpoint}")
                async with self.session.post(url, data=data) as response:
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    logger.info(f"Stripe API POST response: {response.status} in {elapsed_time:.2f}s for {endpoint}")

                    if response.status == 200:
                        response_data = await response.json()
                        logger.debug(f"Stripe API POST success: {endpoint} returned {len(str(response_data))} chars")
                        return response_data
                    else:
                        error_text = await response.text()
                        logger.error(f"Stripe API POST error: {response.status} - {error_text} for {endpoint}")
                        return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Network error calling Stripe API {endpoint} after {elapsed_time:.2f}s: {e}")
            raise
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Unexpected error calling Stripe API {endpoint} after {elapsed_time:.2f}s: {e}")
            return None

    async def list_customers(self, email: str = None, limit: int = 100) -> Optional[dict]:
        """List customers with optional email filter."""
        params = {"limit": limit}
        if email:
            params["email"] = email
        return await self._make_request("GET", "customers", params)

    async def create_customer(self, email: str, idempotency_key: str = None) -> Optional[dict]:
        """Create a new customer."""
        data = {"email": email}
        if idempotency_key:
            data["idempotency_key"] = idempotency_key
        return await self._make_request("POST", "customers", data)

    async def retrieve_customer(self, customer_id: str) -> Optional[dict]:
        """Retrieve a customer by ID."""
        return await self._make_request("GET", f"customers/{customer_id}")

    async def list_subscriptions(self, customer: str = None, limit: int = 100) -> Optional[dict]:
        """List subscriptions with optional customer filter."""
        params = {"limit": limit}
        if customer:
            params["customer"] = customer
        return await self._make_request("GET", "subscriptions", params)

    async def create_subscription(self, customer: str, price: str, idempotency_key: str = None) -> Optional[dict]:
        """Create a new subscription."""
        data = {"customer": customer, "items[0][price]": price}
        if idempotency_key:
            data["idempotency_key"] = idempotency_key
        return await self._make_request("POST", "subscriptions", data)


# Global async client instance
_async_stripe_client = None


async def get_async_stripe_client():
    """Get or create the global async Stripe client."""
    global _async_stripe_client
    if _async_stripe_client is None:
        _async_stripe_client = AsyncStripeClient(stripe_keys["secret_key"])
    return _async_stripe_client


# todo refactor to get all data in 1 call
# @cached(cachetools.TTLCache(maxsize=10000, ttl=60))
def get_subscription_item_id_for_user(stripe_id):
    subscriptions = get_subscription_data_for(stripe_id)
    for i, subscription in enumerate(subscriptions):
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
        for i, subscription in enumerate(subscriptions):
            # if subscription["customer"] == stripe_id:
            subscription_item_id = subscription["items"].data[0]["id"]
            logger.info(subscription)
            # currently, there's only one other subscription
            return subscription_item_id
    except Exception as e:
        logger.error(f"Error getting subscription item ID for email {email}: {e}")
        return None


def create_subscription_for_user(stripe_id, price="price_0MWaBRDtz2XsjQRO51QQkAGs"):
    logger.info(f"Creating subscription for stripe_id: {stripe_id}, price: {price}")

    try:
        subscription = stripe.Subscription.create(
            customer=stripe_id,
            items=[
                {
                    "price": price,
                },
            ],
            idempotency_key=stripe_id + price,
        )
        logger.info(f"Successfully created subscription {subscription.id} for customer {stripe_id}")
        return subscription
    except Exception as e:
        logger.error(f"Failed to create subscription for stripe_id {stripe_id}: {e}")
        raise


def get_self_hosted_subscription_item_id_for_user(stripe_id):
    subscriptions = get_subscription_data_for(stripe_id)
    for i, subscription in enumerate(subscriptions):
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
        for i, subscription in enumerate(subscriptions):
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
    logger.info("Fetching all subscription data from Stripe")
    subscriptions = []
    starting_after = None
    has_more = True
    page_count = 0

    try:
        while has_more:
            page_count += 1
            params = {
                "limit": 10000,
                "starting_after": starting_after,
            }
            logger.debug(f"Fetching subscription page {page_count}, starting_after: {starting_after}")
            response = stripe.Subscription.list(**params)
            subscriptions.extend(response["data"])
            has_more = response["has_more"]
            if has_more:
                starting_after = response["data"][-1]["id"]

        logger.info(f"Successfully fetched {len(subscriptions)} subscriptions across {page_count} pages")
        return subscriptions
    except Exception as e:
        logger.error(f"Error fetching subscription data on page {page_count}: {e}")
        return subscriptions  # Return what we have so far


@cached(cachetools.TTLCache(maxsize=10000, ttl=60))  # 60 seconds
def get_subscription_data_for(stripe_id=None):
    if not stripe_id:
        logger.warning("No stripe_id provided to get_subscription_data_for")
        return []

    logger.debug(f"Fetching subscription data for customer: {stripe_id}")
    try:
        starting_after = None
        params = {"limit": 100, "starting_after": starting_after, "customer": stripe_id}
        response = stripe.Subscription.list(**params)
        logger.debug(f"Found {len(response['data'])} subscriptions for customer {stripe_id}")
        return response["data"]
    except Exception as e:
        logger.error(f"Error getting subscription data for stripe_id {stripe_id}: {e}")
        return []


@cached(cachetools.TTLCache(maxsize=10000, ttl=60))  # 60 seconds
def get_subscription_data_for_email(email):
    if not email:
        logger.warning("No email provided to get_subscription_data_for_email")
        return []

    logger.debug(f"Fetching subscription data for email: {email}")
    try:
        # All customers with email
        logger.debug(f"Looking up Stripe customers for email: {email}")
        customers = stripe.Customer.list(email=email)
        logger.debug(f"Found {len(customers.data)} customers for email {email}")

        all_subscriptions = []
        for i, customer in enumerate(customers):
            if customer["email"] == email:
                stripe_id = customer["id"]
                logger.debug(f"Fetching subscriptions for customer {stripe_id} (email: {email})")
                subscriptions = get_subscription_data_for(stripe_id)
                if subscriptions:
                    all_subscriptions.append(subscriptions)
                if len(all_subscriptions) > 0:
                    logger.debug(f"Returning {len(all_subscriptions[0])} subscriptions for email {email}")
                    return all_subscriptions[0]

        logger.debug(f"No subscriptions found for email {email}")
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

    logger.info(f"Getting or creating Stripe customer for email: {email}")
    try:
        # First try to find existing customer by email
        logger.debug(f"Searching for existing Stripe customer with email: {email}")
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            customer = customers.data[0]
            logger.info(f"Found existing Stripe customer for {email}: {customer.id}")
            return customer.id

        # If no customer found, create a new one
        idempotency_key = user_id or email
        logger.info(f"Creating new Stripe customer for {email} with idempotency_key: {idempotency_key}")
        customer = stripe.Customer.create(email=email, idempotency_key=idempotency_key)
        logger.info(f"Successfully created new Stripe customer for {email}: {customer.id}")
        return customer.id
    except Exception as e:
        logger.error(f"Error getting or creating Stripe customer for {email}: {e}")
        return None


async def get_or_create_stripe_customer_async(email: str, user_id: str = None) -> Optional[str]:
    """
    Async version: Get or create a Stripe customer for the given email.
    Returns the customer ID on success, None on failure.
    """
    if not email:
        logger.warning("No email provided to get_or_create_stripe_customer_async")
        return None

    try:
        async with AsyncStripeClient(stripe_keys["secret_key"]) as client:
            # First try to find existing customer by email
            customers_response = await client.list_customers(email=email, limit=1)
            if customers_response and customers_response.get("data"):
                customer = customers_response["data"][0]
                logger.info(f"Found existing Stripe customer for {email}: {customer['id']}")
                return customer["id"]

            # If no customer found, create a new one
            idempotency_key = user_id or email
            customer = await client.create_customer(email=email, idempotency_key=idempotency_key)
            if customer:
                logger.info(f"Created new Stripe customer for {email}: {customer['id']}")
                return customer["id"]

            return None
    except Exception as e:
        logger.error(f"Error getting or creating Stripe customer for {email}: {e}")
        return None


async def get_subscription_data_for_async(stripe_id: str = None) -> List[Dict[str, Any]]:
    """
    Async version: Get subscription data for a specific Stripe customer.
    Returns list of subscriptions on success, empty list on failure.
    """
    if not stripe_id:
        logger.warning("No stripe_id provided to get_subscription_data_for_async")
        return []

    try:
        async with AsyncStripeClient(stripe_keys["secret_key"]) as client:
            response = await client.list_subscriptions(customer=stripe_id, limit=100)
            if response and response.get("data"):
                return response["data"]
            return []
    except Exception as e:
        logger.error(f"Error getting subscription data for stripe_id {stripe_id}: {e}")
        return []


async def get_subscription_data_for_email_async(email: str) -> List[Dict[str, Any]]:
    """
    Async version: Get subscription data for a specific email.
    Returns list of subscriptions on success, empty list on failure.
    """
    if not email:
        logger.warning("No email provided to get_subscription_data_for_email_async")
        return []

    try:
        async with AsyncStripeClient(stripe_keys["secret_key"]) as client:
            # All customers with email
            customers_response = await client.list_customers(email=email)
            if not customers_response or not customers_response.get("data"):
                return []

            all_subscriptions = []
            for customer in customers_response["data"]:
                if customer["email"] == email:
                    stripe_id = customer["id"]
                    subscriptions = await get_subscription_data_for_async(stripe_id)
                    if subscriptions:
                        all_subscriptions.extend(subscriptions)

            return all_subscriptions
    except Exception as e:
        logger.error(f"Error getting subscription data for email {email}: {e}")
        return []


async def get_subscription_item_id_for_user_email_async(email: str) -> Optional[str]:
    """
    Async version: Get subscription item ID for a user by email.
    Returns subscription item ID on success, None on failure.
    """
    if not email:
        logger.warning("No email provided to get_subscription_item_id_for_user_email_async")
        return None

    try:
        subscriptions = await get_subscription_data_for_email_async(email)
        for subscription in subscriptions:
            if subscription.get("items", {}).get("data"):
                subscription_item_id = subscription["items"]["data"][0]["id"]
                logger.info(f"Found subscription item ID for {email}: {subscription_item_id}")
                return subscription_item_id
        return None
    except Exception as e:
        logger.error(f"Error getting subscription item ID for email {email}: {e}")
        return None


async def get_self_hosted_subscription_count_for_user_async(stripe_id: str) -> int:
    """
    Async version: Get count of active self-hosted subscriptions for a user.
    Returns count on success, 0 on failure.
    """
    if not stripe_id:
        logger.warning("No stripe_id provided to get_self_hosted_subscription_count_for_user_async")
        return 0

    try:
        subscriptions = await get_subscription_data_for_async(stripe_id)
        count = 0
        for subscription in subscriptions:
            if subscription["customer"] == stripe_id:
                if subscription.get("plan", {}).get("name") == "Text Generator - Self Hosted - Per Instance":
                    if subscription["status"] in ["active", "trialing"]:
                        count += 1
                    else:
                        logger.info(f"subscription not active, status: {subscription['status']}")
        return count
    except Exception as e:
        logger.error(f"Error getting self-hosted subscription count for stripe_id {stripe_id}: {e}")
        return 0


async def validate_stripe_customer_async(stripe_id: str, email: str = None) -> Optional[str]:
    """
    Async version: Validate that a Stripe customer ID exists and is valid.
    If the customer ID is invalid, try to find by email.
    Returns the valid customer ID if found, None otherwise.
    """
    if not stripe_id:
        return None

    try:
        async with AsyncStripeClient(stripe_keys["secret_key"]) as client:
            customer = await client.retrieve_customer(stripe_id)
            if customer and customer.get("id") and not customer.get("deleted", False):
                return customer["id"]
    except Exception as e:
        logger.error(f"Error validating Stripe customer {stripe_id}: {e}")
        # If validation fails and we have email, try to find existing customer by email
        if email:
            logger.info(f"Attempting to find existing Stripe customer by email: {email}")
            try:
                async with AsyncStripeClient(stripe_keys["secret_key"]) as client:
                    customers_response = await client.list_customers(email=email, limit=1)
                    if customers_response and customers_response.get("data"):
                        customer = customers_response["data"][0]
                        logger.info(f"Found existing Stripe customer for {email}: {customer['id']}")
                        return customer["id"]
            except Exception as email_error:
                logger.error(f"Error finding Stripe customer by email {email}: {email_error}")

    return None


def validate_stripe_customer(stripe_id, email=None):
    """
    Validate that a Stripe customer ID exists and is valid.
    If the customer ID is invalid (e.g., from different mode), try to find by email.
    Returns the valid customer ID if found, None otherwise.
    """
    if not stripe_id:
        logger.warning("No stripe_id provided to validate_stripe_customer")
        return None

    logger.debug(f"Validating Stripe customer: {stripe_id}")
    try:
        customer = stripe.Customer.retrieve(stripe_id)
        if customer and customer.id and not customer.get("deleted", False):
            logger.debug(f"Successfully validated Stripe customer: {stripe_id}")
            return customer.id
        else:
            logger.warning(f"Stripe customer {stripe_id} is deleted or invalid")
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
                else:
                    logger.warning(f"No Stripe customer found for email: {email}")
            except Exception as email_error:
                logger.error(f"Error finding Stripe customer by email {email}: {email_error}")

    return None
