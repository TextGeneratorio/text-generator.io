import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Set

from fastapi import APIRouter, Depends, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, StreamingResponse

from questions.auth import get_current_user
from questions.db_models_postgres import Document, get_db
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/docs",
    tags=["documents"],
)

DEFAULT_TITLE = "Untitled Document"

# In-process pub/sub for live document updates (SSE). The site runs a single
# worker; clients also fall back to BroadcastChannel + polling.
_subscribers: Dict[str, Set[asyncio.Queue]] = {}
_SSE_QUEUE_SIZE = 32
AUTH_UNAVAILABLE_ERROR = "Authentication temporarily unavailable"


def _get_current_user_response(request: Request, db: Session):
    try:
        current_user = get_current_user(request, db)
    except SQLAlchemyError as e:
        logger.error(f"Database error authenticating document request: {e}")
        return None, JSONResponse({"error": AUTH_UNAVAILABLE_ERROR}, status_code=503)
    if not current_user:
        return None, JSONResponse({"error": "Authentication required"}, status_code=401)
    return current_user, None


def _publish(user_id: str, payload: dict) -> None:
    queues = _subscribers.get(str(user_id))
    if not queues:
        return
    for queue in list(queues):
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass


def _is_blank_content(content: str) -> bool:
    """True when a Quill delta (or plain string) holds no user text."""
    if not content:
        return True
    text = content
    try:
        delta = json.loads(content)
        ops = delta.get("ops", delta) if isinstance(delta, dict) else delta
        if isinstance(ops, list):
            parts = []
            for op in ops:
                if not isinstance(op, dict) or "insert" not in op:
                    continue
                insert = op["insert"]
                if isinstance(insert, str):
                    parts.append(insert)
                else:
                    # An embed (image, video, ...) counts as real content
                    return False
            text = "".join(parts)
    except (ValueError, TypeError, AttributeError):
        pass
    return not text.strip()


def _is_default_title(title: str) -> bool:
    return not title or not title.strip() or title.strip() == DEFAULT_TITLE


def _persist(db: Session, user_id: str, data: dict):
    """Shared save path for /save and /autosave.

    Returns (JSONResponse, document|None). Never creates a row for a document
    that is both untitled and empty - that is what produced the pile of
    "Untitled Document" entries.
    """
    title = data.get("title") or DEFAULT_TITLE
    content = data.get("content", "")
    doc_id = data.get("id")

    document = None
    if doc_id:
        document = Document.get_by_id(db, doc_id)
        if document and document.user_id != user_id:
            logger.warning(f"User {user_id} attempted to write document {doc_id} owned by {document.user_id}")
            return JSONResponse({"error": "Permission denied"}, status_code=403), None

    if not document:
        if _is_default_title(title) and _is_blank_content(content):
            # Nothing worth persisting yet - the client keeps it in memory.
            return JSONResponse({"id": None, "success": True, "skipped": "empty"}), None
        # Suffix guards against two documents created in the same millisecond
        doc_id = f"doc_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        document = Document(id=doc_id, user_id=user_id, title=title, content=content)
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"Created document {doc_id} for user {user_id}")
    else:
        document.title = title
        document.content = content
        db.commit()
        db.refresh(document)

    payload = document.to_dict()
    _publish(
        user_id,
        {
            "type": "doc-update",
            "client_id": data.get("client_id"),
            "document": payload,
        },
    )
    return (
        JSONResponse(
            {
                "id": document.id,
                "success": True,
                "updated_at": payload.get("updated_at"),
                "message": "Document saved successfully",
            }
        ),
        document,
    )


