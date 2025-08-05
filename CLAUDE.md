tools:
use uv - edit requirements.in files and run uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt
uv pip install -r dev-requirements.txt
uv pip install -r questions/inference_server/requirements.txt

## Database Configuration

The app uses environment-aware PostgreSQL configuration with strict environment separation:

### Development Environment (Default)
- Uses `textgen` database on localhost
- Automatically detected when `ENVIRONMENT != "production"`
- Database URL: `postgresql://postgres:password@localhost:5432/textgen`
- Prevents accidental use of production resources

### Production Environment
- Uses `textgen_prod` database
- Enabled by setting `ENVIRONMENT=production`
- Database URL: `postgresql://postgres:password@localhost:5432/textgen_prod`

### Database Setup
Ensure both databases exist and tables are created:
```bash
# Create databases
createdb -U postgres textgen
createdb -U postgres textgen_prod

# Run migrations for development
alembic upgrade head

# Run migrations for production
ENVIRONMENT=production alembic upgrade head
```

## Running the Application

### Development Mode
```bash
# With hot reload and debug logging
python -m uvicorn main:app --host 0.0.0.0 --port 8083 --reload

# Alternative startup scripts
./start_with_postgres.sh   # Uses textgen database
./start_with_prod_db.sh    # Uses textgen_prod database
```

### Production Mode
```bash
# Set production environment
export ENVIRONMENT=production

# Multi-worker production server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8083 --timeout 300 --worker-connections 1000 --max-requests 1000 --max-requests-jitter 100 --preload

# Single worker for debugging production issues
gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8083 --timeout 300
```

### Testing Database Connection
```bash
# Test development database
python -c "from questions.db_models_postgres import engine; print('Database connection successful')"

# Test production database
ENVIRONMENT=production python -c "from questions.db_models_postgres import engine; print('Production database connection successful')"
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

#### Production Database Setup (Recommended)

The application now uses **production database credentials by default** with automatic fallback:

1. **Primary Database**: `textgen_prod` (production)
2. **Fallback Database**: `textgen` (development/backup)

Set production database environment variables:
```bash
# Production PostgreSQL credentials (hardcoded in application)
export PROD_DB_HOST="your-prod-host"
export PROD_DB_USER="your-prod-user"
export PROD_DB_PASSWORD="your-prod-password"
export PROD_DB_PORT="5432"
```

#### Quick Setup

1. **Setup both databases**:
```bash
./setup_prod_databases.sh
```

2. **Start with production configuration**:
```bash
./start_with_prod_db.sh
```

#### Manual Configuration

Set `DATABASE_URL` environment variable:
```bash
# Production PostgreSQL (Primary - textgen_prod)
DATABASE_URL="postgresql://username:password@prod-host:5432/textgen_prod"

# Development/Fallback (textgen)
DATABASE_URL="postgresql://username:password@prod-host:5432/textgen"
```

#### Database Connection Logic

The application will:
1. **Try** to connect to `textgen_prod` first
2. **Fallback** to `textgen` if `textgen_prod` fails
3. **Use** environment `DATABASE_URL` if explicitly set
4. **Default** to production credentials (not localhost development)

The app automatically enables PostgreSQL mode when database connection succeeds.

PYTHONPATH=. pytest tests/test_chat_openai.py


to try test the real inference server:
try kill on this port then rerun cd /home/lee/code/20-questions &&
  PYTHONPATH=/home/lee/code/20-questions:/home/lee/code/20-questions/OFA
  /home/lee/code/20-questions/.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -b :9080
  questions.inference_server.inference_server:app --timeout 180000 --workers 1 then curl -X 'POST' \
    'http://0.0.0.0:9080/api/v1/generate' \
    -H 'accept: application/json' \
    -H 'secret: DjbkCN1iAYnz4oj28QqOEORl84jKSeUT' \
    -H 'Content-Type: application/json' \
    -d '{
    "text": "string",
    "number_of_results": 1,
    "max_length": 100,
    "min_length": 1,
    "max_sentences": 0,
    "min_probability": 0,
    "stop_sequences": [],
    "top_p": 0.9,
    "top_k": 40,
    "temperature": 0.7,
    "seed": 0,
    "repetition_penalty": 1.2,
    "model": "string"
  }'
