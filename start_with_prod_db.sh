#!/bin/bash
# Start 20 Questions with production PostgreSQL database configuration

echo "🚀 Starting 20 Questions with Production Database"
echo "================================================="

# Set production database environment variables
export PROD_DB_HOST="localhost"
export PROD_DB_USER="postgres" 
export PROD_DB_PASSWORD="password"  # Replace with actual production password
export PROD_DB_PORT="5432"

# Use textgen_prod database by default
export DATABASE_URL="postgresql://$PROD_DB_USER:$PROD_DB_PASSWORD@$PROD_DB_HOST:$PROD_DB_PORT/textgen_prod"

echo "📊 Database Configuration:"
echo "  Host: $PROD_DB_HOST"
echo "  User: $PROD_DB_USER"
echo "  Port: $PROD_DB_PORT"
echo "  Database: textgen_prod (primary)"
echo "  Fallback: textgen"
echo "  URL: $DATABASE_URL"
echo

# Test database connectivity before starting the application
echo "🔍 Testing database connectivity..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='$PROD_DB_HOST',
        user='$PROD_DB_USER',
        password='$PROD_DB_PASSWORD',
        port='$PROD_DB_PORT',
        database='textgen_prod'
    )
    conn.close()
    print('✅ textgen_prod database connection successful!')
except Exception as e:
    print(f'⚠️  textgen_prod database connection failed: {e}')
    print('   Trying fallback database: textgen')
    try:
        conn = psycopg2.connect(
            host='$PROD_DB_HOST',
            user='$PROD_DB_USER',
            password='$PROD_DB_PASSWORD',
            port='$PROD_DB_PORT',
            database='textgen'
        )
        conn.close()
        print('✅ textgen database connection successful!')
        import os
        os.environ['DATABASE_URL'] = 'postgresql://$PROD_DB_USER:$PROD_DB_PASSWORD@$PROD_DB_HOST:$PROD_DB_PORT/textgen'
        print('🔄 Switched to textgen database')
    except Exception as e2:
        print(f'❌ Both databases failed: {e2}')
        print('   Please check your database configuration and credentials')
        exit(1)
"

echo
echo "🎯 Starting Text Generator with production database settings..."
python3 main.py
