"""Cron scheduler — background job execution for scheduled agent tasks.

Supports cron expressions (e.g., '0 9 * * *'), intervals ('every 30m'),
and one-shot schedules ('once 2026-04-01T09:00').
"""

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def parse_schedule(schedule: str) -> Tuple[str, Optional[datetime]]:
    """Parse a schedule string into (schedule_type, next_run_at).

    Returns:
        (schedule_type, next_run_at) where schedule_type is 'cron', 'interval', or 'once'
    """
    schedule = schedule.strip()
    now = datetime.now(timezone.utc)

    # Interval: "every 30m", "every 2h", "every 1d"
    interval_match = re.match(r"every\s+(\d+)\s*(m|min|h|hour|d|day)s?", schedule, re.IGNORECASE)
    if interval_match:
        amount = int(interval_match.group(1))
        unit = interval_match.group(2).lower()
        if unit in ("m", "min"):
            delta = timedelta(minutes=amount)
        elif unit in ("h", "hour"):
            delta = timedelta(hours=amount)
        elif unit in ("d", "day"):
            delta = timedelta(days=amount)
        else:
            delta = timedelta(minutes=amount)
        return "interval", now + delta

    # One-shot: ISO timestamp
    if schedule.startswith("once ") or "T" in schedule:
        ts_str = schedule.replace("once ", "").strip()
        try:
            run_at = datetime.fromisoformat(ts_str)
            if run_at.tzinfo is None:
                run_at = run_at.replace(tzinfo=timezone.utc)
            return "once", run_at
        except ValueError:
            pass

    # Cron expression: validate it has 5 fields
    parts = schedule.split()
    if len(parts) == 5:
        # Basic cron validation — we'll compute next_run from the expression later
        return "cron", _next_cron_run(schedule, now)

    raise ValueError(
        f"Invalid schedule: '{schedule}'. "
        "Use cron ('0 9 * * *'), interval ('every 30m'), or ISO timestamp."
    )


def _next_cron_run(expr: str, after: datetime) -> datetime:
    """Compute the next run time for a simple cron expression.

    Supports: minute hour day_of_month month day_of_week
    Only handles * and literal values (no ranges/steps for simplicity).
    """
    parts = expr.split()
    if len(parts) != 5:
        return after + timedelta(hours=1)

    minute, hour, dom, month, dow = parts

    # Simple case: fixed hour and minute, wildcard for rest
    try:
        target_min = int(minute) if minute != "*" else None
        target_hour = int(hour) if hour != "*" else None
    except ValueError:
        return after + timedelta(hours=1)

    candidate = after.replace(second=0, microsecond=0)

    # Search forward up to 48 hours for next match
    for _ in range(2880):  # 48h in minutes
        candidate += timedelta(minutes=1)
        if target_min is not None and candidate.minute != target_min:
            continue
        if target_hour is not None and candidate.hour != target_hour:
            continue
        if dom != "*":
            try:
                if candidate.day != int(dom):
                    continue
            except ValueError:
                pass
        if dow != "*":
            try:
                if candidate.weekday() != (int(dow) % 7):
                    continue
            except ValueError:
                pass
        return candidate

    return after + timedelta(hours=1)


def create_job(db: Session, user_id: str, data: dict) -> dict:
    """Create a new cron job."""
    from questions.db_models_postgres import CronJob

    schedule_type, next_run = parse_schedule(data["schedule"])

    job = CronJob(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=data["name"],
        prompt=data["prompt"],
        schedule=data["schedule"],
        schedule_type=schedule_type,
        skill_ids=data.get("skill_ids"),
        tool_ids=data.get("tool_ids"),
        max_iterations=data.get("max_iterations", 10),
        next_run_at=next_run,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.to_dict()


def list_jobs(db: Session, user_id: str) -> List[dict]:
    """List all cron jobs for a user."""
    from questions.db_models_postgres import CronJob

    jobs = db.query(CronJob).filter_by(user_id=user_id).order_by(CronJob.created_at.desc()).all()
    return [j.to_dict() for j in jobs]


def get_job(db: Session, job_id: str, user_id: str) -> Optional[dict]:
    """Get a specific cron job."""
    from questions.db_models_postgres import CronJob

    job = db.query(CronJob).filter_by(id=job_id, user_id=user_id).first()
    return job.to_dict() if job else None


def update_job(db: Session, job_id: str, user_id: str, data: dict) -> Optional[dict]:
    """Update a cron job."""
    from questions.db_models_postgres import CronJob

    job = db.query(CronJob).filter_by(id=job_id, user_id=user_id).first()
    if not job:
        return None

    if "schedule" in data and data["schedule"]:
        schedule_type, next_run = parse_schedule(data["schedule"])
        job.schedule = data["schedule"]
        job.schedule_type = schedule_type
        job.next_run_at = next_run

    for field in ("name", "prompt", "is_active", "max_iterations"):
        if field in data and data[field] is not None:
            setattr(job, field, data[field])

    db.commit()
    db.refresh(job)
    return job.to_dict()


def delete_job(db: Session, job_id: str, user_id: str) -> bool:
    """Delete a cron job."""
    from questions.db_models_postgres import CronJob

    job = db.query(CronJob).filter_by(id=job_id, user_id=user_id).first()
    if not job:
        return False
    db.delete(job)
    db.commit()
    return True


def get_due_jobs(db: Session) -> List:
    """Get all active jobs that are due to run."""
    from questions.db_models_postgres import CronJob

    now = datetime.now(timezone.utc)
    return (
        db.query(CronJob)
        .filter(CronJob.is_active == True, CronJob.next_run_at <= now)  # noqa: E712
        .all()
    )


def mark_job_run(db: Session, job_id: str, output: Optional[str] = None, error: Optional[str] = None) -> None:
    """Mark a job as having run and compute next_run_at."""
    from questions.db_models_postgres import CronJob

    job = db.query(CronJob).filter_by(id=job_id).first()
    if not job:
        return

    now = datetime.now(timezone.utc)
    job.last_run_at = now
    job.run_count = (job.run_count or 0) + 1
    job.last_output = output
    job.last_error = error

    if job.schedule_type == "once":
        job.is_active = False
        job.next_run_at = None
    elif job.schedule_type == "interval":
        _, next_run = parse_schedule(job.schedule)
        job.next_run_at = next_run
    elif job.schedule_type == "cron":
        job.next_run_at = _next_cron_run(job.schedule, now)

    db.commit()
