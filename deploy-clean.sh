#!/bin/bash

# OpsConductor Clean Architecture Deployment Script

set -e

echo "🧹 OpsConductor Clean Architecture Deployment"
echo "=============================================="

# Check if docker-compose is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.clean.yml down --volumes --remove-orphans 2>/dev/null || true

# Clean up old images
echo "🧹 Cleaning up old images..."
docker system prune -f

# Build and start clean architecture
echo "🚀 Starting clean architecture..."
docker compose -f docker-compose.clean.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo "🔍 Checking service health..."

services=(
    "http://localhost:3005/health:AI Brain"
    "http://localhost:8001/health:Automation Service"
    "http://localhost:8002/health:Asset Service"
    "http://localhost:8003/health:Network Service"
    "http://localhost:8004/health:Communication Service"
)

all_healthy=true

for service in "${services[@]}"; do
    url=$(echo $service | cut -d: -f1-2)
    name=$(echo $service | cut -d: -f3)
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is not responding"
        all_healthy=false
    fi
done

if $all_healthy; then
    echo ""
    echo "🎉 Clean Architecture Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "🧠 AI Brain: http://localhost:3005"
    echo "📊 Architecture Status: http://localhost:3005/architecture"
    echo "🔧 Services Status: http://localhost:3005/services/status"
    echo ""
    echo "Test the system:"
    echo "curl -X POST http://localhost:3005/process \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"intent\": \"Check system status\", \"context\": {}}'"
    echo ""
else
    echo ""
    echo "⚠️  Some services are not healthy. Check logs:"
    echo "docker compose -f docker-compose.clean.yml logs"
    exit 1
fi