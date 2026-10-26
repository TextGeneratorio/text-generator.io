"""FastAPI router for the agent system.

Endpoints:
- /api/chat           — Multi-turn chat with tool calling
- /api/batch          — Batch prompt processing
- /api/tools          — List/manage tools
- /api/skills         — CRUD for skills
- /api/cron           — CRUD for scheduled jobs
- /api/keys           — BYOK key management
- /api/delegate       — Subagent delegation
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from questions.agent import models as m

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


def _get_db():
    """Get database session — imported dynamically to avoid circular imports."""
    from questions.db_models_postgres import get_db

    return get_db


def _get_user(secret: Optional[str] = Header(None), db: Session = Depends(_get_db())):
    """Authenticate user by secret header."""
    if not secret:
        raise HTTPException(status_code=401, detail="Missing 'secret' header")

    from questions.db_models_postgres import User

    user = User.get_by_secret(db, secret)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid secret")
    return user


# ---- Tools ----


@router.get("/tools")
def list_tools():
    """List all registered tools and their availability."""
    # Import tools to trigger registration
    _ensure_tools_registered()
    from questions.agent.registry import registry

    return {
        "tools": registry.list_tools(),
        "toolsets": registry.list_toolsets(),
    }


@router.get("/tools/{tool_name}")
def get_tool(tool_name: str):
    """Get details for a specific tool."""
    _ensure_tools_registered()
    from questions.agent.registry import registry

    entry = registry.get(tool_name)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return {
        "name": entry.name,
        "toolset": entry.toolset,
        "description": entry.description,
        "schema": entry.schema,
        "requires_byok": entry.requires_byok,
        "available": entry.check_fn() if entry.check_fn else True,
    }


# ---- BYOK Keys ----


@router.get("/keys")
def list_keys(user=Depends(_get_user), db: Session = Depends(_get_db())):
    """List user's API keys (no secrets exposed)."""
    from questions.agent.byok import list_keys

    return {"keys": list_keys(db, user.id)}


