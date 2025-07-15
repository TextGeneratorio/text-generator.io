#!/bin/bash
# Setup script to create both textgen and textgen_prod databases

set -e  # Exit on any error

echo "🚀 Setting up Production PostgreSQL Databases"
echo "============================================="

# Production database credentials - update these with your actual credentials
DB_HOST="${PROD_DB_HOST:-localhost}"
DB_USER="${PROD_DB_USER:-postgres}"
DB_PASSWORD="${PROD_DB_PASSWORD:-password}"
DB_PORT="${PROD_DB_PORT:-5432}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Database Configuration:${NC}"
echo "  Host: $DB_HOST"
echo "  User: $DB_USER"
echo "  Port: $DB_PORT"
echo "  Primary DB: textgen_prod"
echo "  Fallback DB: textgen"
echo

# Function to run SQL commands
run_sql() {
    local database="$1"
    local sql="$2"
    local description="$3"
    echo -e "${YELLOW}$description${NC}"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$database" -c "$sql"
}

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to PostgreSQL at $DB_HOST:$DB_PORT${NC}"
    echo "Please ensure PostgreSQL is running and credentials are correct."
    echo "Current credentials:"
    echo "  Host: $DB_HOST"
    echo "  User: $DB_USER" 
    echo "  Password: [hidden]"
    echo "  Port: $DB_PORT"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL connection successful${NC}"

# Create both databases if they don't exist
echo -e "${YELLOW}Creating databases...${NC}"

# Create textgen_prod database (primary)
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "
CREATE DATABASE textgen_prod;
" 2>/dev/null || echo "textgen_prod database already exists"

# Create textgen database (fallback)
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "
CREATE DATABASE textgen;
" 2>/dev/null || echo "textgen database already exists"

# Verify both databases exist
echo -e "${YELLOW}Verifying databases...${NC}"
for db_name in "textgen_prod" "textgen"; do
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$db_name" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database '$db_name' is ready${NC}"
    else
        echo -e "${RED}❌ Cannot connect to database '$db_name'${NC}"
        exit 1
    fi
done

# Set environment variables for the application
export PROD_DB_HOST="$DB_HOST"
export PROD_DB_USER="$DB_USER"
export PROD_DB_PASSWORD="$DB_PASSWORD"
export PROD_DB_PORT="$DB_PORT"
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/textgen_prod"

# Run Alembic migrations on both databases
echo -e "${YELLOW}Running migrations on textgen_prod...${NC}"
DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/textgen_prod" alembic upgrade head

echo -e "${YELLOW}Running migrations on textgen...${NC}"
DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/textgen" alembic upgrade head

echo -e "${GREEN}🎉 Database setup complete!${NC}"
echo ""
echo "Database Configuration:"
echo "  Primary Database: textgen_prod"
echo "  Fallback Database: textgen"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo ""
echo "Connection String (Primary):"
echo "  DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/textgen_prod"
echo ""
echo "Connection String (Fallback):"
echo "  DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/textgen"
echo ""
echo "Next steps:"
echo "1. Start the application: ./start_with_prod_db.sh"
echo "2. Or run tests: python -m pytest tests/"
echo "3. The app will automatically use textgen_prod, falling back to textgen if needed"