@router.get("/list")
async def list_documents_route(request: Request, db: Session = Depends(get_db)):
    current_user, auth_response = _get_current_user_response(request, db)
    if auth_response:
        return auth_response

    try:
        documents = (
            db.query(Document)
            .filter(Document.user_id == current_user.id)
            .order_by(Document.updated.desc(), Document.created.desc())
            .all()
        )
        return JSONResponse({"documents": [doc.to_dict() for doc in documents]})
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

        if not document.is_public:
            current_user, auth_response = _get_current_user_response(request, db)
            if auth_response:
                return auth_response
            if document.user_id != current_user.id:
                return JSONResponse({"error": "Permission denied"}, status_code=403)

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
        current_user, auth_response = _get_current_user_response(request, db)
        if auth_response:
            return auth_response

        data = await request.json()
        response, _ = _persist(db, current_user.id, data)
        return response
    except Exception as e:
        logger.exception(f"Error saving document: {e}")
        db.rollback()
        return JSONResponse({"error": "Failed to save document"}, status_code=500)


@router.post("/autosave")
async def autosave_document_route(request: Request, db: Session = Depends(get_db)):
    try:
        current_user, auth_response = _get_current_user_response(request, db)
        if auth_response:
            return auth_response

        data = await request.json()
        response, _ = _persist(db, current_user.id, data)
        return response
    except Exception as e:
        logger.error(f"Error autosaving document: {e}")
        db.rollback()
        return JSONResponse({"error": "Failed to autosave document"}, status_code=500)


@router.delete("/delete")
async def delete_document_route(request: Request, db: Session = Depends(get_db)):
    doc_id = request.query_params.get("id")
    if not doc_id:
        return JSONResponse({"error": "Document ID is required"}, status_code=400)

    try:
        current_user, auth_response = _get_current_user_response(request, db)
        if auth_response:
            return auth_response

        document = Document.get_by_id(db, doc_id)
        if not document:
            return JSONResponse({"success": True, "message": "Already deleted"})
        if document.user_id != current_user.id:
            return JSONResponse({"error": "Permission denied"}, status_code=403)

        db.delete(document)
        db.commit()
        _publish(current_user.id, {"type": "doc-delete", "id": doc_id})
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        db.rollback()
        return JSONResponse({"error": "Failed to delete document"}, status_code=500)


@router.post("/prune-empty")
async def prune_empty_documents_route(request: Request, db: Session = Depends(get_db)):
    """Remove the user's untitled+empty documents (keeping any id sent as `keep`).

    Cleans up the backlog created by the old client, which saved a blank
    document on every page load.
    """
    try:
        current_user, auth_response = _get_current_user_response(request, db)
        if auth_response:
            return auth_response

        try:
            data = await request.json()
        except Exception:
            data = {}
        keep = data.get("keep")

        documents = Document.get_by_user_id(db, current_user.id)
        removed = []
        for document in documents:
            if document.id == keep:
                continue
            if _is_default_title(document.title) and _is_blank_content(document.content):
                removed.append(document.id)
                db.delete(document)

        if removed:
            db.commit()
            for doc_id in removed:
                _publish(current_user.id, {"type": "doc-delete", "id": doc_id})
            logger.info(f"Pruned {len(removed)} empty documents for user {current_user.id}")

        return JSONResponse({"success": True, "removed": len(removed), "ids": removed})
    except Exception as e:
        logger.error(f"Error pruning empty documents: {e}")
        db.rollback()
        return JSONResponse({"error": "Failed to prune documents"}, status_code=500)


@router.get("/events")
async def document_events_route(request: Request, db: Session = Depends(get_db)):
    """Server-sent events stream of this user's document changes.

    Lets a document typed in one tab/device update live in every other open
    page. Clients ignore events carrying their own client_id.
    """
    current_user, auth_response = _get_current_user_response(request, db)
    if auth_response:
        return auth_response

    user_id = str(current_user.id)
    queue: asyncio.Queue = asyncio.Queue(maxsize=_SSE_QUEUE_SIZE)
    _subscribers.setdefault(user_id, set()).add(queue)

    async def event_stream():
        try:
            yield b": connected\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20.0)
                except asyncio.TimeoutError:
                    yield b": keepalive\n\n"
                    continue
                yield f"data: {json.dumps(payload)}\n\n".encode("utf-8")
        except asyncio.CancelledError:
            raise
        finally:
            queues = _subscribers.get(user_id)
            if queues:
                queues.discard(queue)
                if not queues:
                    _subscribers.pop(user_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
