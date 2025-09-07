import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from questions.auth import get_current_user
from questions.db_models_postgres import Document, get_db
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/docs",
    tags=["documents"],
)


@router.get("/list")
async def list_documents_route(request: Request, db: Session = Depends(get_db)):
    # Get current user from authentication
    current_user = get_current_user(request, db)
    if not current_user:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    try:
        documents = Document.get_by_user_id(db, current_user.id)
        docs_list = [doc.to_dict() for doc in documents]

        return JSONResponse({"documents": docs_list})
    except Exception as e:
        logger.error(f"Error listing documents for user {current_user.id}: {e}")
        return JSONResponse({"error": "Failed to list documents"}, status_code=500)


@router.get("/get")
async def get_document_route(request: Request, db: Session = Depends(get_db)):
    doc_id_str = request.query_params.get("id")
    if not doc_id_str:
        return JSONResponse({"error": "Document ID is required"}, status_code=400)

    try:
        document = Document.get_by_id(db, doc_id_str)

        if not document:
            return JSONResponse({"error": "Document not found"}, status_code=404)

        return JSONResponse(document.to_dict())
    except ValueError:
        logger.error(f"Invalid Document ID format: {doc_id_str}")
        return JSONResponse({"error": "Invalid Document ID format"}, status_code=400)
    except Exception as e:
        logger.error(f"Error getting document {doc_id_str}: {e}")
        return JSONResponse({"error": "Failed to get document"}, status_code=500)


@router.post("/save")
async def save_document_route(request: Request, db: Session = Depends(get_db)):
    try:
        # Get current user from authentication
        current_user = get_current_user(request, db)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)

        data = await request.json()
        user_id = current_user.id  # Use authenticated user ID
        title = data.get("title", "Untitled Document")
        content = data.get("content", "")
        doc_id = data.get("id")  # ID might be present for updates

        document = None
        if doc_id:
            document = Document.get_by_id(db, doc_id)
            if document and document.user_id != user_id:
                # Prevent user from saving over someone else's doc
                logger.warning(f"User {user_id} attempted to save document {doc_id} owned by {document.user_id}")
                return JSONResponse({"error": "Permission denied"}, status_code=403)

        if not document:
            # Create new document with generated ID
            import time

            doc_id = f"doc_{int(time.time() * 1000)}"  # Generate ID similar to frontend format
            document = Document(id=doc_id, user_id=user_id, title=title, content=content)
            db.add(document)
            db.commit()
            db.refresh(document)
            logger.info(f"Creating new document for user {user_id}")
        else:
            # Update existing document
            document.title = title
            document.content = content
            db.commit()
            db.refresh(document)
            logger.info(f"Updating document {doc_id} for user {user_id}")

        return JSONResponse({"id": document.id, "success": True, "message": "Document saved successfully"})
    except Exception as e:
        logger.exception(f"Error saving document: {e}")
        db.rollback()
        return JSONResponse({"error": "Failed to save document"}, status_code=500)


@router.post("/autosave")
async def autosave_document_route(request: Request, db: Session = Depends(get_db)):
    try:
        # Get current user from authentication
        current_user = get_current_user(request, db)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)

        data = await request.json()
        user_id = current_user.id  # Use authenticated user ID
        doc_id = data.get("id")
        title = data.get("title", "Untitled Document")
        content = data.get("content", "")

        document = None
        if doc_id:
            document = Document.get_by_id(db, doc_id)
            if document and document.user_id != user_id:
                # Prevent user from saving over someone else's doc
                logger.warning(f"User {user_id} attempted to autosave document {doc_id} owned by {document.user_id}")
                return JSONResponse({"error": "Permission denied"}, status_code=403)

        if not document:
            # Create new document if ID doesn't exist or wasn't provided
            import time

            doc_id = f"doc_{int(time.time() * 1000)}"  # Generate ID similar to frontend format
            document = Document(id=doc_id, user_id=user_id, title=title, content=content)
            db.add(document)
            db.commit()
            db.refresh(document)
        else:
            # Update existing document
            document.title = title
            document.content = content
            db.commit()
            db.refresh(document)

        return JSONResponse({"id": document.id, "success": True, "message": "Document autosaved"})
    except Exception as e:
        # Avoid logging full exceptions for frequent autosaves unless debugging
        logger.error(f"Error autosaving document: {e}")
        db.rollback()
        return JSONResponse({"error": "Failed to autosave document"}, status_code=500)
