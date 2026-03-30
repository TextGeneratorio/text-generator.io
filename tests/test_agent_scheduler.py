"""Tests for the cron scheduler system."""

from datetime import datetime, timedelta, timezone

import pytest

from questions.agent.scheduler import (
    _next_cron_run,
    create_job,
    delete_job,
    get_due_jobs,
    get_job,
    list_jobs,
    mark_job_run,
    parse_schedule,
    update_job,
)
from questions.db_models_postgres import Base, CronJob, User


@pytest.fixture(scope="module")
def db_engine():
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    session = Session()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        id="cron_test_user",
        email="cron@test.com",
        name="Cron Tester",
        secret="cron_test_secret",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestScheduleParsing:
    def test_parse_interval_minutes(self):
        stype, next_run = parse_schedule("every 30m")
        assert stype == "interval"
        assert next_run is not None
        assert next_run > datetime.now(timezone.utc)

    def test_parse_interval_hours(self):
        stype, next_run = parse_schedule("every 2h")
        assert stype == "interval"
        now = datetime.now(timezone.utc)
        assert next_run > now + timedelta(hours=1)

    def test_parse_interval_days(self):
        stype, next_run = parse_schedule("every 1d")
        assert stype == "interval"

    def test_parse_cron_expression(self):
        stype, next_run = parse_schedule("0 9 * * *")
        assert stype == "cron"
        assert next_run is not None

    def test_parse_once_iso(self):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        stype, next_run = parse_schedule(f"once {future.isoformat()}")
        assert stype == "once"
        assert next_run is not None

    def test_parse_invalid_schedule(self):
        with pytest.raises(ValueError, match="Invalid schedule"):
            parse_schedule("not a valid schedule at all")

    def test_parse_cron_five_fields(self):
        stype, _ = parse_schedule("30 14 * * 1")
        assert stype == "cron"


class TestNextCronRun:
    def test_fixed_time(self):
        now = datetime(2026, 3, 30, 10, 0, 0, tzinfo=timezone.utc)
        next_run = _next_cron_run("0 12 * * *", now)
        assert next_run.hour == 12
        assert next_run.minute == 0

    def test_wildcard_minute(self):
        now = datetime(2026, 3, 30, 10, 0, 0, tzinfo=timezone.utc)
        next_run = _next_cron_run("* 11 * * *", now)
        assert next_run.hour == 11

    def test_all_wildcards(self):
        now = datetime(2026, 3, 30, 10, 0, 0, tzinfo=timezone.utc)
        next_run = _next_cron_run("* * * * *", now)
        assert next_run > now


class TestCronJobCRUD:
    def test_create_job(self, db_session, test_user):
        result = create_job(
            db_session,
            test_user.id,
            {
                "name": "Daily report",
                "prompt": "Generate a daily report",
                "schedule": "0 9 * * *",
            },
        )
        assert result["name"] == "Daily report"
        assert result["schedule_type"] == "cron"
        assert result["is_active"] is True
        assert result["next_run_at"] is not None

    def test_create_interval_job(self, db_session, test_user):
        result = create_job(
            db_session,
            test_user.id,
            {
                "name": "Frequent check",
                "prompt": "Check status",
                "schedule": "every 30m",
            },
        )
        assert result["schedule_type"] == "interval"

    def test_list_jobs(self, db_session, test_user):
        create_job(
            db_session,
            test_user.id,
            {"name": "Job A", "prompt": "Do A", "schedule": "every 1h"},
        )
        create_job(
            db_session,
            test_user.id,
            {"name": "Job B", "prompt": "Do B", "schedule": "every 2h"},
        )
        jobs = list_jobs(db_session, test_user.id)
        assert len(jobs) >= 2

    def test_get_job(self, db_session, test_user):
        created = create_job(
            db_session,
            test_user.id,
            {"name": "Get test", "prompt": "Test", "schedule": "every 1h"},
        )
        retrieved = get_job(db_session, created["id"], test_user.id)
        assert retrieved is not None
        assert retrieved["name"] == "Get test"

    def test_get_job_wrong_user(self, db_session, test_user):
        created = create_job(
            db_session,
            test_user.id,
            {"name": "Private", "prompt": "Test", "schedule": "every 1h"},
        )
        assert get_job(db_session, created["id"], "other_user") is None

    def test_update_job(self, db_session, test_user):
        created = create_job(
            db_session,
            test_user.id,
            {"name": "Update me", "prompt": "Old", "schedule": "every 1h"},
        )
        updated = update_job(
            db_session,
            created["id"],
            test_user.id,
            {"name": "Updated", "prompt": "New prompt"},
        )
        assert updated["name"] == "Updated"

    def test_update_schedule(self, db_session, test_user):
        created = create_job(
            db_session,
            test_user.id,
            {"name": "Reschedule", "prompt": "Test", "schedule": "every 1h"},
        )
        updated = update_job(
            db_session,
            created["id"],
            test_user.id,
            {"schedule": "every 30m"},
        )
        assert updated["schedule_type"] == "interval"

    def test_delete_job(self, db_session, test_user):
        created = create_job(
            db_session,
            test_user.id,
            {"name": "Delete me", "prompt": "Doomed", "schedule": "every 1h"},
        )
        assert delete_job(db_session, created["id"], test_user.id) is True
        assert get_job(db_session, created["id"], test_user.id) is None

    def test_delete_nonexistent(self, db_session, test_user):
        assert delete_job(db_session, "fake-id", test_user.id) is False


class TestJobExecution:
    def test_mark_job_run_interval(self, db_session, test_user):
        created = create_job(
            db_session,
            test_user.id,
            {"name": "Run test", "prompt": "Run", "schedule": "every 1h"},
        )
        mark_job_run(db_session, created["id"], output="done", error=None)

        updated = get_job(db_session, created["id"], test_user.id)
        assert updated["run_count"] == 1
        assert updated["next_run_at"] is not None  # Rescheduled

    def test_mark_job_run_once_deactivates(self, db_session, test_user):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        created = create_job(
            db_session,
            test_user.id,
            {"name": "One shot", "prompt": "Once", "schedule": f"once {future.isoformat()}"},
        )
        mark_job_run(db_session, created["id"], output="done")

        updated = get_job(db_session, created["id"], test_user.id)
        assert updated["is_active"] is False

    def test_get_due_jobs(self, db_session, test_user):
        # Create a job that's already due
        job = CronJob(
            id="due-job",
            user_id=test_user.id,
            name="Due now",
            prompt="Run me",
            schedule="every 1h",
            schedule_type="interval",
            next_run_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        db_session.add(job)
        db_session.commit()

        due = get_due_jobs(db_session)
        due_ids = [j.id for j in due]
        assert "due-job" in due_ids
