from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import json
import logging
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import IntegrityError

from questions.db_models_postgres import CancellationSurvey, EmailOptout, SessionLocal, User, WinbackSend, get_db

logger = logging.getLogger(__name__)

EMAILS_DIR = Path(__file__).parent.parent / "emails"
BASE_URL = "https://text-generator.io"
INTERVAL_SECONDS = 6 * 3600
MIN_GAP = timedelta(hours=20)
LEASE = timedelta(minutes=30)
LOCK_KEY = 7340211
LOCK_FILE = os.getenv("WINBACK_LOCK_FILE", os.path.join(tempfile.gettempdir(), "textgen_winback.lock"))
router = APIRouter()


def _secret() -> Optional[bytes]:
    s = os.getenv("WINBACK_UNSUBSCRIBE_SECRET") or os.getenv("STRIPE_WEBHOOK_SECRET")
    return s.encode() if s else None


def make_token(email: str) -> Optional[str]:
    key = _secret()
    if not key:
        return None
    body = base64.urlsafe_b64encode(email.strip().lower().encode()).decode().rstrip("=")
    sig = hmac.new(key, body.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{body}.{sig}"


def verify_token(token: str) -> Optional[str]:
    key = _secret()
    if not key or not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(hmac.new(key, body.encode(), hashlib.sha256).hexdigest()[:32], sig):
        return None
    try:
        return base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)).decode()
    except Exception:
        return None


def unsubscribe_url(email: str) -> Optional[str]:
    t = make_token(email)
    return f"{BASE_URL}/api/winback/unsubscribe?token={t}" if t else None


def is_opted_out(db, email: str) -> bool:
    return db.query(EmailOptout).filter(EmailOptout.email == email.strip().lower()).first() is not None


def record_optout(db, email: str) -> None:
    email = email.strip().lower()
    if is_opted_out(db, email):
        return
    db.add(EmailOptout(email=email))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def _page(msg: str) -> HTMLResponse:
    return HTMLResponse(
        "<html><body style='font-family:sans-serif;text-align:center;padding:60px;'>"
        f"<h2>{msg}</h2><p><a href='https://text-generator.io'>Back to Text Generator</a></p></body></html>"
    )


@router.get("/api/winback/unsubscribe")
async def winback_unsubscribe_get(token: str, db=Depends(get_db)):
    email = verify_token(token)
    if not email:
        return HTMLResponse("Invalid link", status_code=400)
    record_optout(db, email)
    return _page("You've been unsubscribed")


@router.post("/api/winback/unsubscribe")
async def winback_unsubscribe_post(request: Request, db=Depends(get_db)):
    token = request.query_params.get("token")
    if not token:
        form = await request.form()
        token = str(form.get("token", ""))
    email = verify_token(token)
    if not email:
        return JSONResponse({"error": "invalid token"}, status_code=400)
    record_optout(db, email)
    return JSONResponse({"status": "unsubscribed"})


def claim_send(db, email: str, step: int, now: Optional[datetime] = None) -> str:
    now = now or datetime.utcnow()
    email = email.strip().lower()
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    stmt = insert(WinbackSend).values(email=email, step=step, status="sending", claimed_at=now).on_conflict_do_nothing(
        index_elements=["email", "step"]
    )
    res = db.execute(stmt)
    db.commit()
    if res.rowcount == 1:
        return "claimed"
    res = db.query(WinbackSend).filter(
        WinbackSend.email == email,
        WinbackSend.step == step,
        WinbackSend.status == "sending",
        WinbackSend.sent_at.is_(None),
        WinbackSend.claimed_at < now - LEASE,
    ).update({"claimed_at": now}, synchronize_session=False)
    db.commit()
    if res == 1:
        return "claimed"
    row = db.query(WinbackSend).filter(WinbackSend.email == email, WinbackSend.step == step).first()
    return "sent" if row is not None and row.status == "sent" else "busy"


def mark_sent(db, email: str, step: int, now: datetime) -> None:
    db.query(WinbackSend).filter(WinbackSend.email == email.strip().lower(), WinbackSend.step == step).update(
        {"status": "sent", "sent_at": now}, synchronize_session=False
    )
    db.commit()


