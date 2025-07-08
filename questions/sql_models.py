import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///data.db')

if DATABASE_URL.startswith('sqlite'):
    connect_args = {'check_same_thread': False}
    if DATABASE_URL == 'sqlite:///:memory:':
        engine = create_engine(
            DATABASE_URL,
            connect_args=connect_args,
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            connect_args=connect_args,
        )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    def to_dict(self):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        for k, v in result.items():
            if hasattr(v, 'isoformat'):
                result[k] = v.isoformat()
        return result

class User(BaseModel):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    stripe_id = Column(String)
    secret = Column(String)
    password_hash = Column(String)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_subscribed = Column(Boolean, default=False)
    num_self_hosted_instances = Column(Integer, default=0)
    cookie_user = Column(Integer)
    profile_url = Column(String)
    access_token = Column(String)
    photo_url = Column(String)
    free_credits = Column(Integer, default=0)
    charges_monthly = Column(Integer, default=0)

    @classmethod
    def byId(cls, id):
        with SessionLocal() as session:
            return session.query(cls).filter_by(id=id).first()

    @classmethod
    def byEmail(cls, email):
        with SessionLocal() as session:
            return session.query(cls).filter_by(email=email).first()

    @classmethod
    def bySecret(cls, secret):
        with SessionLocal() as session:
            return session.query(cls).filter_by(secret=secret).first()

    @classmethod
    def save(cls, user):
        with SessionLocal() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

# Initialize the tables if they don't exist
Base.metadata.create_all(bind=engine)
