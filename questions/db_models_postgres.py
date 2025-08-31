from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from typing import Optional

# Database configuration - Environment-aware and simplified
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, production
IS_PRODUCTION = ENVIRONMENT == "production"

# Database credentials - hardcoded as requested
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "lee") 
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = os.getenv("DB_PORT", "5432")

# Database selection based on environment - strict separation
if IS_PRODUCTION:
    DB_NAME = "textgen_prod"
    print(f"🎯 Production environment: using {DB_NAME} database")
    # In production, use explicit production database URL
    if DB_PASSWORD:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Use Unix socket for local connections without password
        DATABASE_URL = f"postgresql://{DB_USER}@/{DB_NAME}?host=/var/run/postgresql"
else:
    DB_NAME = "textgen"
    print(f"🔧 Development environment: using {DB_NAME} database")
    # In development, prioritize DATABASE_URL env var if set, otherwise use textgen
    if os.getenv("DATABASE_URL"):
        DATABASE_URL = os.getenv("DATABASE_URL")
    elif DB_PASSWORD:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Use Unix socket for local connections without password
        DATABASE_URL = f"postgresql://{DB_USER}@/{DB_NAME}?host=/var/run/postgresql"
    # Ensure we never accidentally use production database in development
    if "textgen_prod" in DATABASE_URL:
        print("⚠️  Detected textgen_prod in development, forcing textgen database")
        DATABASE_URL = f"postgresql://{DB_USER}@/textgen?host=/var/run/postgresql"

# Create engine with connection testing
def create_engine_with_testing():
    """Create database engine and test the connection."""
    try:
        engine = create_engine(DATABASE_URL)
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✅ Database connection successful: {DATABASE_URL}")
        return engine
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Database URL: {DATABASE_URL}")
        
        # Only allow fallback in development and only to safe alternatives
        if not IS_PRODUCTION:
            # Try alternative local database names if current fails
            if "textgen" in DATABASE_URL and "textgen_prod" not in DATABASE_URL:
                print("🔄 Development fallback disabled - check your local database setup")
            print("💡 Make sure your local PostgreSQL is running and the textgen database exists")
        
        raise

try:
    engine = create_engine_with_testing()
except Exception as e:
    print(f"⚠️  Using basic engine configuration: {e}")
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=True)  # nullable for migration from Firebase
    created = Column(DateTime, default=func.now())
    updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # User profile fields
    name = Column(String, nullable=True)
    profile_url = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    
    # Subscription and payment fields
    is_subscribed = Column(Boolean, default=False)
    stripe_id = Column(String, nullable=True)
    secret = Column(String, nullable=False)  # API secret
    free_credits = Column(Integer, default=0)
    charges_monthly = Column(Integer, default=0)
    num_self_hosted_instances = Column(Integer, default=0)
    
    # Legacy fields
    cookie_user = Column(Integer, nullable=True)
    access_token = Column(String, nullable=True)

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_rooms = relationship("ChatRoom", back_populates="user", cascade="all, delete-orphan")
    save_games = relationship("SaveGame", back_populates="user", cascade="all, delete-orphan")

    @classmethod
    def get_by_email(cls, db, email: str):
        return db.query(cls).filter(cls.email == email).first()

    @classmethod
    def get_by_secret(cls, db, secret: str):
        return db.query(cls).filter(cls.secret == secret).first()

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_url': self.profile_url,
            'photo_url': self.photo_url,
            'is_subscribed': self.is_subscribed,
            'stripe_id': self.stripe_id,
            'secret': self.secret,
            'free_credits': self.free_credits,
            'charges_monthly': self.charges_monthly,
            'num_self_hosted_instances': self.num_self_hosted_instances,
            'created': self.created.isoformat() if self.created else None,
            'updated': self.updated.isoformat() if self.updated else None
        }


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created = Column(DateTime, default=func.now())
    updated = Column(DateTime, default=func.now(), onupdate=func.now())
    is_public = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="documents")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'user_id': self.user_id,
            'created_at': self.created.isoformat() if self.created else None,
            'updated_at': self.updated.isoformat() if self.updated else None,
            'is_public': self.is_public
        }
    
    @classmethod
    def get_by_id(cls, db, doc_id):
        """Get a document by its ID."""
        return db.query(cls).filter(cls.id == doc_id).first()
    
    @classmethod
    def get_by_user_id(cls, db, user_id):
        """Get all documents for a specific user."""
        return db.query(cls).filter(cls.user_id == user_id).all()


class AICharacter(Base):
    __tablename__ = "ai_characters"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_public = Column(Boolean, default=False)
    
    # Personality and behavior settings
    temperature = Column(String, nullable=True)  # Stored as string for flexibility
    max_tokens = Column(Integer, nullable=True)
    
    # Appearance and avatar
    avatar_url = Column(String, nullable=True)
    voice_id = Column(String, nullable=True)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_public': self.is_public,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'avatar_url': self.avatar_url,
            'voice_id': self.voice_id,
            'usage_count': self.usage_count
        }


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    ai_character_id = Column(String, ForeignKey("ai_characters.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Room settings
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_rooms")
    ai_character = relationship("AICharacter")
    messages = relationship("ChatMessage", back_populates="chat_room", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'ai_character_id': self.ai_character_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'is_public': self.is_public
        }


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)
    chat_room_id = Column(String, ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # None for AI messages
    content = Column(Text, nullable=False)
    message_type = Column(String, nullable=False)  # 'user', 'ai', 'system'
    created_at = Column(DateTime, default=func.now())
    
    # Message metadata
    message_metadata = Column(JSON, nullable=True)  # For storing additional message data
    
    # Relationships
    chat_room = relationship("ChatRoom", back_populates="messages")
    user = relationship("User")
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_room_id': self.chat_room_id,
            'user_id': self.user_id,
            'content': self.content,
            'message_type': self.message_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata
        }


class Voice(Base):
    __tablename__ = "voices"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    voice_id = Column(String, nullable=False)  # External voice service ID
    provider = Column(String, nullable=False)  # 'elevenlabs', 'openai', etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Voice characteristics
    gender = Column(String, nullable=True)
    accent = Column(String, nullable=True)
    age_range = Column(String, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'voice_id': self.voice_id,
            'provider': self.provider,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'gender': self.gender,
            'accent': self.accent,
            'age_range': self.age_range
        }


class SaveGame(Base):
    __tablename__ = "save_games"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    game_type = Column(String, nullable=False)  # '20-questions', 'chat', etc.
    game_state = Column(JSON, nullable=False)  # JSON representation of game state
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Game metadata
    name = Column(String, nullable=True)  # User-friendly name for the save
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="save_games")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_type': self.game_type,
            'game_state': self.game_state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'name': self.name,
            'is_completed': self.is_completed
        }


# Database session handling
def get_db_session():
    """
    Get a database session for use in async contexts.
    Remember to close the session when done.
    """
    return SessionLocal()


def get_db():
    """
    FastAPI dependency for database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session_sync():
    """
    Get a database session for synchronous use (non-FastAPI contexts).
    Remember to close the session when done.
    """
    return SessionLocal()


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
