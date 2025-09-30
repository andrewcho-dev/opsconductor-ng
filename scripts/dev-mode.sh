#!/bin/bash

# OpsConductor Development Mode
# Starts the system with volume mounts for live file changes

set -e

echo "🚀 Starting OpsConductor in DEVELOPMENT MODE"
echo "   - Live file changes enabled"
echo "   - Volume mounts active"
echo "   - Fast iteration mode"
echo ""

# Check if docker-compose.dev.yml exists
if [ ! -f "docker-compose.dev.yml" ]; then
    echo "❌ ERROR: docker-compose.dev.yml not found!"
    echo "   Make sure you're running this from the project root directory."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker compose -f docker-compose.clean.yml down 2>/dev/null || true
docker compose -f docker-compose.dev.yml down 2>/dev/null || true

# Build and start development environment
echo "🔨 Building and starting development environment..."
docker compose -f docker-compose.dev.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker compose -f docker-compose.dev.yml ps

echo ""
echo "✅ OpsConductor DEVELOPMENT MODE is running!"
echo ""
echo "📋 Service URLs:"
echo "   🧠 AI Brain:        http://localhost:3005"
echo "   🤖 Automation:      http://localhost:8001"
echo "   📦 Assets:          http://localhost:8002"
echo "   🌐 Network:         http://localhost:8003"
echo "   💬 Communication:   http://localhost:8004"
echo "   🔐 Identity:        http://localhost:8005"
echo "   🎨 Frontend:        http://localhost:3000"
echo "   🔄 Prefect:         http://localhost:4200"
echo ""
echo "📝 Development Features:"
echo "   - File changes are reflected immediately"
echo "   - No need to rebuild containers for code changes"
echo "   - Shared directory is live-mounted"
echo "   - Frontend has hot reload enabled"
echo ""
echo "🔧 Useful Commands:"
echo "   ./scripts/status.sh     - Check service status"
echo "   ./scripts/logs.sh       - View service logs"
echo "   ./scripts/stop-dev.sh   - Stop development mode"
echo "   ./scripts/prod-mode.sh  - Switch to production mode"
echo ""