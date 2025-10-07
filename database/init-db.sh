#!/bin/bash
# Database initialization script for OpsConductor
# This script ensures the database is properly initialized with ALL required tables and data

set -e

echo "🔧 Initializing OpsConductor database..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec opsconductor-postgres pg_isready -U opsconductor; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Check if database exists and has tables
TABLE_COUNT=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog');" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$TABLE_COUNT" -eq "0" ]; then
    echo "📋 Database is empty. Initializing MASTER schema (includes ALL schemas)..."
    docker exec -i opsconductor-postgres psql -U opsconductor -d opsconductor < /home/opsconductor/opsconductor-ng/database/master-schema.sql
    echo "✅ Database schema initialized successfully!"
else
    echo "📊 Database already has $TABLE_COUNT tables. Checking for missing schemas..."
    
    # Check for execution schema
    EXECUTION_SCHEMA=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'execution';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$EXECUTION_SCHEMA" -eq "0" ]; then
        echo "🔄 Adding missing execution schema (Phase 7)..."
        docker exec -i opsconductor-postgres psql -U opsconductor -d opsconductor < /home/opsconductor/opsconductor-ng/database/phase7-execution-schema.sql
        echo "✅ Execution schema added!"
    fi
    
    # Check for tool_catalog schema
    TOOL_CATALOG_SCHEMA=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'tool_catalog';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$TOOL_CATALOG_SCHEMA" -eq "0" ]; then
        echo "🔄 Adding missing tool_catalog schema..."
        docker exec -i opsconductor-postgres psql -U opsconductor -d opsconductor < /home/opsconductor/opsconductor-ng/database/tool-catalog-schema.sql
        echo "✅ Tool catalog schema added!"
    fi
fi

# Verify critical tables exist
echo "🔍 Verifying database integrity..."

CRITICAL_TABLES=(
    "identity.users"
    "identity.roles" 
    "identity.user_roles"
    "assets.assets"
    "automation.jobs"
    "automation.job_executions"
    "communication.notification_templates"
    "tool_catalog.tools"
    "tool_catalog.tool_capabilities"
    "tool_catalog.tool_patterns"
    "execution.executions"
    "execution.execution_steps"
    "execution.execution_queue"
)

MISSING_TABLES=()

for table in "${CRITICAL_TABLES[@]}"; do
    schema=$(echo $table | cut -d'.' -f1)
    table_name=$(echo $table | cut -d'.' -f2)
    
    EXISTS=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$schema' AND table_name = '$table_name';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$EXISTS" -eq "1" ]; then
        echo "✅ $table exists"
    else
        echo "❌ $table is MISSING!"
        MISSING_TABLES+=("$table")
    fi
done

# If any tables are missing, fail with helpful message
if [ ${#MISSING_TABLES[@]} -gt 0 ]; then
    echo ""
    echo "❌ CRITICAL ERROR: ${#MISSING_TABLES[@]} required tables are missing!"
    echo "Missing tables:"
    for table in "${MISSING_TABLES[@]}"; do
        echo "   - $table"
    done
    echo ""
    echo "💡 To fix this, run:"
    echo "   docker exec -i opsconductor-postgres psql -U opsconductor -d opsconductor < /home/opsconductor/opsconductor-ng/database/master-schema.sql"
    exit 1
fi

# Check if admin user exists
ADMIN_EXISTS=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM identity.users WHERE username = 'admin';" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$ADMIN_EXISTS" -eq "1" ]; then
    echo "✅ Admin user exists"
else
    echo "❌ Admin user is missing!"
    exit 1
fi

# Check assets count
ASSET_COUNT=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM assets.assets;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$ASSET_COUNT" -gt "0" ]; then
    echo "✅ Assets populated ($ASSET_COUNT assets)"
else
    echo "⚠️  No assets in database"
fi

# Check tool catalog
TOOL_COUNT=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM tool_catalog.tools;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$TOOL_COUNT" -gt "0" ]; then
    echo "✅ Tool catalog populated ($TOOL_COUNT tools)"
else
    echo "⚠️  Tool catalog is empty!"
fi

echo ""
echo "🎉 Database initialization complete!"
echo ""
echo "📊 Database Summary:"
echo "   - Total tables: $(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog');" | tr -d ' ')"
echo "   - Schemas: $(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog');" | tr -d ' ')"
echo "   - Users: $(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM identity.users;" | tr -d ' ')"
echo "   - Roles: $(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM identity.roles;" | tr -d ' ')"
echo "   - Assets: $(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM assets.assets;" | tr -d ' ')"
echo "   - Tools: $(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM tool_catalog.tools;" | tr -d ' ')"
echo "   - Executions: $(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "SELECT COUNT(*) FROM execution.executions;" | tr -d ' ')"
echo ""