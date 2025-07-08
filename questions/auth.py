import bcrypt
import secrets
import string
from typing import Optional
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
from .db_models_postgres import User, get_db
import os

# Configuration
BCRYPT_ROUNDS = 12
BCRYPT_PEPPER = os.getenv("BCRYPT_PEPPER", "")


def hash_password(password: str) -> str:
    """Hash a password with bcrypt and pepper."""
    password_peppered = password + BCRYPT_PEPPER
    hashed = bcrypt.hashpw(password_peppered.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    password_peppered = password + BCRYPT_PEPPER
    return bcrypt.checkpw(password_peppered.encode("utf-8"), password_hash.encode("utf-8"))


def generate_random_string(length: int = 32) -> str:
    """Generate a random string for secrets."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_user_id() -> str:
    """Generate a unique user ID."""
    return generate_random_string(16)


def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """Authenticate a user with email and password."""
    user = User.get_by_email(db, email)
    if not user:
        return None
    
    if not user.password_hash:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def create_user(email: str, password: str, db: Session) -> User:
    """Create a new user with email and password."""
    # Check if user already exists
    existing_user = User.get_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    user = User(
        id=generate_user_id(),
        email=email,
        password_hash=hash_password(password),
        secret=generate_random_string(32)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def login_or_create_user(email: str, password: str, db: Session) -> User:
    """Login user or create if doesn't exist (migration-friendly)."""
    user = User.get_by_email(db, email)
    
    if user and user.password_hash:
        # Existing user with password - verify it
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid credentials")
    else:
        # New user or existing user without password (from Firebase migration)
        if not user:
            user = User(
                id=generate_user_id(),
                email=email,
                secret=generate_random_string(32)
            )
            db.add(user)
        
        # Set password
        user.password_hash = hash_password(password)
        db.commit()
        db.refresh(user)
    
    return user


# Session management (simple in-memory for now, could be Redis later)
session_dict = {}


def set_session_for_user(user: User):
    """Store user session."""
    if user:
        session_dict[user.secret] = user


def get_user_from_session(secret: str) -> Optional[User]:
    """Get user from session by secret."""
    return session_dict.get(secret)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from session cookie or header."""
    # Try to get from session cookie
    secret = request.cookies.get("session_secret")
    
    # Try to get from Authorization header
    if not secret:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            secret = auth_header[7:]
    
    if not secret:
        return None
    
    # First try from memory cache
    user = get_user_from_session(secret)
    if user:
        return user
    
    # Fallback to database lookup
    user = User.get_by_secret(db, secret)
    if user:
        set_session_for_user(user)
    
    return user


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """Require authentication, raise 401 if not authenticated."""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
