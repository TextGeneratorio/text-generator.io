#!/bin/bash
# Environment configuration for PostgreSQL migration

# Set database URL for PostgreSQL
export DATABASE_URL="postgresql://postgres:password@localhost:5432/textgen"

# Set Google Cloud credentials if available
if [ -f "secrets/google-credentials.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/google-credentials.json"
fi

# Start the application with PostgreSQL enabled
echo "🚀 Starting 20 Questions with PostgreSQL database..."
echo "📊 Database: PostgreSQL (migrated from NDB)"
echo "👤 Users migrated: 11,214"
echo "📄 Documents migrated: 157"
echo

python main.py
