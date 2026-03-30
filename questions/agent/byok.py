"""BYOK — Bring Your Own Key management.

Stores user API keys encrypted with Fernet (symmetric encryption).
Keys are encrypted at rest in the database, decrypted only when needed for API calls.
"""

import hashlib
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Derive encryption key from a secret. In production, set BYOK_ENCRYPTION_KEY env var.
# Falls back to deriving from a stable secret for development.
_ENCRYPTION_KEY = os.getenv("BYOK_ENCRYPTION_KEY")


def _get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    key = _ENCRYPTION_KEY
    if not key:
        # Derive a stable key from a seed for development
        seed = os.getenv("SECRET_KEY", "text-generator-dev-byok-seed-change-me")
        key = hashlib.sha256(seed.encode()).digest()
        import base64

        key = base64.urlsafe_b64encode(key)
    elif isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def _make_prefix(api_key: str) -> str:
    """Create a safe display prefix from an API key."""
    if len(api_key) <= 8:
        return api_key[:3] + "..."
    return api_key[:6] + "..." + api_key[-4:]


SUPPORTED_PROVIDERS = {
    "openai",
    "anthropic",
    "google",
    "groq",
    "mistral",
    "deepseek",
    "xai",
    "openrouter",
    "together",
    "minimax",
    "fal",
    "cohere",
}


def add_key(db: Session, user_id: str, provider: str, api_key: str) -> dict:
    """Store an encrypted API key for a user+provider. Replaces existing key for same provider."""
    from questions.db_models_postgres import UserAPIKey

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}. Supported: {sorted(SUPPORTED_PROVIDERS)}")

    fernet = _get_fernet()
    encrypted = fernet.encrypt(api_key.encode()).decode()
    prefix = _make_prefix(api_key)

    # Deactivate existing keys for same user+provider
    existing = db.query(UserAPIKey).filter_by(user_id=user_id, provider=provider, is_active=True).all()
    for old_key in existing:
        old_key.is_active = False

    entry = UserAPIKey(
        id=str(uuid.uuid4()),
        user_id=user_id,
        provider=provider,
        encrypted_key=encrypted,
        key_prefix=prefix,
        is_active=True,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry.to_dict()


def get_key(db: Session, user_id: str, provider: str) -> Optional[str]:
    """Retrieve and decrypt the active API key for a user+provider."""
    from questions.db_models_postgres import UserAPIKey

    entry = (
        db.query(UserAPIKey).filter_by(user_id=user_id, provider=provider, is_active=True).first()
    )
    if not entry:
        return None

    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(entry.encrypted_key.encode()).decode()
    except InvalidToken:
        logger.error(f"Failed to decrypt key for user={user_id} provider={provider}")
        return None

    # Update last_used_at
    entry.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return decrypted


def list_keys(db: Session, user_id: str) -> List[dict]:
    """List all active API keys for a user (no secrets exposed)."""
    from questions.db_models_postgres import UserAPIKey

    entries = db.query(UserAPIKey).filter_by(user_id=user_id, is_active=True).all()
    return [e.to_dict() for e in entries]


def revoke_key(db: Session, user_id: str, key_id: str) -> bool:
    """Revoke (deactivate) an API key."""
    from questions.db_models_postgres import UserAPIKey

    entry = db.query(UserAPIKey).filter_by(id=key_id, user_id=user_id, is_active=True).first()
    if not entry:
        return False
    entry.is_active = False
    db.commit()
    return True


def get_user_providers(db: Session, user_id: str) -> set:
    """Get the set of providers a user has active keys for."""
    from questions.db_models_postgres import UserAPIKey

    entries = db.query(UserAPIKey.provider).filter_by(user_id=user_id, is_active=True).distinct().all()
    return {e[0] for e in entries}
