#!/bin/bash
# Database initialization script for OpsConductor
# This script ensures the database is properly initialized with all required tables and data

set -e

echo "🔧 Initializing OpsConductor database..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec opsconductor-postgres pg_isready -U postgres; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Check if database exists and has tables
TABLE_COUNT=$(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog');" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$TABLE_COUNT" -eq "0" ]; then
    echo "📋 Database is empty. Initializing complete schema..."
    docker exec -i opsconductor-postgres psql -U postgres -d opsconductor < /home/opsconductor/opsconductor-ng/database/complete-schema.sql
    echo "✅ Database schema initialized successfully!"
else
    echo "📊 Database already has $TABLE_COUNT tables. Checking for missing components..."
    
    # Check for specific tables and add them if missing
    ENHANCED_TARGETS=$(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'assets' AND table_name = 'enhanced_targets';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$ENHANCED_TARGETS" -eq "0" ]; then
        echo "🔄 Adding missing enhanced targets schema..."
        docker exec -i opsconductor-postgres psql -U postgres -d opsconductor < /home/opsconductor/opsconductor-ng/database/complete-schema.sql
        echo "✅ Enhanced targets schema added!"
    fi
    
    # Check for service definitions
    SERVICE_DEFS=$(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'assets' AND table_name = 'service_definitions';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$SERVICE_DEFS" -eq "0" ]; then
        echo "🔄 Adding service definitions table..."
        docker exec -i opsconductor-postgres psql -U postgres -d opsconductor < /home/opsconductor/opsconductor-ng/database/complete-schema.sql
        echo "✅ Service definitions added!"
    fi
fi

# Verify critical tables exist
echo "🔍 Verifying database integrity..."

CRITICAL_TABLES=(
    "identity.users"
    "identity.roles" 
    "identity.user_roles"
    "assets.enhanced_targets"
    "assets.target_services"
    "assets.service_definitions"
    "automation.jobs"
    "automation.job_executions"
    "communication.notification_templates"
)

for table in "${CRITICAL_TABLES[@]}"; do
    schema=$(echo $table | cut -d'.' -f1)
    table_name=$(echo $table | cut -d'.' -f2)
    
    EXISTS=$(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$schema' AND table_name = '$table_name';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$EXISTS" -eq "1" ]; then
        echo "✅ $table exists"
    else
        echo "❌ $table is missing!"
        exit 1
    fi
done

# Check if admin user exists
ADMIN_EXISTS=$(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM identity.users WHERE username = 'admin';" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$ADMIN_EXISTS" -eq "1" ]; then
    echo "✅ Admin user exists"
else
    echo "❌ Admin user is missing!"
    exit 1
fi

# Check service definitions count
SERVICE_COUNT=$(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM assets.service_definitions;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$SERVICE_COUNT" -gt "20" ]; then
    echo "✅ Service definitions populated ($SERVICE_COUNT services)"
else
    echo "⚠️  Service definitions may be incomplete ($SERVICE_COUNT services)"
fi

echo "🎉 Database initialization complete!"
echo ""
echo "📊 Database Summary:"
echo "   - Total tables: $(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog');" | tr -d ' ')"
echo "   - Users: $(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM identity.users;" | tr -d ' ')"
echo "   - Roles: $(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM identity.roles;" | tr -d ' ')"
echo "   - Enhanced targets: $(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM assets.enhanced_targets;" | tr -d ' ')"
echo "   - Service definitions: $(docker exec opsconductor-postgres psql -U postgres -d opsconductor -t -c "SELECT COUNT(*) FROM assets.service_definitions;" | tr -d ' ')"
echo ""