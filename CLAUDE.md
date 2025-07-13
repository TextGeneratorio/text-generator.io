tools:
use uv - edit requirements.in files and run uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt
uv pip install -r dev-requirements.txt
uv pip install -r questions/inference_server/requirements.txt

## Running the Application

### Development Mode (with real database)
The app auto-detects development mode via:
- `SERVER_SOFTWARE` starts with "Development" OR
- `IS_DEVELOP=1` environment variable OR  
- `models/debug.env` file exists

Development command:
```bash
# With hot reload and debug logging
python -m uvicorn main:app --host 0.0.0.0 --port 8083 --reload

# Alternative with environment variable
IS_DEVELOP=1 python -m uvicorn main:app --host 0.0.0.0 --port 8083 --reload
```

### Production Mode  
Production command (robust, non-blocking):
```bash
# Multi-worker production server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8083 --timeout 300 --worker-connections 1000 --max-requests 1000 --max-requests-jitter 100 --preload

# Single worker for debugging production issues
gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8083 --timeout 300
```
## Inference Server

### Installation

```bash
pip install -r questions/inference_server/requirements.txt
```

### Running

```bash
PYTHONPATH=$(pwd) python questions/inference_server/main.py
```

gunicorn style 
```bash
gunicorn questions.inference_server.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:9909
```

### Database Configuration
Set `DATABASE_URL` environment variable:
```bash
# Development/Local PostgreSQL
DATABASE_URL="postgresql://postgres:password@localhost:5432/textgen"

# Production PostgreSQL  
DATABASE_URL="postgresql://username:password@prod-host:5432/textgen_db"
```

The app automatically enables PostgreSQL mode when database connection succeeds.

PYTHONPATH=. pytest tests/test_chat_openai.py