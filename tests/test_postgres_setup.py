import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from questions.db_models_postgres import Base, User

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/textgen")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def test_postgres_connection(setup_db):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_user_crud(setup_db):
    import uuid
    session = SessionLocal()
    
    # Use a unique email to avoid conflicts
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    user = User(id=user_id, email=unique_email, secret="s", password_hash="h")
    session.add(user)
    session.commit()
    fetched = session.query(User).filter_by(id=user_id).first()
    assert fetched is not None
    assert fetched.email == unique_email
    session.delete(fetched)
    session.commit()
    session.close()
