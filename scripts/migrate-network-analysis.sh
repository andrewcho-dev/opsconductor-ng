#!/bin/bash

# Script to migrate existing OpsConductor database to include Network Analysis schema
# This script should be run if you have an existing OpsConductor installation

set -e

echo "🔄 Migrating OpsConductor database to include Network Analysis schema..."

# Database connection parameters
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-opsconductor}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres123}

# Check if database is accessible
echo "📡 Testing database connection..."
if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ Cannot connect to database. Please check your connection parameters."
    echo "   DB_HOST: $DB_HOST"
    echo "   DB_PORT: $DB_PORT"
    echo "   DB_NAME: $DB_NAME"
    echo "   DB_USER: $DB_USER"
    exit 1
fi

echo "✅ Database connection successful"

# Apply migration
echo "🚀 Applying Network Analysis schema migration..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f ../database/migrate-network-analysis.sql

if [ $? -eq 0 ]; then
    echo "✅ Network Analysis schema migration completed successfully!"
    echo ""
    echo "📊 Database now includes the following new tables:"
    echo "   - network_analysis.remote_probes"
    echo "   - network_analysis.capture_sessions"
    echo "   - network_analysis.capture_results"
    echo "   - network_analysis.monitoring_data"
    echo "   - network_analysis.network_alerts"
    echo "   - network_analysis.analysis_jobs"
    echo "   - network_analysis.protocol_analysis"
    echo "   - network_analysis.ai_analysis"
    echo ""
    echo "🎯 Your OpsConductor system is now ready to accept remote probes!"
else
    echo "❌ Migration failed. Please check the error messages above."
    exit 1
fi