@contextlib.contextmanager
def scheduler_lock(db=None):
    if db is not None and db.get_bind().dialect.name == "postgresql":
        from sqlalchemy import text

        conn = db.get_bind().connect()
        try:
            got = bool(conn.execute(text("select pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}).scalar())
            try:
                yield got
            finally:
                if got:
                    conn.execute(text("select pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
        finally:
            conn.close()
        return
    import fcntl

    fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def enabled() -> bool:
    return os.getenv("TEXTGEN_WINBACK_ENABLED", "0") == "1"


def load_config() -> dict:
    return json.loads((EMAILS_DIR / "winback_config.json").read_text())


def render(html: str, user: User, url: str) -> str:
    name = user.name or user.email.split("@")[0]
    return html.replace("{{.Name}}", name).replace("{{.Email}}", user.email).replace("{{.UnsubscribeURL}}", url)


def due_index(row: CancellationSurvey, emails: list, now: datetime) -> Optional[int]:
    if row.winback_stopped or row.cancel_at is None:
        return None
    idx = row.winback_sent or 0
    if idx >= len(emails):
        return None
    if now < row.cancel_at + timedelta(days=emails[idx]["delay_days"]):
        return None
    if row.winback_last_sent_at and now - row.winback_last_sent_at < MIN_GAP:
        return None
    return idx


def _resubscribed(user: User) -> bool:
    from questions.subscription_utils import check_user_subscription

    return bool(check_user_subscription(user))


def run_winback(
    dry_run: bool = True,
    now: Optional[datetime] = None,
    send: Optional[Callable[[str, str, str, str], None]] = None,
    is_resubscribed: Callable[[User], bool] = _resubscribed,
    db=None,
) -> dict:
    now = now or datetime.utcnow()
    config = load_config()
    emails = config["emails"]
    stats = {"due": 0, "sent": 0, "skipped": 0, "stopped": 0}
    own = db is None
    db = db or SessionLocal()
    try:
        rows = db.query(CancellationSurvey).filter(CancellationSurvey.winback_stopped.is_(False)).all()
        for row in rows:
            if row.cancel_at is None or now < row.cancel_at:
                continue
            idx = due_index(row, emails, now)
            if idx is None:
                continue
            if is_opted_out(db, row.email):
                row.winback_stopped = True
                stats["stopped"] += 1
                continue
            user = db.query(User).filter(User.email == row.email).first()
            if user is None or user.email_unsubscribed:
                row.winback_stopped = True
                stats["stopped"] += 1
                continue
            if is_resubscribed(user):
                row.winback_stopped = True
                stats["stopped"] += 1
                continue
            stats["due"] += 1
            if dry_run:
                continue
            unsub = unsubscribe_url(user.email)
            if unsub is None:
                logger.error("winback unsubscribe secret missing; not sending")
                stats["skipped"] += 1
                continue
            if send is None:
                from questions.drip_email import send_drip_email

                send_fn = send_drip_email
            else:
                send_fn = send
            claim = claim_send(db, user.email, idx, now)
            if claim == "sent":
                row.winback_sent = idx + 1
                row.winback_last_sent_at = now
                db.commit()
                continue
            if claim != "claimed":
                stats["skipped"] += 1
                continue
            entry = emails[idx]
            html = render((EMAILS_DIR / entry["template"]).read_text(), user, unsub)
            try:
                send_fn(user.email, entry["subject"], html, unsub)
            except Exception:
                logger.exception("winback send failed for %s", user.email)
                stats["skipped"] += 1
                continue
            mark_sent(db, user.email, idx, now)
            row.winback_sent = idx + 1
            row.winback_last_sent_at = now
            db.commit()
            stats["sent"] += 1
        db.commit()
    finally:
        if own:
            db.close()
    return stats


def _loop() -> None:
    while True:
        try:
            if enabled():
                db = SessionLocal()
                try:
                    with scheduler_lock(db) as got:
                        if got:
                            try:
                                from questions.cancel_flow import reconcile_cancellations

                                logger.info("winback reconciled: %s", reconcile_cancellations(db))
                            except Exception:
                                logger.exception("cancellation reconcile failed")
                                db.rollback()
                            logger.info("winback run: %s", run_winback(dry_run=False, db=db))
                finally:
                    db.close()
        except Exception:
            logger.exception("winback loop error")
        time.sleep(INTERVAL_SECONDS)


def start_scheduler() -> bool:
    if not enabled():
        return False
    threading.Thread(target=_loop, name="winback", daemon=True).start()
    return True


if __name__ == "__main__":
    import sys

    print(run_winback(dry_run="--send" not in sys.argv or not enabled()))
