#!/bin/bash

# Update OpsConductor Services with Metrics Support
# This script rebuilds and restarts all services to include Prometheus metrics

set -e

echo "🔧 Updating OpsConductor services with Prometheus metrics support..."

# Services to update
SERVICES=(
    "identity-service"
    "asset-service" 
    "automation-service"
    "communication-service"
    "ai-brain"
    "network-analyzer-service"
)

# Function to update a service
update_service() {
    local service=$1
    echo "📦 Building $service..."
    docker compose build --no-cache $service
    
    echo "🔄 Restarting $service..."
    docker compose up -d $service
    
    # Wait for service to be healthy
    echo "⏳ Waiting for $service to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose ps $service | grep -q "healthy"; then
            echo "✅ $service is healthy"
            break
        elif [ $attempt -eq $max_attempts ]; then
            echo "❌ $service failed to become healthy"
            return 1
        else
            echo "   Attempt $attempt/$max_attempts - waiting..."
            sleep 2
            ((attempt++))
        fi
    done
}

# Update each service
for service in "${SERVICES[@]}"; do
    echo ""
    echo "🚀 Updating $service..."
    update_service $service
done

echo ""
echo "🎉 All services updated successfully!"
echo ""
echo "📊 Testing metrics endpoints..."

# Test metrics endpoints
for service in "${SERVICES[@]}"; do
    case $service in
        "identity-service") port=3001 ;;
        "asset-service") port=3002 ;;
        "automation-service") port=3003 ;;
        "communication-service") port=3004 ;;
        "ai-brain") port=3005 ;;
        "network-analyzer-service") port=3006 ;;
    esac
    
    echo "Testing $service metrics at http://localhost:$port/metrics"
    if curl -s -f http://localhost:$port/metrics > /dev/null; then
        echo "✅ $service metrics endpoint working"
    else
        echo "❌ $service metrics endpoint not responding"
    fi
done

echo ""
echo "🔍 Checking Prometheus targets..."
echo "Visit http://localhost:9090/targets to verify all services are being scraped"
echo ""
echo "📈 Grafana available at http://localhost:3200 (admin/admin)"
echo "📊 Prometheus available at http://localhost:9090"