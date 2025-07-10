# PostgreSQL Database Configuration Summary

## Overview
Both `main.py` and `inference_server.py` (along with `audio_server.py`) now use the same PostgreSQL database for user authentication and document storage.

## Database Configuration

### Connection String
All servers use the same database connection string:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/textgen
```

### Database Models
- **User model**: Stores user authentication, subscription info, and API secrets
- **Document model**: Stores user documents and content

## Server Configuration

### main.py (Web Interface)
- **Database Access**: Uses FastAPI dependency injection with `Depends(get_db)`
- **Authentication**: Session-based authentication with cookies
- **User Lookup**: Uses `get_current_user()` from `questions.auth`
- **Database Functions**: Uses `get_db()` generator for session management

### inference_server.py (API Server)
- **Database Access**: Uses `get_db_session_sync()` for synchronous database access
- **Authentication**: Uses API secret from headers (`secret: str = Header(...)`)
- **User Lookup**: Uses `User.get_by_secret(db, secret)` directly
- **Database Functions**: Uses `get_db_session_sync()` for manual session management

### audio_server.py (Audio Processing)
- **Database Access**: Uses `get_db_session_sync()` for synchronous database access
- **Authentication**: Uses API secret from headers (`secret: str = Header(...)`)
- **User Lookup**: Uses `User.get_by_secret(db, secret)` directly
- **Database Functions**: Uses `get_db_session_sync()` for manual session management

## Authentication Flow

### Web Interface (main.py)
1. User logs in via `/api/login` endpoint
2. Session cookie is set with `session_secret`
3. Subsequent requests use `get_current_user()` to validate session
4. User data is stored in PostgreSQL

### API Servers (inference_server.py, audio_server.py)
1. Client sends API request with `secret` header
2. Server looks up user using `User.get_by_secret(db, secret)`
3. User is cached in `session_dict` for performance
4. Stripe usage is tracked and updated in PostgreSQL

## Database Session Management

### FastAPI Dependency Pattern (main.py)
```python
from questions.db_models_postgres import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

@app.get("/api/endpoint")
async def endpoint(db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # db is automatically closed by FastAPI
```

### Manual Session Pattern (inference_server.py, audio_server.py)
```python
from questions.db_models_postgres import get_db_session_sync, User

def some_function(secret: str):
    db = get_db_session_sync()
    try:
        user = User.get_by_secret(db, secret)
        # do work with user
        db.commit()
    finally:
        db.close()  # Must manually close
```

## Environment Variables

Required environment variables for PostgreSQL:
```bash
USE_POSTGRES=True
DATABASE_URL=postgresql://postgres:password@localhost:5432/textgen
```

## Testing Database Sharing

Run the test script to verify all servers can access the same database:
```bash
python test_database_sharing.py
```

## Common Issues and Solutions

### Issue: "No module named 'questions.db_models_postgres'"
**Solution**: Ensure PYTHONPATH includes the project root:
```bash
export PYTHONPATH=/path/to/20-questions2:$PYTHONPATH
```

### Issue: "could not connect to server"
**Solution**: Start PostgreSQL database:
```bash
docker-compose -f docker-compose-postgres.yml up -d
```

### Issue: "relation does not exist"
**Solution**: Run database migrations:
```bash
alembic upgrade head
```

### Issue: Different authentication between servers
**Solution**: 
- Web interface uses session cookies (automatic)
- API servers use secret headers (manual)
- Both share the same user database

## Key Benefits

1. **Single Source of Truth**: All servers use the same PostgreSQL database
2. **Consistent Authentication**: Users created in web interface work with API servers
3. **Shared Session Management**: User sessions are synchronized across servers
4. **Scalable Architecture**: Database can be scaled independently of servers
5. **Data Persistence**: User data persists across server restarts

## Monitoring and Debugging

### View Database Connections
```sql
SELECT * FROM pg_stat_activity WHERE datname = 'textgen';
```

### Check User Sessions
```sql
SELECT id, email, secret, created FROM users ORDER BY created DESC LIMIT 10;
```

### Monitor API Usage
```sql
SELECT email, charges_monthly, stripe_id FROM users WHERE charges_monthly > 0;
```
