#!/usr/bin/env python3
"""
Migration script to transfer users from Google Cloud NDB to PostgreSQL
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set required environment variables
project_root = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', os.path.join(project_root, 'secrets/google-credentials.json'))
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'questions-346919')
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/textgen')

def setup_logging():
    """Setup logging for the migration process"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('user_migration.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_connections(logger):
    """Test both database connections"""
    logger.info("Testing database connections...")
    
    # Test PostgreSQL connection
    try:
        from questions.db_models_postgres import SessionLocal, create_tables
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ PostgreSQL connection successful")
        
        # Ensure tables exist
        create_tables()
        logger.info("✅ PostgreSQL tables created/verified")
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    # Test Google Cloud NDB connection
    try:
        from google.cloud import ndb
        
        # Define NDB User model for migration
        class NDBUser(ndb.Model):
            id = ndb.StringProperty(required=True)
            cookie_user = ndb.IntegerProperty()
            created = ndb.DateTimeProperty(auto_now_add=True)
            updated = ndb.DateTimeProperty(auto_now=True)
            is_subscribed = ndb.BooleanProperty(default=False)
            num_self_hosted_instances = ndb.IntegerProperty(default=0)
            name = ndb.StringProperty()
            email = ndb.StringProperty()
            profile_url = ndb.StringProperty()
            access_token = ndb.StringProperty()
            photo_url = ndb.StringProperty()
            stripe_id = ndb.StringProperty()
            secret = ndb.StringProperty()
            free_credits = ndb.IntegerProperty(default=0)
            charges_monthly = ndb.IntegerProperty(default=0)
            
        client = ndb.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "questions-346919"))
        
        with client.context():
            # Try to query one user to test connection
            NDBUser.query().fetch(1)
            logger.info("✅ Google Cloud NDB connection successful")
            
    except Exception as e:
        logger.error(f"❌ Google Cloud NDB connection failed: {e}")
        logger.error("Make sure GOOGLE_APPLICATION_CREDENTIALS is set correctly")
        return False
    
    return True

def migrate_users(logger) -> int:
    """Migrate all users from NDB to PostgreSQL"""
    from google.cloud import ndb
    from questions.db_models_postgres import User as PGUser, SessionLocal
    
    # Define NDB User model for migration (same as in test_connections)
    class NDBUser(ndb.Model):
        id = ndb.StringProperty(required=True)
        cookie_user = ndb.IntegerProperty()
        created = ndb.DateTimeProperty(auto_now_add=True)
        updated = ndb.DateTimeProperty(auto_now=True)
        is_subscribed = ndb.BooleanProperty(default=False)
        num_self_hosted_instances = ndb.IntegerProperty(default=0)
        name = ndb.StringProperty()
        email = ndb.StringProperty()
        profile_url = ndb.StringProperty()
        access_token = ndb.StringProperty()
        photo_url = ndb.StringProperty()
        stripe_id = ndb.StringProperty()
        secret = ndb.StringProperty()
        free_credits = ndb.IntegerProperty(default=0)
        charges_monthly = ndb.IntegerProperty(default=0)
        
    client = ndb.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "questions-346919"))
    
    logger.info("Starting user migration...")
    
    db = SessionLocal()
    migrated_count = 0
    updated_count = 0
    error_count = 0
    
    try:
        with client.context():
            # Fetch all users from NDB
            ndb_users = NDBUser.query().fetch()
            logger.info(f"Found {len(ndb_users)} users in NDB")
            
            for ndb_user in ndb_users:
                try:
                    # Check if user already exists in PostgreSQL
                    existing_user = db.query(PGUser).filter(
                        PGUser.id == ndb_user.id
                    ).first()
                    
                    if existing_user:
                        # Update existing user with NDB data (except password)
                        existing_user.email = ndb_user.email
                        existing_user.name = ndb_user.name
                        existing_user.stripe_id = ndb_user.stripe_id
                        existing_user.secret = ndb_user.secret
                        existing_user.free_credits = ndb_user.free_credits or 0
                        existing_user.charges_monthly = ndb_user.charges_monthly or 0
                        existing_user.profile_url = ndb_user.profile_url
                        existing_user.photo_url = ndb_user.photo_url
                        existing_user.created = ndb_user.created
                        existing_user.updated = ndb_user.updated
                        
                        updated_count += 1
                        logger.debug(f"Updated existing user: {ndb_user.email}")
                    else:
                        # Create new PostgreSQL user
                        pg_user = PGUser(
                            id=ndb_user.id,
                            email=ndb_user.email,
                            name=ndb_user.name,
                            stripe_id=ndb_user.stripe_id,
                            secret=ndb_user.secret,
                            free_credits=ndb_user.free_credits or 0,
                            charges_monthly=ndb_user.charges_monthly or 0,
                            profile_url=ndb_user.profile_url,
                            photo_url=ndb_user.photo_url,
                            created=ndb_user.created,
                            updated=ndb_user.updated,
                            # password_hash will be None - users will need to set password on first login
                        )
                        
                        db.add(pg_user)
                        migrated_count += 1
                        logger.debug(f"Migrated new user: {ndb_user.email}")
                    
                    db.commit()
                    
                    if (migrated_count + updated_count) % 10 == 0:
                        logger.info(f"Processed {migrated_count + updated_count} users...")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error migrating user {ndb_user.email}: {e}")
                    db.rollback()
                    continue
    
    finally:
        db.close()
    
    logger.info(f"User migration completed: {migrated_count} new, {updated_count} updated, {error_count} errors")
    return migrated_count + updated_count

