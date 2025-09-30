#!/bin/bash

# Check OpsConductor Status

set -e

echo "📊 OpsConductor System Status"
echo "=============================="
echo ""

# Check which mode is running
DEV_RUNNING=$(docker compose -f docker-compose.dev.yml ps --services --filter "status=running" 2>/dev/null | wc -l)
PROD_RUNNING=$(docker compose -f docker-compose.clean.yml ps --services --filter "status=running" 2>/dev/null | wc -l)

if [ "$DEV_RUNNING" -gt 0 ]; then
    echo "🚀 Mode: DEVELOPMENT (with volume mounts)"
    echo "📋 Services:"
    docker compose -f docker-compose.dev.yml ps
    echo ""
    echo "📝 Development Features Active:"
    echo "   ✅ Live file changes"
    echo "   ✅ Volume mounts"
    echo "   ✅ Hot reload (frontend)"
    echo ""
elif [ "$PROD_RUNNING" -gt 0 ]; then
    echo "🏭 Mode: PRODUCTION (no volume mounts)"
    echo "📋 Services:"
    docker compose -f docker-compose.clean.yml ps
    echo ""
    echo "🏭 Production Features Active:"
    echo "   ✅ Self-contained containers"
    echo "   ✅ No host dependencies"
    echo "   ⚠️  File changes require rebuild"
    echo ""
else
    echo "😴 Status: NOT RUNNING"
    echo ""
    echo "🔧 Start Options:"
    echo "   ./scripts/dev-mode.sh   - Development mode (live changes)"
    echo "   ./scripts/prod-mode.sh  - Production mode (containers only)"
    echo ""
    exit 0
fi

# Check service health
echo "🏥 Health Checks:"
echo "=================="

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local timeout=5
    
    if curl -f -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo "   ✅ $service_name: Healthy"
    else
        echo "   ❌ $service_name: Unhealthy or not responding"
    fi
}

check_service "AI Brain" "http://localhost:3005/health"
check_service "Automation Service" "http://localhost:8001/health"
check_service "Asset Service" "http://localhost:8002/health"
check_service "Network Service" "http://localhost:8003/health"
check_service "Communication Service" "http://localhost:8004/health"
check_service "Identity Service" "http://localhost:8005/health"
check_service "Prefect Server" "http://localhost:4200/api/health"

if [ "$DEV_RUNNING" -gt 0 ]; then
    check_service "Frontend (Dev)" "http://localhost:3000"
fi

echo ""
echo "🔧 Management Commands:"
echo "======================="
echo "   ./scripts/logs.sh       - View service logs"
echo "   ./scripts/restart.sh    - Restart services"
if [ "$DEV_RUNNING" -gt 0 ]; then
    echo "   ./scripts/stop-dev.sh   - Stop development mode"
    echo "   ./scripts/prod-mode.sh  - Switch to production mode"
else
    echo "   ./scripts/stop-prod.sh  - Stop production mode"
    echo "   ./scripts/dev-mode.sh   - Switch to development mode"
fi
echo ""