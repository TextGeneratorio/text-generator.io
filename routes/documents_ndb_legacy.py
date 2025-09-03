import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Assuming models are accessible like this, adjust if necessary
from questions.db_models import Document

router = APIRouter(
    prefix="/api/docs",
    tags=["documents"],
)


@router.get("/list")
async def list_documents_route(request: Request):
    user_id = request.query_params.get("userId")
    if not user_id:
        # Consider fetching userId from authenticated session/token if possible
        # instead of relying solely on query param for security.
        return JSONResponse({"error": "User ID is required"}, status_code=400)

    try:
        documents = Document.byUserId(user_id)
        docs_list = []
        for doc in documents:
            doc_dict = doc.to_dict()
            # Ensure ID is included correctly if key is available
            if doc.key:
                doc_dict["id"] = doc.key.id()
            docs_list.append(doc_dict)

        return JSONResponse({"documents": docs_list})
    except Exception as e:
        logger.error(f"Error listing documents for user {user_id}: {e}")
        return JSONResponse({"error": "Failed to list documents"}, status_code=500)


@router.get("/get")
async def get_document_route(request: Request):
    doc_id_str = request.query_params.get("id")
    if not doc_id_str:
        return JSONResponse({"error": "Document ID is required"}, status_code=400)

    try:
        # Assuming ID is numeric, handle potential errors if it's not
        # doc_id = int(doc_id_str) # NDB keys can be string or int, check model usage
        document = Document.byId(doc_id_str)  # Assuming byId handles string/int ID

        if not document:
            return JSONResponse({"error": "Document not found"}, status_code=404)

        doc_dict = document.to_dict()
        if document.key:
            doc_dict["id"] = document.key.id()

        return JSONResponse(doc_dict)
    except ValueError:
        logger.error(f"Invalid Document ID format: {doc_id_str}")
        return JSONResponse({"error": "Invalid Document ID format"}, status_code=400)
    except Exception as e:
        logger.error(f"Error getting document {doc_id_str}: {e}")
        return JSONResponse({"error": "Failed to get document"}, status_code=500)


@router.post("/save")
async def save_document_route(request: Request):
    try:
        data = await request.json()
        user_id = data.get("userId")
        title = data.get("title", "Untitled Document")
        content = data.get("content", "")
        doc_id = data.get("id")  # ID might be present for updates

        if not user_id:
            # TODO: Get userId from authenticated session/token
            return JSONResponse({"error": "User ID is required"}, status_code=400)

        document = None
        if doc_id:
            document = Document.byId(doc_id)
            if document and document.user_id != user_id:
                # Prevent user from saving over someone else's doc
                logger.warning(f"User {user_id} attempted to save document {doc_id} owned by {document.user_id}")
                return JSONResponse({"error": "Permission denied"}, status_code=403)

        if not document:
            # Create new document
            document = Document(user_id=user_id, title=title, content=content)
            logger.info(f"Creating new document for user {user_id}")
        else:
            # Update existing document
            document.title = title
            document.content = content
            logger.info(f"Updating document {doc_id} for user {user_id}")

        # Save document
        key = Document.save(document)
        saved_id = key.id() if key else doc_id  # Use key ID if available

        return JSONResponse({"id": saved_id, "success": True, "message": "Document saved successfully"})
    except Exception as e:
        logger.exception(f"Error saving document for user {user_id}: {e}")  # Use logger.exception for stack trace
        return JSONResponse({"error": "Failed to save document"}, status_code=500)


@router.post("/autosave")
async def autosave_document_route(request: Request):
    # This can reuse the save logic
    # For simplicity, duplicating logic slightly, could refactor later
    try:
        data = await request.json()
        user_id = data.get("userId")
        doc_id = data.get("id")
        title = data.get("title", "Untitled Document")
        content = data.get("content", "")

        if not user_id:
            # TODO: Get userId from authenticated session/token
            return JSONResponse({"error": "User ID is required"}, status_code=400)

        document = None
        if doc_id:
            document = Document.byId(doc_id)
            if document and document.user_id != user_id:
                # Prevent user from saving over someone else's doc
                logger.warning(f"User {user_id} attempted to autosave document {doc_id} owned by {document.user_id}")
                return JSONResponse({"error": "Permission denied"}, status_code=403)

        if not document:
            # Create new document if ID doesn't exist or wasn't provided
            document = Document(user_id=user_id, title=title, content=content)
            # logger.info(f"Creating new document via autosave for user {user_id}") # Less verbose for autosave
        else:
            # Update existing document
            document.title = title
            document.content = content
            # logger.info(f"Autosaving document {doc_id} for user {user_id}") # Less verbose

        # Save document
        key = Document.save(document)
        saved_id = key.id() if key else doc_id  # Use key ID if available

        return JSONResponse(
            {
                "id": saved_id,  # Return the ID (new or existing)
                "success": True,
                "message": "Document autosaved",
            }
        )
    except Exception as e:
        # Avoid logging full exceptions for frequent autosaves unless debugging
        logger.error(f"Error autosaving document for user {user_id}: {e}")
        return JSONResponse({"error": "Failed to autosave document"}, status_code=500)