def verify_migration(logger):
    """Verify the migration by comparing user counts"""
    from google.cloud import ndb
    from questions.db_models_postgres import User as PGUser, SessionLocal
    
    # Define NDB User model for migration (same as above)
    class NDBUser(ndb.Model):
        id = ndb.StringProperty(required=True)
        cookie_user = ndb.IntegerProperty()
        created = ndb.DateTimeProperty(auto_now_add=True)
        updated = ndb.DateTimeProperty(auto_now=True)
        is_subscribed = ndb.BooleanProperty(default=False)
        num_self_hosted_instances = ndb.IntegerProperty(default=0)
        name = ndb.StringProperty()
        email = ndb.StringProperty()
        profile_url = ndb.StringProperty()
        access_token = ndb.StringProperty()
        photo_url = ndb.StringProperty()
        stripe_id = ndb.StringProperty()
        secret = ndb.StringProperty()
        free_credits = ndb.IntegerProperty(default=0)
        charges_monthly = ndb.IntegerProperty(default=0)
        
    client = ndb.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "questions-346919"))
    
    logger.info("Verifying migration...")
    
    db = SessionLocal()
    
    try:
        # Count PostgreSQL records
        pg_user_count = db.query(PGUser).count()
        
        # Count NDB records
        with client.context():
            ndb_user_count = NDBUser.query().count()
        
        logger.info("Migration verification:")
        logger.info(f"  Users: NDB={ndb_user_count}, PostgreSQL={pg_user_count}")
        
        if pg_user_count >= ndb_user_count:
            logger.info("✅ User migration verification successful!")
            return True
        else:
            logger.warning("⚠️  User migration may be incomplete - counts don't match")
            return False
            
    finally:
        db.close()

def main():
    """Main migration function"""
    logger = setup_logging()
    
    logger.info("🚀 Starting NDB to PostgreSQL User Migration")
    logger.info("=" * 50)
    
    # Test connections
    if not test_connections(logger):
        logger.error("❌ Connection tests failed. Aborting migration.")
        sys.exit(1)
    
    start_time = datetime.now()
    
    try:
        # Migrate users
        user_count = migrate_users(logger)
        
        # Verify migration
        verify_migration(logger)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🎉 User migration completed successfully!")
        logger.info("📊 Summary:")
        logger.info(f"   Users processed: {user_count}")
        logger.info(f"   Duration: {duration}")
        logger.info("   Log file: user_migration.log")
        logger.info("")
        logger.info("⚠️  NOTE: Migrated users do not have passwords set.")
        logger.info("   They will need to set a password on first login.")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
