#!/bin/bash

# Setup script for PostgreSQL authentication migration

echo "Setting up PostgreSQL authentication..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start PostgreSQL (if using Docker)
if command -v docker &> /dev/null; then
    echo "Starting PostgreSQL with Docker..."
    docker-compose -f docker-compose-postgres.yml up -d db
    sleep 5
fi

# Create database and run migrations
echo "Setting up database..."
python -c "
from questions.db_models_postgres import create_tables
create_tables()
print('Database tables created successfully!')
"

# Run migrations if alembic is available
if command -v alembic &> /dev/null; then
    echo "Running database migrations..."
    alembic upgrade head
fi

echo "Setup complete!"
echo "You can now start the application with PostgreSQL authentication."
echo ""
echo "Environment variables:"
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/textgen"
echo ""
echo "To start the application:"
echo "uvicorn main:app --reload --host 0.0.0.0 --port 8080"
