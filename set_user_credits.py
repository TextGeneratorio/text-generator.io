#!/usr/bin/env python3
"""Grant credits + subscription to a user by email, optionally setting their secret.

Targets the local dev DB (textgen) by default. To hit prod, either:
    ENVIRONMENT=production DB_HOST=... DB_USER=... DB_PASSWORD=... python3 set_user_credits.py
or supply a full URL:
    DATABASE_URL="postgresql://user:pass@prod-host:5432/textgen_prod" python3 set_user_credits.py

Usage:
    python3 set_user_credits.py                              # dry-run against dev
    python3 set_user_credits.py --apply                      # apply against dev
    python3 set_user_credits.py --email user@x --secret KEY --credits 10000 --apply
"""
from __future__ import annotations

import argparse
import os
import sys

# Defaults come from env so no personal email/secret is committed to source.
# Override per-run with --email / --secret or TARGET_EMAIL / TARGET_SECRET.
TARGET_EMAIL = os.getenv("TARGET_EMAIL", "")
TARGET_SECRET = os.getenv("TARGET_SECRET", "")
TARGET_CREDITS = int(os.getenv("TARGET_CREDITS", "10000"))


def build_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", os.getenv("USER", "lee"))
    password = os.getenv("DB_PASSWORD", "")
    port = os.getenv("DB_PORT", "5432")
    env = os.getenv("ENVIRONMENT", "development")
    db = "textgen_prod" if env == "production" else "textgen"
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return f"postgresql://{user}@/{db}?host=/var/run/postgresql"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default=TARGET_EMAIL)
    parser.add_argument("--secret", default=TARGET_SECRET)
    parser.add_argument("--credits", type=int, default=TARGET_CREDITS)
    parser.add_argument("--apply", action="store_true", help="actually commit the update")
    args = parser.parse_args()

    if not args.email or not args.secret:
        parser.error(
            "--email and --secret are required "
            "(or set TARGET_EMAIL / TARGET_SECRET env vars)"
        )

    from sqlalchemy import create_engine, text

    url = build_url()
    redacted = url.replace(os.getenv("DB_PASSWORD", "__no_pw__"), "***") if os.getenv("DB_PASSWORD") else url
    print(f"→ target db: {redacted}")
    print(f"→ user:      {args.email}")
    print(f"→ secret:    {args.secret[:4]}…{args.secret[-3:]}  (len={len(args.secret)})")
    print(f"→ credits:   at least {args.credits}")
    print(f"→ apply:     {args.apply}")
    print()

    engine = create_engine(url)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, email, is_subscribed, free_credits, secret, stripe_id "
                "FROM users WHERE email = :email"
            ),
            {"email": args.email},
        ).fetchone()

        if not row:
            print(f"✗ user with email {args.email} not found")
            return 2

        user_id, email, is_subscribed, free_credits, current_secret, stripe_id = row
        print(
            f"  current: id={user_id} subscribed={is_subscribed} credits={free_credits} "
            f"secret_matches={current_secret == args.secret} stripe_id={stripe_id}"
        )

        new_credits = max(free_credits or 0, args.credits)
        changes = {
            "is_subscribed": True,
            "free_credits": new_credits,
        }
        if current_secret != args.secret:
            changes["secret"] = args.secret

        print("  changes:", {k: (v if k != "secret" else v[:4] + "…") for k, v in changes.items()})

        if not args.apply:
            print("\n(dry-run — pass --apply to commit)")
            return 0

        stmt = "UPDATE users SET " + ", ".join(f"{k} = :{k}" for k in changes) + " WHERE id = :id"
        params = {**changes, "id": user_id}
        conn.execute(text(stmt), params)
        conn.commit()
        print("✓ committed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
