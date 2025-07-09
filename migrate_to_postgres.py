#!/usr/bin/env python3
"""
Migration script to transfer documents from Google Cloud NDB to PostgreSQL
Note: Users are now stored in PostgreSQL only, so we only migrate documents.
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set required environment variables
project_root = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', os.path.join(project_root, 'secrets/google-credentials.json'))
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'questions-346919')  # Set the correct project ID
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
        from questions.db_models import Document as NDBDocument, client
        with client.context():
            # Try to query one document to test connection
            NDBDocument.query().fetch(1)
            logger.info("✅ Google Cloud NDB connection successful")
            
    except Exception as e:
        logger.error(f"❌ Google Cloud NDB connection failed: {e}")
        logger.error("Make sure GOOGLE_APPLICATION_CREDENTIALS is set correctly")
        return False
    
    return True

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
    """Verify the migration by comparing document counts"""
    from questions.db_models import Document as NDBDocument, client
    from questions.db_models_postgres import Document as PGDocument, SessionLocal
    
    logger.info("Verifying migration...")
    
    db = SessionLocal()
    
    try:
        # Count PostgreSQL records
        pg_doc_count = db.query(PGDocument).count()
        
        # Count NDB records
        with client.context():
            ndb_doc_count = NDBDocument.query().count()
        
        logger.info("Migration verification:")
        logger.info(f"  Documents: NDB={ndb_doc_count}, PostgreSQL={pg_doc_count}")
        
        if pg_doc_count >= ndb_doc_count:
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
    
    logger.info("🚀 Starting NDB to PostgreSQL Document Migration")
    logger.info("=" * 50)
    
    # Test connections
    if not test_connections(logger):
        logger.error("❌ Connection tests failed. Aborting migration.")
        sys.exit(1)
    
    start_time = datetime.now()
    
    try:
        # Migrate documents only (users are now PostgreSQL-only)
        doc_count = migrate_documents(logger)
        
        # Verify migration
        verify_migration(logger)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🎉 Migration completed successfully!")
        logger.info("📊 Summary:")
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
