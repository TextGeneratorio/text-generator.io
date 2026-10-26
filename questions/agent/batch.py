"""Batch processing — run multiple prompts concurrently with rate limiting.

Designed for cost-conscious batch operations. Limits concurrency and
tracks estimated costs.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from questions.agent.chat import call_llm

logger = logging.getLogger(__name__)

# Batch limits
MAX_BATCH_SIZE = 50
MAX_CONCURRENT = 5  # Process at most 5 prompts concurrently


async def process_batch(
    db: Session,
    user_id: str,
    prompts: List[Dict[str, Any]],
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Process a batch of prompts concurrently.

    Args:
        db: Database session
        user_id: User ID
        prompts: List of prompt dicts with 'prompt', 'system_prompt', 'max_tokens', 'temperature'
        model: Model to use
        api_key: BYOK API key

    Returns:
        Batch job result with all responses
    """
    from questions.db_models_postgres import BatchJob

    if len(prompts) > MAX_BATCH_SIZE:
        raise ValueError(f"Batch size exceeds maximum of {MAX_BATCH_SIZE}")

    batch_id = str(uuid.uuid4())
    batch_job = BatchJob(
        id=batch_id,
        user_id=user_id,
        status="running",
        total_prompts=len(prompts),
        model=model,
    )
    db.add(batch_job)
    db.commit()

    results = [None] * len(prompts)
    errors = {}
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def process_one(index: int, prompt_data: dict):
        async with semaphore:
            prompt_text = prompt_data.get("prompt", "")
            system_prompt = prompt_data.get("system_prompt")
            max_tokens = prompt_data.get("max_tokens", 1024)
            temperature = prompt_data.get("temperature", 0.7)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt_text})

            try:
                response = await call_llm(
                    messages=messages,
                    model=model,
                    api_key=api_key,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                choice = response.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                results[index] = {
                    "index": index,
                    "prompt": prompt_text,
                    "response": content,
                    "usage": response.get("usage"),
                }
            except Exception as e:
                logger.exception(f"Batch item {index} failed")
                errors[str(index)] = str(e)
                results[index] = {
                    "index": index,
                    "prompt": prompt_text,
                    "response": None,
                    "error": str(e),
                }

    # Run all prompts with concurrency limit
    tasks = [process_one(i, p) for i, p in enumerate(prompts)]
    await asyncio.gather(*tasks, return_exceptions=True)

    # Update batch job
    completed = sum(1 for r in results if r and r.get("response") is not None)
    failed = sum(1 for r in results if r and r.get("error") is not None)

    batch_job = db.query(BatchJob).filter_by(id=batch_id).first()
    if batch_job:
        batch_job.status = "completed"
        batch_job.completed_prompts = completed
        batch_job.failed_prompts = failed
        batch_job.results = results
        batch_job.errors = errors if errors else None
        batch_job.completed_at = datetime.now(timezone.utc)
        db.commit()

    return {
        "batch_id": batch_id,
        "status": "completed",
        "total_prompts": len(prompts),
        "completed_prompts": completed,
        "failed_prompts": failed,
        "results": results,
    }


def get_batch_status(db: Session, batch_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get the status of a batch job."""
    from questions.db_models_postgres import BatchJob

    job = db.query(BatchJob).filter_by(id=batch_id, user_id=user_id).first()
    if not job:
        return None
    return job.to_dict()
