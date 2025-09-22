#!/bin/bash

# OpsConductor Network Analyzer Service Deployment Script
# This script starts the network analyzer service with proper configuration

set -e

echo "🔍 Starting OpsConductor Network Analyzer Service..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")/.."

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please run from the project root."
    exit 1
fi

# Build and start the network analyzer service
echo "📦 Building network analyzer service..."
docker compose build network-analyzer-service

echo "🚀 Starting network analyzer service..."
docker compose up -d network-analyzer-service

# Wait for service to be healthy
echo "⏳ Waiting for service to be ready..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if docker compose ps network-analyzer-service | grep -q "healthy\|Up"; then
        echo "✅ Network Analyzer Service is ready!"
        echo ""
        echo "🌐 Service Information:"
        echo "   - Service URL: http://localhost:3006"
        echo "   - Health Check: http://localhost:3006/health"
        echo "   - API Documentation: http://localhost:3006/docs"
        echo "   - WebSocket Monitoring: ws://localhost:3006/ws/monitoring/{session_id}"
        echo ""
        echo "🔧 Available Capabilities:"
        echo "   - Packet capture and analysis"
        echo "   - Real-time network monitoring"
        echo "   - Protocol-specific analysis"
        echo "   - AI-powered network diagnosis"
        echo "   - Remote agent deployment"
        echo ""
        echo "📚 Documentation: See network-analyzer-service/README.md"
        break
    fi
    
    sleep 2
    counter=$((counter + 2))
    echo "   Waiting... ($counter/$timeout seconds)"
done

if [ $counter -ge $timeout ]; then
    echo "❌ Service failed to start within $timeout seconds"
    echo "📋 Service logs:"
    docker compose logs network-analyzer-service --tail=20
    exit 1
fi

echo ""
echo "🎉 Network Analyzer Service is now available for OpsConductor!"