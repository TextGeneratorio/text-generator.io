import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from questions.db_models_postgres import Base, Document, User
from routes.documents import list_documents_route as list_documents, get_document_route as get_document, save_document_route as save_document, autosave_document_route as autosave_document

# Set up in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

pytestmark = [pytest.mark.integration]

class MockRequest:
    def __init__(self, query_params=None, json_data=None):
        self.query_params = query_params or {}
        self._json = json_data or {}
    
    async def json(self):
        return self._json

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        id="test_user_123",
        email="test@example.com",
        name="Test User",
        secret="test_secret_key",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_document(db_session, test_user):
    """Create a test document."""
    document = Document(
        user_id=test_user.id,
        title="Test Document",
        content="This is test content"
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document

@pytest.mark.asyncio
async def test_list_documents_route(db_session, test_user, test_document):
    """Test listing documents for a user."""
    # Create another document
    doc2 = Document(
        user_id=test_user.id,
        title="Second Document",
        content="More content"
    )
    db_session.add(doc2)
    db_session.commit()
    
    # Test successful request
    request = MockRequest(query_params={"userId": test_user.id})
    response = await list_documents(request, db_session)
    
    assert response.status_code == 200
    data = json.loads(response.body)
    assert "documents" in data
    assert len(data["documents"]) == 2
    
    # Test missing user ID
    request = MockRequest(query_params={})
    response = await list_documents(request, db_session)
    
    assert response.status_code == 400
    data = json.loads(response.body)
    assert "error" in data

@pytest.mark.asyncio
async def test_get_document_route(db_session, test_user, test_document):
    """Test getting a specific document."""
    # Test successful request
    request = MockRequest(query_params={"id": str(test_document.id)})
    response = await get_document(request, db_session)
    
    assert response.status_code == 200
    data = json.loads(response.body)
    assert data["id"] == test_document.id
    assert data["title"] == test_document.title
    assert data["content"] == test_document.content
    
    # Test missing document ID
    request = MockRequest(query_params={})
    response = await get_document(request, db_session)
    
    assert response.status_code == 400
    data = json.loads(response.body)
    assert "error" in data
    
    # Test invalid document ID format
    request = MockRequest(query_params={"id": "invalid"})
    response = await get_document(request, db_session)
    
    assert response.status_code == 400
    data = json.loads(response.body)
    assert "error" in data
    
    # Test non-existent document
    request = MockRequest(query_params={"id": "999999"})
    response = await get_document(request, db_session)
    
    assert response.status_code == 404
    data = json.loads(response.body)
    assert "error" in data

@pytest.mark.asyncio
async def test_save_document_route_new(db_session, test_user):
    """Test saving a new document."""
    # Test creating new document
    request = MockRequest(json_data={
        "userId": test_user.id,
        "title": "New Document",
        "content": "New content"
    })
    response = await save_document(request, db_session)
    
    assert response.status_code == 200
    data = json.loads(response.body)
    assert data["success"] is True
    assert "id" in data
    
    # Verify document was created
    doc_id = data["id"]
    document = Document.get_by_id(db_session, doc_id)
    assert document is not None
    assert document.title == "New Document"
    assert document.content == "New content"
    assert document.user_id == test_user.id

@pytest.mark.asyncio
async def test_save_document_route_update(db_session, test_user, test_document):
    """Test updating an existing document."""
    # Test updating existing document
    request = MockRequest(json_data={
        "id": test_document.id,
        "userId": test_user.id,
        "title": "Updated Document",
        "content": "Updated content"
    })
    response = await save_document(request, db_session)
    
    assert response.status_code == 200
    data = json.loads(response.body)
    assert data["success"] is True
    assert data["id"] == test_document.id
    
    # Verify document was updated
    db_session.refresh(test_document)
    assert test_document.title == "Updated Document"
    assert test_document.content == "Updated content"

@pytest.mark.asyncio
async def test_save_document_route_permission_denied(db_session, test_user, test_document):
    """Test permission denied when trying to save another user's document."""
    # Create another user
    other_user = User(
        id="other_user_456",
        email="other@example.com",
        name="Other User",
        secret="other_secret_key",
        password_hash="other_hashed_password"
    )
    db_session.add(other_user)
    db_session.commit()
    
    # Try to update test_document with other_user's ID
    request = MockRequest(json_data={
        "id": test_document.id,
        "userId": other_user.id,
        "title": "Malicious Update",
        "content": "Malicious content"
    })
    response = await save_document(request, db_session)
    
    assert response.status_code == 403
    data = json.loads(response.body)
    assert "error" in data

@pytest.mark.asyncio
async def test_save_document_route_missing_user_id(db_session):
    """Test error when user ID is missing."""
    request = MockRequest(json_data={
        "title": "Document without user",
        "content": "Content"
    })
    response = await save_document(request, db_session)
    
    assert response.status_code == 400
    data = json.loads(response.body)
    assert "error" in data

@pytest.mark.asyncio
async def test_autosave_document_route(db_session, test_user):
    """Test autosaving a document."""
    # Test autosaving new document
    request = MockRequest(json_data={
        "userId": test_user.id,
        "title": "Autosaved Document",
        "content": "Autosaved content"
    })
    response = await autosave_document(request, db_session)
    
    assert response.status_code == 200
    data = json.loads(response.body)
    assert data["success"] is True
    assert "id" in data
    
    # Test autosaving existing document
    doc_id = data["id"]
    request = MockRequest(json_data={
        "id": doc_id,
        "userId": test_user.id,
        "title": "Updated Autosave",
        "content": "Updated autosave content"
    })
    response = await autosave_document(request, db_session)
    
    assert response.status_code == 200
    data = json.loads(response.body)
    assert data["success"] is True
    assert data["id"] == doc_id
