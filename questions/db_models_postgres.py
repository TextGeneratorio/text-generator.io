from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    title = Column(String, default="Untitled Document")
    content = Column(Text, nullable=True)
    created = Column(DateTime, default=func.now())
    updated = Column(DateTime, default=func.now(), onupdate=func.now())

    @classmethod
    def get_by_id(cls, session, doc_id: int) -> Optional['Document']:
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


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
