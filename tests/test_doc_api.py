import json
import pytest
from unittest.mock import Mock, patch
from questions.db_models_postgres import Document, User
from routes.documents import list_documents_route as list_documents, get_document_route as get_document, save_document_route as save_document, autosave_document_route as autosave_document

pytestmark = [pytest.mark.integration]

class MockRequest:
    def __init__(self, query_params=None, json_data=None, cookies=None, headers=None):
        self.query_params = query_params or {}
        self._json = json_data or {}
        self.cookies = cookies or {}
        self.headers = headers or {}
    
    async def json(self):
        return self._json

@pytest.mark.asyncio
async def test_list_documents_route(db_session, test_user, test_document):
    """Test listing documents for a user."""
    # Create another document
    import time
    doc2_id = f"doc_{int(time.time() * 1000) + 1}"  # Add 1 to ensure unique ID
    doc2 = Document(
        id=doc2_id,
        user_id=test_user.id,
        title="Second Document",
        content="More content"
    )
    db_session.add(doc2)
    db_session.commit()
    
    # Test successful request with authenticated user
    request = MockRequest(cookies={"session_secret": test_user.secret})
    with patch('routes.documents.get_current_user', return_value=test_user):
        response = await list_documents(request, db_session)
        
        assert response.status_code == 200
        data = json.loads(response.body)
        assert "documents" in data
        assert len(data["documents"]) == 2
    
    # Test unauthenticated request
    request = MockRequest(cookies={})
    with patch('routes.documents.get_current_user', return_value=None):
        response = await list_documents(request, db_session)
        
        assert response.status_code == 401
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
    
    # Test non-existent document ID
    request = MockRequest(query_params={"id": "invalid"})
    response = await get_document(request, db_session)
    
    assert response.status_code == 404
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
    request = MockRequest(
        json_data={
            "title": "New Document",
            "content": "New content"
        },
        cookies={"session_secret": test_user.secret}
    )
    with patch('routes.documents.get_current_user', return_value=test_user):
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
    request = MockRequest(
        json_data={
            "id": test_document.id,
            "title": "Updated Document",
            "content": "Updated content"
        },
        cookies={"session_secret": test_user.secret}
    )
    with patch('routes.documents.get_current_user', return_value=test_user):
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
    
    # Try to update test_document with other_user's credentials
    request = MockRequest(
        json_data={
            "id": test_document.id,
            "title": "Malicious Update",
            "content": "Malicious content"
        },
        cookies={"session_secret": other_user.secret}
    )
    with patch('routes.documents.get_current_user', return_value=other_user):
        response = await save_document(request, db_session)
        
        assert response.status_code == 403
        data = json.loads(response.body)
        assert "error" in data

@pytest.mark.asyncio
async def test_save_document_route_missing_user_id(db_session):
    """Test error when user is not authenticated."""
    request = MockRequest(
        json_data={
            "title": "Document without user",
            "content": "Content"
        },
        cookies={}
    )
    with patch('routes.documents.get_current_user', return_value=None):
        response = await save_document(request, db_session)
        
        assert response.status_code == 401
        data = json.loads(response.body)
        assert "error" in data

@pytest.mark.asyncio
async def test_autosave_document_route(db_session, test_user):
    """Test autosaving a document."""
    # Test autosaving new document
    request = MockRequest(
        json_data={
            "title": "Autosaved Document",
            "content": "Autosaved content"
        },
        cookies={"session_secret": test_user.secret}
    )
    with patch('routes.documents.get_current_user', return_value=test_user):
        response = await autosave_document(request, db_session)
        
        assert response.status_code == 200
        data = json.loads(response.body)
        assert data["success"] is True
        assert "id" in data
        
        # Test autosaving existing document
        doc_id = data["id"]
        request = MockRequest(
            json_data={
                "id": doc_id,
                "title": "Updated Autosave",
                "content": "Updated autosave content"
            },
            cookies={"session_secret": test_user.secret}
        )
        response = await autosave_document(request, db_session)
        
        assert response.status_code == 200
        data = json.loads(response.body)
        assert data["success"] is True
    assert data["id"] == doc_id
