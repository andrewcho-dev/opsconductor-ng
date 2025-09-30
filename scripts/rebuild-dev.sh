#!/bin/bash

# OpsConductor Development Rebuild
# Force complete rebuild of development environment

set -e

echo "🔨 OpsConductor COMPLETE DEVELOPMENT REBUILD"
echo "============================================"
echo ""

# Check if docker-compose.dev.yml exists
if [ ! -f "docker-compose.dev.yml" ]; then
    echo "❌ ERROR: docker-compose.dev.yml not found!"
    echo "   Make sure you're running this from the project root directory."
    exit 1
fi

# Stop everything
echo "🛑 Stopping all containers..."
docker compose -f docker-compose.dev.yml down 2>/dev/null || true
docker compose -f docker-compose.clean.yml down 2>/dev/null || true

# Remove all OpsConductor containers
echo "🗑️  Removing all OpsConductor containers..."
docker ps -a --format "{{.Names}}" | grep opsconductor | xargs -r docker rm -f 2>/dev/null || true

# Remove all OpsConductor images
echo "🗑️  Removing all OpsConductor images..."
docker images --format "{{.Repository}}:{{.Tag}}" | grep opsconductor | xargs -r docker rmi -f 2>/dev/null || true

# Clean build cache
echo "🧹 Cleaning Docker build cache..."
docker builder prune -f 2>/dev/null || true

# Remove orphaned volumes (but keep data volumes)
echo "🧹 Cleaning orphaned volumes..."
docker volume ls -q | grep -v -E "(postgres_data|redis_data|ollama_models|prefect_data)" | xargs -r docker volume rm 2>/dev/null || true

# Rebuild everything from scratch
echo "🔨 Rebuilding everything from scratch..."
docker compose -f docker-compose.dev.yml build --no-cache --pull

# Start the system
echo "🚀 Starting rebuilt development environment..."
docker compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check service health
echo "🏥 Checking service health..."
docker compose -f docker-compose.dev.yml ps

echo ""
echo "✅ COMPLETE REBUILD FINISHED!"
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
echo "🔧 Useful Commands:"
echo "   ./scripts/status.sh     - Check service status"
echo "   ./scripts/logs.sh       - View service logs"
echo "   ./scripts/validate-mounts.sh - Validate configuration"
echo ""