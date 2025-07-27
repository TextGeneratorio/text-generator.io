from fastapi import HTTPException, Depends
from .db_models_postgres import User
from .payments.payments import get_subscription_item_id_for_user_email
from .auth import get_current_user


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
        raise HTTPException(
            status_code=403, 
            detail="Active subscription required to access this feature"
        )
    
    return user


def check_user_subscription(user: User) -> bool:
    """
    Check if a user has an active subscription.
    Returns True if subscribed, False otherwise.
    """
    if not user or not user.email:
        return False
    
    try:
        subscription_item_id = get_subscription_item_id_for_user_email(user.email)
        return subscription_item_id is not None
    except Exception:
        return False


def get_subscription_status(user: User) -> dict:
    """
    Get detailed subscription status for a user.
    Returns dictionary with subscription info.
    """
    if not user or not user.email:
        return {
            "is_subscribed": False,
            "subscription_required": True,
            "message": "Please log in to access premium features"
        }
    
    try:
        subscription_item_id = get_subscription_item_id_for_user_email(user.email)
        is_subscribed = subscription_item_id is not None
        
        return {
            "is_subscribed": is_subscribed,
            "subscription_required": not is_subscribed,
            "message": "Subscribe to unlock premium features" if not is_subscribed else "Active subscription",
            "subscription_item_id": subscription_item_id
        }
    except Exception as e:
        return {
            "is_subscribed": False,
            "subscription_required": True,
            "message": "Error checking subscription status",
            "error": str(e)
        }
