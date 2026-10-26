"""
Drip email campaign sender for text-generator.io.

Usage:
    # Send pending drip emails for all eligible users
    python -m questions.drip_email

    # Dry run (print what would be sent)
    python -m questions.drip_email --dry-run

    # Send a specific email to a specific user (for testing)
    python -m questions.drip_email --test-email user@example.com --email-index 1
"""

import json
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from sellerinfo import AWS_SMTP_PASSWORD, AWS_SMTP_USERNAME, AWS_REGION, FROM_EMAIL

from questions.db_models_postgres import SessionLocal, User

SMTP_HOST = f"email-smtp.{AWS_REGION}.amazonaws.com"
SMTP_PORT = 587
BASE_URL = "https://text-generator.io"
EMAILS_DIR = Path(__file__).parent.parent / "emails"


def load_drip_config():
    with open(EMAILS_DIR / "drip_config.json") as f:
        return json.load(f)


def load_email_template(template_name: str) -> str:
    with open(EMAILS_DIR / template_name) as f:
        return f.read()


def ensure_unsubscribe_token(db, user: User) -> str:
    """Ensure user has an unsubscribe token, create one if missing."""
    if not user.email_unsubscribe_token:
        user.email_unsubscribe_token = secrets.token_urlsafe(32)
        db.commit()
    return user.email_unsubscribe_token


def render_email(html: str, user: User, unsubscribe_token: str) -> str:
    """Replace template variables in email HTML."""
    name = user.name or user.email.split("@")[0]
    unsubscribe_url = f"{BASE_URL}/api/email/unsubscribe?token={unsubscribe_token}"
    html = html.replace("{{.Name}}", name)
    html = html.replace("{{.Email}}", user.email)
    html = html.replace("{{.UnsubscribeURL}}", unsubscribe_url)
    return html


def send_drip_email(to_email: str, subject: str, html_body: str, unsubscribe_url: str):
    """Send a single drip email with proper unsubscribe headers."""
    text_body = f"View this email in your browser. Unsubscribe: {unsubscribe_url}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Text Generator <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(AWS_SMTP_USERNAME, AWS_SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())


def get_eligible_users(db):
    """Get users who should receive their next drip email."""
    return (
        db.query(User)
        .filter(
            User.email_unsubscribed != True,  # noqa: E712
            User.email.isnot(None),
        )
        .all()
    )


def should_send_next_email(user: User, email_config: dict) -> bool:
    """Check if enough time has passed to send the next drip email."""
    if user.email_unsubscribed:
        return False

    emails = email_config["emails"]
    next_index = (user.drip_email_sent or 0)

    if next_index >= len(emails):
        return False  # all emails sent

    next_email = emails[next_index]
    delay_days = next_email["delay_days"]

    # For the first email (day 0), send immediately if none sent yet
    if next_index == 0 and (user.drip_email_sent or 0) == 0:
        return True

    # Check if enough days have passed since account creation
    if not user.created:
        return False

    target_date = user.created + timedelta(days=delay_days)
    now = datetime.utcnow()

    # Don't send if we haven't reached the target date
    if now < target_date:
        return False

    # Don't send more than one email per day
    if user.drip_email_last_sent_at:
        if now - user.drip_email_last_sent_at < timedelta(hours=20):
            return False

    return True


def run_drip_campaign(dry_run=False):
    """Send pending drip emails for all eligible users."""
    config = load_drip_config()
    emails = config["emails"]
    db = SessionLocal()

    try:
        users = get_eligible_users(db)
        sent_count = 0
        skip_count = 0

        for user in users:
            next_index = user.drip_email_sent or 0

            if next_index >= len(emails):
                continue

            if not should_send_next_email(user, config):
                skip_count += 1
                continue

            email_def = emails[next_index]
            token = ensure_unsubscribe_token(db, user)
            unsubscribe_url = f"{BASE_URL}/api/email/unsubscribe?token={token}"

            template_html = load_email_template(email_def["template"])
            rendered = render_email(template_html, user, token)

            if dry_run:
                print(f"  [DRY RUN] Would send #{email_def['id']} '{email_def['subject']}' to {user.email}")
            else:
                try:
                    send_drip_email(user.email, email_def["subject"], rendered, unsubscribe_url)
                    user.drip_email_sent = next_index + 1
                    user.drip_email_last_sent_at = datetime.utcnow()
                    db.commit()
                    print(f"  Sent #{email_def['id']} to {user.email}")
                except Exception as e:
                    print(f"  ERROR sending to {user.email}: {e}")
                    db.rollback()

            sent_count += 1

        print(f"\nDrip run complete: {sent_count} sent, {skip_count} skipped")
    finally:
        db.close()


def send_test_email(email: str, email_index: int):
    """Send a specific drip email to a specific address for testing."""
    config = load_drip_config()
    emails = config["emails"]

    if email_index < 1 or email_index > len(emails):
        print(f"Invalid email index {email_index}. Must be 1-{len(emails)}")
        return

    email_def = emails[email_index - 1]
    template_html = load_email_template(email_def["template"])
    token = "test-token-preview"
    unsubscribe_url = f"{BASE_URL}/api/email/unsubscribe?token={token}"

    # Simple substitution for test
    rendered = template_html.replace("{{.Name}}", "Test User")
    rendered = rendered.replace("{{.Email}}", email)
    rendered = rendered.replace("{{.UnsubscribeURL}}", unsubscribe_url)

    send_drip_email(email, email_def["subject"], rendered, unsubscribe_url)
    print(f"Sent test email #{email_index} '{email_def['subject']}' to {email}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Text Generator drip email campaign")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be sent without sending")
    parser.add_argument("--test-email", type=str, help="Send a test email to this address")
    parser.add_argument("--email-index", type=int, default=1, help="Which email to send (1-20)")
    args = parser.parse_args()

    if args.test_email:
        send_test_email(args.test_email, args.email_index)
    else:
        run_drip_campaign(dry_run=args.dry_run)
