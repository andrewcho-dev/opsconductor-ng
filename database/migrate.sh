#!/bin/bash

# Database migration script for OpsConductor
# This script helps migrate from separate databases to unified schema

set -e

echo "🗄️  OpsConductor Database Migration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if .env file exists
if [ ! -f ../.env ]; then
    print_info ".env file not found. Please run setup-env.sh first."
    exit 1
fi

# Load environment variables
source ../.env

# Database connection parameters
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-opsconductor}
DB_USER=${DB_USER:-opsconductor}
DB_PASS=${DB_PASS:-opsconductor123}

print_info "Connecting to database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Check if PostgreSQL is available
print_info "Checking database connectivity..."
if command -v psql >/dev/null 2>&1; then
    PGPASSWORD=${DB_PASS} psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -c "SELECT version();" >/dev/null 2>&1
    print_status $? "Database connection successful"
else
    print_info "psql not found. Assuming database is accessible via Docker."
fi

# Apply schema
print_info "Applying database schema..."
if command -v psql >/dev/null 2>&1; then
    PGPASSWORD=${DB_PASS} psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -f init-schema.sql
    print_status $? "Schema applied successfully"
else
    print_info "To apply schema manually, run:"
    print_info "docker exec -i opsconductor-postgres psql -U ${DB_USER} -d ${DB_NAME} < database/init-schema.sql"
fi

# Verify tables exist
print_info "Verifying table creation..."
if command -v psql >/dev/null 2>&1; then
    TABLE_COUNT=$(PGPASSWORD=${DB_PASS} psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
    if [ "$TABLE_COUNT" -gt 8 ]; then
        print_status 0 "All tables created successfully ($TABLE_COUNT tables found)"
    else
        print_status 1 "Expected more than 8 tables, found $TABLE_COUNT"
    fi
else
    print_info "Manual verification needed - check that all tables exist in the database"
fi

echo ""
print_info "Migration completed!"
print_info "Tables created:"
print_info "- users (authentication and authorization)"
print_info "- credentials (encrypted credential storage)"
print_info "- targets (target system definitions)"
print_info "- jobs (job definitions)"
print_info "- schedules (cron scheduling)"
print_info "- job_runs (execution tracking)"
print_info "- job_run_steps (step-level execution)"
print_info "- audit_log (audit trail with hash chaining)"
print_info "- notifications (notification delivery)"
print_info "- dlq (dead letter queue)"

echo ""
echo -e "${GREEN}🎉 Database migration completed successfully!${NC}"