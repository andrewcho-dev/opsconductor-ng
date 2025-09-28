#!/bin/bash

echo "🚀 Deploying OpsConductor - New Architecture"
echo "============================================"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down --remove-orphans

# Build and start services
echo "🏗️  Building and starting services..."
docker compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
services=("postgres" "redis" "api-gateway" "identity-service" "asset-service" "automation-service" "communication-service")

for service in "${services[@]}"; do
    if docker compose ps "$service" | grep -q "healthy\|Up"; then
        echo "  ✅ $service is running"
    else
        echo "  ❌ $service is not healthy"
    fi
done

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "  API Gateway:        http://localhost:8080"
echo "  Identity Service:   http://localhost:3001"
echo "  Asset Service:      http://localhost:3002"
echo "  Automation Service: http://localhost:3003"
echo "  Communication:      http://localhost:3004"
echo "  Frontend:           http://localhost:3000"
echo "  Flower (Celery):    http://localhost:5555"
echo ""
echo "🔍 Health Checks:"
echo "  curl http://localhost:8080/health"
echo "  curl http://localhost:3001/health"
echo ""
echo "📝 View logs:"
echo "  docker compose logs -f [service-name]"
