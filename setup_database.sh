#!/bin/bash

# PostgreSQL Database Setup Script for Text Generator
# This script sets up a clean PostgreSQL database for the Text Generator application

set -e  # Exit on any error

echo "🚀 Setting up PostgreSQL Database for Text Generator"
echo "=================================================="

# Configuration
DB_NAME="textgen"
DB_USER="postgres"
DB_PASSWORD="password"
DB_HOST="localhost"
DB_PORT="5432"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run SQL commands
run_sql() {
    local sql="$1"
    local description="$2"
    echo -e "${YELLOW}$description${NC}"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
}

# Function to run SQL files
run_sql_file() {
    local file="$1"
    local description="$2"
    echo -e "${YELLOW}$description${NC}"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$file"
}

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to PostgreSQL at $DB_HOST:$DB_PORT${NC}"
    echo "Please ensure PostgreSQL is running:"
    echo "  docker-compose -f docker-compose-postgres.yml up -d"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL connection successful${NC}"

# Create database if it doesn't exist
echo -e "${YELLOW}Creating database '$DB_NAME' if it doesn't exist...${NC}"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "
CREATE DATABASE $DB_NAME;
" 2>/dev/null || echo "Database already exists"

# Check if database exists
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to database '$DB_NAME'${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Database '$DB_NAME' is ready${NC}"

# Run Alembic migrations to create core tables
echo -e "${YELLOW}Running Alembic migrations...${NC}"
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
alembic upgrade head

# Verify core tables exist
echo -e "${YELLOW}Verifying core tables...${NC}"
TABLES=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('users', 'documents', 'alembic_version')
ORDER BY table_name;
")

EXPECTED_TABLES=("alembic_version" "documents" "users")
for table in "${EXPECTED_TABLES[@]}"; do
    if echo "$TABLES" | grep -q "$table"; then
        echo -e "${GREEN}✅ Table '$table' exists${NC}"
    else
        echo -e "${RED}❌ Table '$table' is missing${NC}"
        exit 1
    fi
done

# Add proper foreign key constraints
echo -e "${YELLOW}Adding foreign key constraints...${NC}"
run_sql "
ALTER TABLE documents 
ADD CONSTRAINT fk_documents_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) 
ON DELETE CASCADE;
" "Adding foreign key constraint: documents.user_id -> users.id"

# Add indexes for better performance
echo -e "${YELLOW}Adding performance indexes...${NC}"
run_sql "
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_updated ON documents(updated);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_secret ON users(secret);
CREATE INDEX IF NOT EXISTS idx_users_stripe_id ON users(stripe_id);
" "Adding performance indexes"

# Verify database structure
echo -e "${YELLOW}Verifying database structure...${NC}"
run_sql "
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
" "Listing all tables"

# Display database statistics
echo -e "${YELLOW}Database statistics:${NC}"
run_sql "
SELECT 
    'users' as table_name,
    COUNT(*) as record_count
FROM users
UNION ALL
SELECT 
    'documents' as table_name,
    COUNT(*) as record_count
FROM documents;
" "Record counts"

# Create a simple test to verify everything works
echo -e "${YELLOW}Running connectivity test...${NC}"
run_sql "
SELECT 
    current_database() as database_name,
    current_user as current_user,
    version() as postgres_version;
" "Database connectivity test"

echo -e "${GREEN}🎉 Database setup complete!${NC}"
echo ""
echo "Database Configuration:"
echo "  Database: $DB_NAME"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo ""
echo "Connection String:"
echo "  DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Next steps:"
echo "1. Set environment variable: export DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo "2. Run the application: python main.py"
echo "3. Or run tests: python -m pytest tests/"
