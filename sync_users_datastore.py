#!/usr/bin/env python3
"""
Simple migration script to sync remaining users from Google Cloud Datastore to PostgreSQL
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set required environment variables
project_root = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", os.path.join(project_root, "secrets/google-credentials.json"))
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "questions-346919")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:password@localhost:5432/textgen")


def sync_users():
    """Sync remaining users from Google Cloud Datastore to PostgreSQL"""
    from google.cloud import datastore

    from questions.db_models_postgres import SessionLocal
    from questions.db_models_postgres import User as PGUser

    print("🚀 Starting user sync from Google Cloud Datastore to PostgreSQL")
    print("=" * 60)

    # Initialize clients
    ds_client = datastore.Client(project="questions-346919")
    db = SessionLocal()

    migrated_count = 0
    updated_count = 0
    error_count = 0

    try:
        # Get all users from datastore
        query = ds_client.query(kind="User")
        ds_users = list(query.fetch())
        print(f"Found {len(ds_users)} users in Google Cloud Datastore")

        # Get existing user IDs from PostgreSQL
        existing_user_ids = set(user.id for user in db.query(PGUser.id).all())
        print(f"Found {len(existing_user_ids)} users in PostgreSQL")

        for ds_user in ds_users:
            try:
                user_id = ds_user.get("id")
                if not user_id:
                    continue

                # Check if user exists in PostgreSQL
                if user_id in existing_user_ids:
                    # Update existing user
                    existing_user = db.query(PGUser).filter(PGUser.id == user_id).first()
                    if existing_user:
                        existing_user.email = ds_user.get("email")
                        existing_user.name = ds_user.get("name")
                        existing_user.stripe_id = ds_user.get("stripe_id")
                        existing_user.secret = ds_user.get("secret")
                        existing_user.free_credits = ds_user.get("free_credits", 0)
                        existing_user.charges_monthly = ds_user.get("charges_monthly", 0)
                        existing_user.profile_url = ds_user.get("profile_url")
                        existing_user.photo_url = ds_user.get("photo_url")
                        existing_user.created = ds_user.get("created")
                        existing_user.updated = ds_user.get("updated")
                        updated_count += 1
                else:
                    # Create new user
                    new_user = PGUser(
                        id=user_id,
                        email=ds_user.get("email"),
                        name=ds_user.get("name"),
                        stripe_id=ds_user.get("stripe_id"),
                        secret=ds_user.get("secret"),
                        free_credits=ds_user.get("free_credits", 0),
                        charges_monthly=ds_user.get("charges_monthly", 0),
                        profile_url=ds_user.get("profile_url"),
                        photo_url=ds_user.get("photo_url"),
                        created=ds_user.get("created"),
                        updated=ds_user.get("updated"),
                        # password_hash will be None - users need to set password on first login
                    )
                    db.add(new_user)
                    migrated_count += 1

                # Commit every 100 users
                if (migrated_count + updated_count) % 100 == 0:
                    db.commit()
                    print(f"Processed {migrated_count + updated_count} users...")

            except Exception as e:
                error_count += 1
                print(f"Error processing user {ds_user.get('email', 'unknown')}: {e}")
                db.rollback()
                continue

        # Final commit
        db.commit()

        print("\n✅ Sync completed!")
        print("📊 Results:")
        print(f"   New users migrated: {migrated_count}")
        print(f"   Existing users updated: {updated_count}")
        print(f"   Errors: {error_count}")
        print(f"   Total processed: {migrated_count + updated_count}")

        # Final verification
        final_count = db.query(PGUser).count()
        print("\n🔍 Final verification:")
        print(f"   Total users in PostgreSQL: {final_count}")
        print(f"   Total users in Datastore: {len(ds_users)}")

        if final_count >= len(ds_users):
            print("✅ All users successfully synced!")
        else:
            print(f"⚠️  {len(ds_users) - final_count} users may still need to be migrated")

    finally:
        db.close()


if __name__ == "__main__":
    sync_users()