@router.post("/keys")
def add_key(req: m.AddAPIKeyRequest, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Add or replace an API key for a provider."""
    from questions.agent.byok import add_key

    try:
        result = add_key(db, user.id, req.provider, req.api_key)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/keys/{key_id}")
def revoke_key(key_id: str, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Revoke an API key."""
    from questions.agent.byok import revoke_key

    if not revoke_key(db, user.id, key_id):
        raise HTTPException(status_code=404, detail="Key not found")
    return {"status": "revoked"}


# ---- Skills ----


@router.get("/skills")
def list_skills(
    category: Optional[str] = None,
    user=Depends(_get_user),
    db: Session = Depends(_get_db()),
):
    """List available skills (bundled + user's own + public)."""
    from questions.agent.skill_manager import list_skills

    return {"skills": list_skills(db, user_id=user.id, category=category)}


@router.get("/skills/{skill_id}")
def get_skill(skill_id: str, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Get full skill content."""
    from questions.agent.skill_manager import get_skill

    skill = get_skill(db, skill_id, user_id=user.id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/skills")
def create_skill(req: m.SkillCreate, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Create a new skill."""
    from questions.agent.skill_manager import create_skill

    return create_skill(db, user.id, req.model_dump())


@router.put("/skills/{skill_id}")
def update_skill(
    skill_id: str,
    req: m.SkillUpdate,
    user=Depends(_get_user),
    db: Session = Depends(_get_db()),
):
    """Update a skill."""
    from questions.agent.skill_manager import update_skill

    result = update_skill(db, skill_id, user.id, req.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Skill not found or not owned by you")
    return result


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: str, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Delete a skill."""
    from questions.agent.skill_manager import delete_skill

    if not delete_skill(db, skill_id, user.id):
        raise HTTPException(status_code=404, detail="Skill not found or not owned by you")
    return {"status": "deleted"}


# ---- Cron ----


@router.get("/cron")
def list_cron_jobs(user=Depends(_get_user), db: Session = Depends(_get_db())):
    """List user's cron jobs."""
    from questions.agent.scheduler import list_jobs

    return {"jobs": list_jobs(db, user.id)}


@router.post("/cron")
def create_cron_job(req: m.CronJobCreate, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Create a new cron job."""
    from questions.agent.scheduler import create_job

    try:
        return create_job(db, user.id, req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/cron/{job_id}")
def update_cron_job(
    job_id: str,
    req: m.CronJobUpdate,
    user=Depends(_get_user),
    db: Session = Depends(_get_db()),
):
    """Update a cron job."""
    from questions.agent.scheduler import update_job

    result = update_job(db, job_id, user.id, req.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.delete("/cron/{job_id}")
def delete_cron_job(job_id: str, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Delete a cron job."""
    from questions.agent.scheduler import delete_job

    if not delete_job(db, job_id, user.id):
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "deleted"}


# ---- Chat ----


@router.post("/chat")
async def chat(req: m.ChatRequest, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Multi-turn chat with optional tool calling.

    Supports BYOK — if user has stored keys for the requested provider,
    those keys are used. Otherwise falls back to platform keys.
    """
    _ensure_tools_registered()
    from questions.agent.byok import get_key
    from questions.agent.chat import chat_with_tools
    from questions.agent.skill_manager import get_skill

    # Resolve API key: BYOK > platform key
    api_key = None
    if req.provider:
        api_key = get_key(db, user.id, req.provider)

    # Load skill content if requested
    skill_content = None
    if req.skill_ids:
        skill_parts = []
        for sid in req.skill_ids:
            skill = get_skill(db, sid, user_id=user.id)
            if skill and skill.get("content"):
                skill_parts.append(skill["content"])
        if skill_parts:
            skill_content = "\n\n---\n\n".join(skill_parts)

    messages = [msg.model_dump() for msg in req.messages]

    result = await chat_with_tools(
        messages=messages,
        model=req.model,
        provider=req.provider,
        api_key=api_key,
        tools_enabled=req.tools_enabled,
        skill_content=skill_content,
        system_prompt=req.system_prompt,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        db=db,
        user_id=user.id,
    )

    return result


# ---- Batch ----


@router.post("/batch")
async def batch(req: m.BatchRequest, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Process multiple prompts in a batch.

    Requires BYOK for the requested provider to control costs.
    """
    from questions.agent.batch import process_batch
    from questions.agent.byok import get_key

    api_key = None
    if req.provider:
        api_key = get_key(db, user.id, req.provider)

    prompts = [p.model_dump() for p in req.prompts]

    result = await process_batch(
        db=db,
        user_id=user.id,
        prompts=prompts,
        model=req.model,
        api_key=api_key,
    )
    return result


@router.get("/batch/{batch_id}")
def get_batch_status(batch_id: str, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Get batch job status."""
    from questions.agent.batch import get_batch_status

    result = get_batch_status(db, batch_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return result


# ---- Delegate ----


@router.post("/delegate")
async def delegate(req: m.DelegateRequest, user=Depends(_get_user), db: Session = Depends(_get_db())):
    """Spawn a focused subagent to handle a specific task."""
    _ensure_tools_registered()
    from questions.agent.byok import get_key
    from questions.agent.chat import call_llm
    from questions.agent.delegate import run_subagent

    api_key = None
    if req.provider:
        api_key = get_key(db, user.id, req.provider)

    async def chat_fn(messages, tools=None, max_tokens=2048):
        return await call_llm(
            messages=messages,
            model=req.model,
            api_key=api_key,
            tools=tools,
            max_tokens=max_tokens,
        )

    result = await run_subagent(
        goal=req.goal,
        context=req.context,
        chat_fn=chat_fn,
        tools_enabled=req.tools_enabled,
        max_iterations=req.max_iterations,
    )
    return result


# ---- Internal helpers ----

_tools_registered = False


def _ensure_tools_registered():
    """Import tool modules to trigger self-registration."""
    global _tools_registered
    if _tools_registered:
        return
    try:
        import questions.agent.tools.calculator  # noqa: F401
        import questions.agent.tools.summarize  # noqa: F401
        import questions.agent.tools.text_generate  # noqa: F401
        import questions.agent.tools.web_search  # noqa: F401
    except ImportError as e:
        logger.warning(f"Failed to import some tools: {e}")
    _tools_registered = True
