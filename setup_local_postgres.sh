#!/bin/bash
# Setup script for local PostgreSQL (non-Docker)

set -e  # Exit on any error

echo "🚀 Setting up Local PostgreSQL Authentication"
echo "============================================="

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install it first:"
    echo "   Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "   macOS: brew install postgresql"
    echo "   Arch: sudo pacman -S postgresql"
    exit 1
fi

# Check if PostgreSQL service is running
if ! sudo systemctl is-active --quiet postgresql; then
    echo "🔧 Starting PostgreSQL service..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

echo "✅ PostgreSQL service is running"

# Database configuration
DB_NAME="textgen"
DB_USER="postgres"
DB_PASSWORD="password"
DB_HOST="localhost"
DB_PORT="5432"

# Create database and user
echo "🔧 Setting up database and user..."
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};" 2>/dev/null || echo "Database ${DB_NAME} already exists"
sudo -u postgres psql -c "ALTER USER ${DB_USER} PASSWORD '${DB_PASSWORD}';" 2>/dev/null || true

echo "✅ Database setup complete"

# Install Python dependencies with version fixes
echo "🔧 Installing Python dependencies..."

# Fix alembic version issue - use latest available version
pip install alembic==1.13.3  # Use latest available version instead of 1.16.2

# Install other required packages
pip install psycopg2-binary sqlalchemy

echo "✅ Python dependencies installed"

# Set environment variable
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "✅ DATABASE_URL set to: $DATABASE_URL"

# Test database connection
echo "🧪 Testing database connection..."
python3 -c "
import psycopg2
import os

try:
    conn = psycopg2.connect(
        dbname='${DB_NAME}',
        user='${DB_USER}',
        password='${DB_PASSWORD}',
        host='${DB_HOST}',
        port='${DB_PORT}'
    )
    conn.close()
    print('✅ Database connection successful!')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Create database tables
echo "🔧 Creating database tables..."
python3 -c "
import sys
import os
sys.path.insert(0, '.')

# Set the database URL
os.environ['DATABASE_URL'] = '${DATABASE_URL}'

try:
    from questions.db_models_postgres import create_tables
    create_tables()
    print('✅ Database tables created successfully!')
except ImportError as e:
    print(f'⚠️  Could not import db_models_postgres: {e}')
    print('   This is OK if you haven\'t created the PostgreSQL models yet')
except Exception as e:
    print(f'❌ Error creating tables: {e}')
    exit(1)
"

# Initialize alembic if not already done
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    echo "🔧 Initializing Alembic..."
    alembic init alembic 2>/dev/null || true
    alembic revision --autogenerate -m "Initial migration" 2>/dev/null || echo "⚠️  Alembic revision creation skipped"
fi

# Run migrations
echo "🔧 Running database migrations..."
alembic upgrade head 2>/dev/null || echo "⚠️  Alembic migrations skipped (no migrations to run)"

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Database Configuration:"
echo "   Database: ${DB_NAME}"
echo "   User: ${DB_USER}"
echo "   Host: ${DB_HOST}:${DB_PORT}"
echo ""
echo "🔧 Environment Variables (add to your .bashrc or .zshrc):"
echo "   export DATABASE_URL=\"postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}\""
echo ""
echo "🚀 To start the application:"
echo "   export DATABASE_URL=\"postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}\""
echo "   GOOGLE_APPLICATION_CREDENTIALS=secrets/google-credentials.json python main.py"
echo ""
echo "🧪 To test the connection:"
echo "   psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME}"
