import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from questions.db_models_postgres import Base, Document, User

_old_init = httpx.Client.__init__


def fixed_init(self, *args, **kwargs):
    # Remove 'app' from kwargs if present
    kwargs.pop("app", None)
    _old_init(self, *args, **kwargs)


httpx.Client.__init__ = fixed_init

# SQLite test database URL (in-memory for speed and isolation)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with SQLite for fast, isolated testing
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_test_db):
    """Create a fresh database session for each test."""
    # Create a new session for each test
    session = TestingSessionLocal()

    # Clear all tables between tests for clean state
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    yield session

    # Clean up after the test
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        id="test_user_123",
        email="test@example.com",
        name="Test User",
        secret="test_secret_key",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_document(db_session, test_user):
    """Create a test document."""
    import time

    doc_id = f"doc_{int(time.time() * 1000)}"
    document = Document(id=doc_id, user_id=test_user.id, title="Test Document", content="This is test content")
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


class MockRequest:
    def __init__(self, query_params=None, json_data=None, user=None):
        self.query_params = query_params or {}
        self._json = json_data or {}
        self.user = user

    async def json(self):
        return self._json


@pytest.fixture
def mock_authenticated_request():
    """Create a mock request with authentication."""

    def _create_request(user=None, query_params=None, json_data=None):
        return MockRequest(query_params=query_params, json_data=json_data, user=user)

    return _create_request
