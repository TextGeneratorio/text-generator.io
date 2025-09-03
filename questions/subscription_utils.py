import hashlib
import logging
import os
import secrets
import time
from typing import Dict, Optional, Tuple

from fastapi import Depends, Header, HTTPException

from .auth import get_current_user
from .db_models_postgres import User
from .payments.payments import get_subscription_item_id_for_user_email

logger = logging.getLogger(__name__)

# Subscription status cache: email -> (subscription_item_id, timestamp)
_subscription_cache: Dict[str, Tuple[Optional[str], float]] = {}
SUBSCRIPTION_CACHE_TTL = 300  # 5 minutes cache TTL

# Backend validation secret - should be set in environment
BACKEND_VALIDATION_SECRET = os.getenv("BACKEND_VALIDATION_SECRET", "")
if not BACKEND_VALIDATION_SECRET:
    # Generate a random secret if not set - this ensures it's always available
    BACKEND_VALIDATION_SECRET = secrets.token_hex(32)
    logger.warning("BACKEND_VALIDATION_SECRET not set in environment. Using generated secret.")


def require_subscription(user: User = Depends(get_current_user)) -> User:
    """
    Dependency that ensures user has an active subscription.
    Raises HTTPException if user is not subscribed.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check if user has active subscription
    subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    if not subscription_item_id:
        raise HTTPException(status_code=403, detail="Active subscription required to access this feature")

    return user


def get_subscription_item_id_cached(user_email: str) -> Optional[str]:
    """
    Get subscription item ID with caching to reduce Stripe API calls.
    Cache expires after SUBSCRIPTION_CACHE_TTL seconds.
    """
    current_time = time.time()

    # Check cache first
    if user_email in _subscription_cache:
        subscription_item_id, cached_time = _subscription_cache[user_email]
        if current_time - cached_time < SUBSCRIPTION_CACHE_TTL:
            logger.debug(f"Using cached subscription status for {user_email}")
            return subscription_item_id

    # Cache miss or expired, fetch from Stripe
    try:
        subscription_item_id = get_subscription_item_id_for_user_email(user_email)
        _subscription_cache[user_email] = (subscription_item_id, current_time)
        logger.info(f"Cached subscription status for {user_email}: {subscription_item_id is not None}")
        return subscription_item_id
    except Exception as e:
        logger.error(f"Error fetching subscription for {user_email}: {e}")
        return None


def check_user_subscription(user: User) -> bool:
    """
    Check if a user has an active subscription.
    Returns True if subscribed, False otherwise.
    """
    if not user or not user.email:
        return False

    try:
        subscription_item_id = get_subscription_item_id_cached(user.email)
        return subscription_item_id is not None
    except Exception:
        return False


def clear_subscription_cache(user_email: str = None):
    """
    Clear subscription cache for a specific user or all users.
    """
    global _subscription_cache
    if user_email:
        _subscription_cache.pop(user_email, None)
        logger.info(f"Cleared subscription cache for {user_email}")
    else:
        _subscription_cache.clear()
        logger.info("Cleared entire subscription cache")


def generate_subscription_validation_token(user_email: str, subscription_item_id: str) -> str:
    """
    Generate a secure validation token for subscription verification.
    This provides an additional layer of security against subscription bypass.
    """
    data = f"{user_email}:{subscription_item_id}:{BACKEND_VALIDATION_SECRET}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def validate_subscription_with_backend_secret(user: User, validation_token: str = None) -> bool:
    """
    Validate subscription with backend secret verification.
    This provides extra security by requiring both:
    1. Valid subscription in Stripe
    2. Valid backend validation token
    """
    if not user or not user.email:
        logger.warning("Subscription validation failed: No user or email")
        return False

    try:
        # First check if user has active subscription
        subscription_item_id = get_subscription_item_id_for_user_email(user.email)
        if not subscription_item_id:
            logger.warning(f"Subscription validation failed: No active subscription for {user.email}")
            return False

        # If validation token is provided, verify it matches
        if validation_token:
            expected_token = generate_subscription_validation_token(user.email, subscription_item_id)
            if validation_token != expected_token:
                logger.error(f"Subscription validation failed: Invalid backend token for {user.email}")
                return False

        logger.info(f"Subscription validation successful for {user.email}")
        return True

    except Exception as e:
        logger.error(f"Subscription validation error for {user.email}: {e}")
        return False


def validate_subscription_with_backend_secret_cached(user: User, validation_token: str = None) -> bool:
    """
    Validate subscription with backend secret verification using cached subscription data.
    This provides extra security and performance by:
    1. Using cached subscription data to reduce Stripe API calls
    2. Validating subscription in Stripe (cached)
    3. Validating backend validation token
    """
    if not user or not user.email:
        logger.warning("Subscription validation failed: No user or email")
        return False

    try:
        # First check if user has active subscription (using cache)
        subscription_item_id = get_subscription_item_id_cached(user.email)
        if not subscription_item_id:
            logger.warning(f"Subscription validation failed: No active subscription for {user.email}")
            return False

        # If validation token is provided, verify it matches
        if validation_token:
            expected_token = generate_subscription_validation_token(user.email, subscription_item_id)
            if validation_token != expected_token:
                logger.error(f"Subscription validation failed: Invalid backend token for {user.email}")
                return False

        logger.info(f"Subscription validation successful for {user.email} (cached)")
        return True

    except Exception as e:
        logger.error(f"Subscription validation error for {user.email}: {e}")
        return False


def require_subscription_with_backend_validation(
    user: User = Depends(get_current_user), x_validation_token: str = Header(default=None, alias="X-Validation-Token")
) -> User:
    """
    Enhanced subscription requirement with backend secret validation.
    This is the most secure subscription check that should be used for Claude API calls.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not validate_subscription_with_backend_secret(user, x_validation_token):
        raise HTTPException(status_code=403, detail="Active subscription with valid backend validation required")

    return user


def get_subscription_status(user: User) -> dict:
    """
    Get detailed subscription status for a user with caching.
    Returns dictionary with subscription info.
    """
    if not user or not user.email:
        return {
            "is_subscribed": False,
            "subscription_required": True,
            "message": "Please log in to access premium features",
        }

    try:
        subscription_item_id = get_subscription_item_id_cached(user.email)
        is_subscribed = subscription_item_id is not None

        return {
            "is_subscribed": is_subscribed,
            "subscription_required": not is_subscribed,
            "message": "Subscribe to unlock premium features" if not is_subscribed else "Active subscription",
            "subscription_item_id": subscription_item_id,
        }
    except Exception as e:
        return {
            "is_subscribed": False,
            "subscription_required": True,
            "message": "Error checking subscription status",
            "error": str(e),
        }
