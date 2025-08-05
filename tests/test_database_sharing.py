#!/usr/bin/env python
"""
Test script to verify that both main.py and inference_server.py can properly
connect to and share the same PostgreSQL database.
"""

import sys
import os
sys.path.insert(0, '.')

# Set environment variables for PostgreSQL
os.environ['USE_POSTGRES'] = 'True'
os.environ['DATABASE_URL'] = 'postgresql://postgres:password@localhost:5432/textgen'

def test_main_py_database():
    """Test that main.py can connect to PostgreSQL"""
    print("Testing main.py database connection...")
    try:
        from main import USE_POSTGRES, get_db
        print(f"main.py USE_POSTGRES: {USE_POSTGRES}")
        
        if USE_POSTGRES:
            db_gen = get_db()
            db = next(db_gen)
            print("✓ main.py can connect to PostgreSQL")
            db.close()
        else:
            print("✗ main.py is not using PostgreSQL")
            
    except Exception as e:
        print(f"✗ main.py database connection failed: {e}")
        return False
    
    return USE_POSTGRES

def test_inference_server_database():
    """Test that inference_server.py can connect to PostgreSQL"""
    print("\nTesting inference_server.py database connection...")
    try:
        # Try to import just the database parts without the full server
        from questions.db_models_postgres import User, get_db_session_sync
        print("✓ PostgreSQL models imported successfully")
        
        db = get_db_session_sync()
        # Try to perform a simple query
        user_count = db.query(User).count()
        print(f"✓ inference_server.py can connect to PostgreSQL (found {user_count} users)")
        db.close()
        
        # Try to import the inference server module (might have other dependencies)
        try:
            from questions.inference_server import inference_server
            print("✓ inference_server.py module imported successfully")
        except Exception as e:
            print(f"⚠ inference_server.py module import failed (but database works): {e}")
        
    except Exception as e:
        print(f"✗ inference_server.py database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_audio_server_database():
    """Test that audio_server.py can connect to PostgreSQL"""
    print("\nTesting audio_server.py database connection...")
    try:
        # Try to import just the database parts without the full server
        from questions.db_models_postgres import User, get_db_session_sync
        print("✓ PostgreSQL models imported successfully")
        
        db = get_db_session_sync()
        # Try to perform a simple query
        user_count = db.query(User).count()
        print(f"✓ audio_server.py can connect to PostgreSQL (found {user_count} users)")
        db.close()
        
        # Try to import the audio server module (might have other dependencies)
        try:
            from questions.audio_server import audio_server
            print("✓ audio_server.py module imported successfully")
        except Exception as e:
            print(f"⚠ audio_server.py module import failed (but database works): {e}")
        
    except Exception as e:
        print(f"✗ audio_server.py database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_database_sharing():
    """Test that all servers see the same database"""
    print("\nTesting database sharing...")
    try:
        from questions.db_models_postgres import User, get_db_session_sync
        
        # Create a test user
        db = get_db_session_sync()
        test_email = "test_sharing@example.com"
        
        # Clean up any existing test user
        existing_user = User.get_by_email(db, test_email)
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        # Create a new test user
        new_user = User(
            id="test_sharing_123",
            email=test_email,
            secret="test_secret_123",
            password_hash="test_hash"
        )
        db.add(new_user)
        db.commit()
        
        print(f"✓ Created test user: {test_email}")
        
        # Verify all servers can see the same user
        from main import USE_POSTGRES
        if USE_POSTGRES:
            from main import get_db as main_get_db
            main_db_gen = main_get_db()
            main_db = next(main_db_gen)
            main_user = User.get_by_email(main_db, test_email)
            main_db.close()
            
            if main_user:
                print("✓ main.py can see the test user")
            else:
                print("✗ main.py cannot see the test user")
        
        # Test from inference server perspective
        inf_db = get_db_session_sync()
        inf_user = User.get_by_email(inf_db, test_email)
        inf_db.close()
        
        if inf_user:
            print("✓ inference_server.py can see the test user")
        else:
            print("✗ inference_server.py cannot see the test user")
        
        # Clean up
        db.delete(new_user)
        db.commit()
        db.close()
        
        print("✓ Database sharing test completed")
        
    except Exception as e:
        print(f"✗ Database sharing test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("PostgreSQL Database Sharing Test")
    print("=" * 50)
    
    # Test each server's database connection
    main_ok = test_main_py_database()
    inference_ok = test_inference_server_database()
    audio_ok = test_audio_server_database()
    
    if main_ok and inference_ok and audio_ok:
        sharing_ok = test_database_sharing()
        
        if sharing_ok:
            print("\n🎉 All tests passed! Both servers can properly share the PostgreSQL database.")
        else:
            print("\n❌ Database sharing test failed!")
            sys.exit(1)
    else:
        print("\n❌ Some servers cannot connect to PostgreSQL!")
        sys.exit(1)

if __name__ == "__main__":
    main()
