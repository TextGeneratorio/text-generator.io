#!/usr/bin/env python3
"""
Migration script to transfer all users and documents from Google Cloud NDB to PostgreSQL
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set required environment variables
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', 'secrets/google-credentials.json')
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/textgen')

def setup_logging():
    """Setup logging for the migration process"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('migration.log'),
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
        from questions.db_models import User as NDBUser, client
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
    from questions.db_models import User as NDBUser, client
    from questions.db_models_postgres import User as PGUser, SessionLocal
    
    logger.info("Starting user migration...")
    
    db = SessionLocal()
    migrated_count = 0
    error_count = 0
    
    try:
        with client.context():
            # Fetch all users from NDB
            ndb_users = NDBUser.query().fetch()
            logger.info(f"Found {len(ndb_users)} users in NDB")
            
            for ndb_user in ndb_users:
                try:
                    # Check if user already exists in PostgreSQL
                    existing_user = db.query(PGUser).filter(PGUser.id == ndb_user.id).first()
                    if existing_user:
                        logger.info(f"User {ndb_user.id} already exists, skipping...")
                        continue
                    
                    # Create new PostgreSQL user
                    pg_user = PGUser(
                        id=ndb_user.id,
                        email=ndb_user.email or f"user_{ndb_user.id}@migrated.local",
                        name=ndb_user.name,
                        profile_url=ndb_user.profile_url,
                        photo_url=ndb_user.photo_url,
                        is_subscribed=ndb_user.is_subscribed or False,
                        stripe_id=ndb_user.stripe_id,
                        secret=ndb_user.secret or f"secret_{ndb_user.id}",
                        free_credits=ndb_user.free_credits or 0,
                        charges_monthly=ndb_user.charges_monthly or 0,
                        num_self_hosted_instances=ndb_user.num_self_hosted_instances or 0,
                        cookie_user=ndb_user.cookie_user,
                        access_token=ndb_user.access_token,
                        created=ndb_user.created,
                        updated=ndb_user.updated
                    )
                    
                    db.add(pg_user)
                    db.commit()
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        logger.info(f"Migrated {migrated_count} users...")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error migrating user {ndb_user.id}: {e}")
                    db.rollback()
                    continue
    
    finally:
        db.close()
    
    logger.info(f"User migration completed: {migrated_count} migrated, {error_count} errors")
    return migrated_count

def migrate_documents(logger) -> int:
    """Migrate all documents from NDB to PostgreSQL"""
    from questions.db_models import Document as NDBDocument, client
    from questions.db_models_postgres import Document as PGDocument, SessionLocal
    
    logger.info("Starting document migration...")
    
    db = SessionLocal()
    migrated_count = 0
    error_count = 0
    
    try:
        with client.context():
            # Fetch all documents from NDB
            ndb_documents = NDBDocument.query().fetch()
            logger.info(f"Found {len(ndb_documents)} documents in NDB")
            
            for ndb_doc in ndb_documents:
                try:
                    # Check if document already exists in PostgreSQL
                    # Since NDB uses auto-generated keys, we'll check by user_id, title, and created time
                    existing_doc = db.query(PGDocument).filter(
                        PGDocument.user_id == ndb_doc.user_id,
                        PGDocument.title == (ndb_doc.title or "Untitled Document"),
                        PGDocument.created == ndb_doc.created
                    ).first()
                    
                    if existing_doc:
                        logger.debug(f"Document for user {ndb_doc.user_id} already exists, skipping...")
                        continue
                    
                    # Create new PostgreSQL document
                    pg_doc = PGDocument(
                        user_id=ndb_doc.user_id,
                        title=ndb_doc.title or "Untitled Document",
                        content=ndb_doc.content,
                        created=ndb_doc.created,
                        updated=ndb_doc.updated
                    )
                    
                    db.add(pg_doc)
                    db.commit()
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        logger.info(f"Migrated {migrated_count} documents...")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error migrating document for user {ndb_doc.user_id}: {e}")
                    db.rollback()
                    continue
    
    finally:
        db.close()
    
    logger.info(f"Document migration completed: {migrated_count} migrated, {error_count} errors")
    return migrated_count

def verify_migration(logger):
    """Verify the migration by comparing counts"""
    from questions.db_models import User as NDBUser, Document as NDBDocument, client
    from questions.db_models_postgres import User as PGUser, Document as PGDocument, SessionLocal
    
    logger.info("Verifying migration...")
    
    db = SessionLocal()
    
    try:
        # Count PostgreSQL records
        pg_user_count = db.query(PGUser).count()
        pg_doc_count = db.query(PGDocument).count()
        
        # Count NDB records
        with client.context():
            ndb_user_count = NDBUser.query().count()
            ndb_doc_count = NDBDocument.query().count()
        
        logger.info("Migration verification:")
        logger.info(f"  Users: NDB={ndb_user_count}, PostgreSQL={pg_user_count}")
        logger.info(f"  Documents: NDB={ndb_doc_count}, PostgreSQL={pg_doc_count}")
        
        if pg_user_count >= ndb_user_count and pg_doc_count >= ndb_doc_count:
            logger.info("✅ Migration verification successful!")
            return True
        else:
            logger.warning("⚠️  Migration may be incomplete - counts don't match")
            return False
            
    finally:
        db.close()

def main():
    """Main migration function"""
    logger = setup_logging()
    
    logger.info("🚀 Starting NDB to PostgreSQL Migration")
    logger.info("=" * 50)
    
    # Test connections
    if not test_connections(logger):
        logger.error("❌ Connection tests failed. Aborting migration.")
        sys.exit(1)
    
    start_time = datetime.now()
    
    try:
        # Migrate users
        user_count = migrate_users(logger)
        
        # Migrate documents
        doc_count = migrate_documents(logger)
        
        # Verify migration
        verify_migration(logger)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🎉 Migration completed successfully!")
        logger.info("📊 Summary:")
        logger.info(f"   Users migrated: {user_count}")
        logger.info(f"   Documents migrated: {doc_count}")
        logger.info(f"   Duration: {duration}")
        logger.info("   Log file: migration.log")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
