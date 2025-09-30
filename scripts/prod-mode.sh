#!/bin/bash

# OpsConductor Production Mode
# Starts the system without volume mounts (production-like)

set -e

echo "🏭 Starting OpsConductor in PRODUCTION MODE"
echo "   - No volume mounts"
echo "   - Self-contained containers"
echo "   - Production-like environment"
echo ""

# Check if docker-compose.clean.yml exists
if [ ! -f "docker-compose.clean.yml" ]; then
    echo "❌ ERROR: docker-compose.clean.yml not found!"
    echo "   Make sure you're running this from the project root directory."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker compose -f docker-compose.dev.yml down 2>/dev/null || true
docker compose -f docker-compose.clean.yml down 2>/dev/null || true

# Build and start production environment
echo "🔨 Building and starting production environment..."
docker compose -f docker-compose.clean.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker compose -f docker-compose.clean.yml ps

echo ""
echo "✅ OpsConductor PRODUCTION MODE is running!"
echo ""
echo "📋 Service URLs:"
echo "   🧠 AI Brain:        http://localhost:3005"
echo "   🤖 Automation:      http://localhost:8001"
echo "   📦 Assets:          http://localhost:8002"
echo "   🌐 Network:         http://localhost:8003"
echo "   💬 Communication:   http://localhost:8004"
echo "   🔄 Prefect:         http://localhost:4200"
echo ""
echo "🏭 Production Features:"
echo "   - All code baked into containers"
echo "   - No host file dependencies"
echo "   - Self-contained and portable"
echo "   - Production-ready configuration"
echo ""
echo "⚠️  Note: File changes require container rebuild"
echo "   Use './scripts/dev-mode.sh' for development with live changes"
echo ""
echo "🔧 Useful Commands:"
echo "   ./scripts/status.sh     - Check service status"
echo "   ./scripts/logs.sh       - View service logs"
echo "   ./scripts/stop-prod.sh  - Stop production mode"
echo "   ./scripts/dev-mode.sh   - Switch to development mode"
echo ""