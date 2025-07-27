from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from typing import Optional

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/textgen")

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
    documents = relationship("Document", back_populates="user")
    ai_characters = relationship("AICharacter", back_populates="user")
    voices = relationship("Voice", back_populates="user")

    @classmethod
    def get_by_id(cls, session, user_id: str) -> Optional['User']:
        return session.query(cls).filter(cls.id == user_id).first()

    @classmethod
    def get_by_email(cls, session, email: str) -> Optional['User']:
        return session.query(cls).filter(cls.email == email).first()

    @classmethod
    def get_by_secret(cls, session, secret: str) -> Optional['User']:
        return session.query(cls).filter(cls.secret == secret).first()

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created': self.created.isoformat() if self.created else None,
            'updated': self.updated.isoformat() if self.updated else None,
            'is_subscribed': self.is_subscribed,
            'stripe_id': self.stripe_id,
            'secret': self.secret,
            'free_credits': self.free_credits,
            'charges_monthly': self.charges_monthly,
            'num_self_hosted_instances': self.num_self_hosted_instances,
            'profile_url': self.profile_url,
            'photo_url': self.photo_url,
        }


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    title = Column(String, default="Untitled Document")
    content = Column(Text, nullable=True)
    created = Column(DateTime, default=func.now())
    updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="documents")

    @classmethod
    def get_by_id(cls, session, doc_id: str) -> Optional['Document']:
        return session.query(cls).filter(cls.id == doc_id).first()

    @classmethod
    def get_by_user_id(cls, session, user_id: str):
        return session.query(cls).filter(cls.user_id == user_id).order_by(cls.updated.desc()).all()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'created': self.created.isoformat() if self.created else None,
            'updated': self.updated.isoformat() if self.updated else None,
        }


class AICharacter(Base):
    __tablename__ = "ai_characters"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=True)
    greeting = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    avatar_file_name = Column(String, nullable=True)
    bucket_name = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    visibility = Column(String, nullable=True)
    url_name = Column(String, nullable=True)
    num_interactions = Column(Integer, default=0)
    user__id = Column(String, ForeignKey('users.id'), nullable=True)  # Using existing column name
    user__username = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    voice = Column(String, nullable=True)
    img_gen_enabled = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    search_score = Column(Integer, default=0)
    updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="ai_characters", foreign_keys=[user__id])

    @classmethod
    def get_by_id(cls, session, character_id: str) -> Optional['AICharacter']:
        return session.query(cls).filter(cls.id == character_id).first()

    @classmethod
    def get_by_name(cls, session, name: str) -> Optional['AICharacter']:
        return session.query(cls).filter(cls.name == name).first()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'greeting': self.greeting,
            'description': self.description,
            'avatar_file_name': self.avatar_file_name,
            'bucket_name': self.bucket_name,
            'tags': self.tags,
            'visibility': self.visibility,
            'url_name': self.url_name,
            'num_interactions': self.num_interactions,
            'user__id': self.user__id,
            'user__username': self.user__username,
            'gender': self.gender,
            'voice': self.voice,
            'img_gen_enabled': self.img_gen_enabled,
            'priority': self.priority,
            'search_score': self.search_score,
            'updated': self.updated.isoformat() if self.updated else None,
        }


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    urlkey = Column(String, nullable=True)
    description = Column(String, nullable=True)
    visibility = Column(String, nullable=True)
    invite_code = Column(String, nullable=True)
    user_count = Column(Integer, default=0)
    users_names = Column(JSON, nullable=True)
    characters = Column(JSON, nullable=True)
    admins = Column(JSON, nullable=True)

    # Relationships
    messages = relationship("ChatMessage", back_populates="chat_room")

    @classmethod
    def get_by_id(cls, session, room_id: str) -> Optional['ChatRoom']:
        return session.query(cls).filter(cls.id == room_id).first()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'urlkey': self.urlkey,
            'description': self.description,
            'visibility': self.visibility,
            'invite_code': self.invite_code,
            'user_count': self.user_count,
            'users_names': self.users_names,
            'characters': self.characters,
            'admins': self.admins,
        }


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)
    chat_room_id = Column(String, ForeignKey('chat_rooms.id'), nullable=True)
    text = Column(Text, nullable=True)
    username = Column(String, nullable=True)
    avatar_file_name = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    # Relationships
    chat_room = relationship("ChatRoom", back_populates="messages")

    @classmethod
    def get_by_id(cls, session, message_id: str) -> Optional['ChatMessage']:
        return session.query(cls).filter(cls.id == message_id).first()

    @classmethod
    def get_by_chat_room_id(cls, session, chat_room_id: str):
        return session.query(cls).filter(cls.chat_room_id == chat_room_id).order_by(cls.timestamp.asc()).all()

    def to_dict(self):
        return {
            'id': self.id,
            'chat_room_id': self.chat_room_id,
            'text': self.text,
            'username': self.username,
            'avatar_file_name': self.avatar_file_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class Voice(Base):
    __tablename__ = "voices"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url_name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    avatar_file_name = Column(String, nullable=True)
    voice_sample_url = Column(String, nullable=True)
    voice_input_url = Column(String, nullable=True)
    sample_text = Column(String, nullable=True)
    user__id = Column(String, ForeignKey('users.id'), nullable=True)  # Using existing column name
    user__username = Column(String, nullable=True)
    visibility = Column(String, nullable=True)
    created = Column(DateTime, default=func.now())
    updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="voices", foreign_keys=[user__id])

    @classmethod
    def get_by_id(cls, session, voice_id: str) -> Optional['Voice']:
        return session.query(cls).filter(cls.id == voice_id).first()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url_name': self.url_name,
            'description': self.description,
            'avatar_file_name': self.avatar_file_name,
            'voice_sample_url': self.voice_sample_url,
            'voice_input_url': self.voice_input_url,
            'sample_text': self.sample_text,
            'user__id': self.user__id,
            'user__username': self.user__username,
            'visibility': self.visibility,
            'created': self.created.isoformat() if self.created else None,
            'updated': self.updated.isoformat() if self.updated else None,
        }


class SaveGame(Base):
    __tablename__ = "save_games"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    input_outputs = Column(JSON, nullable=True)
    backstory = Column(String, nullable=True)

    @classmethod
    def get_by_id(cls, session, save_id: str) -> Optional['SaveGame']:
        return session.query(cls).filter(cls.id == save_id).first()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'input_outputs': self.input_outputs,
            'backstory': self.backstory,
        }


# Database session handling
def get_db_session():
    """
    Get a database session that can be used in both main.py and inference_server.
    This ensures consistent database access across both servers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
