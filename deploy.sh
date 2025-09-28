#!/bin/bash

# Get the host IP dynamically
HOST_IP=$(hostname -I | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    HOST_IP="127.0.0.1"
    echo "⚠️  Warning: Could not detect host IP, using 127.0.0.1"
fi

echo "🚀 Deploying OpsConductor - New Architecture"
echo "============================================"
echo "🌐 Host IP: $HOST_IP"

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
echo "  API Gateway:        http://$HOST_IP:8080"
echo "  Identity Service:   http://$HOST_IP:3001"
echo "  Asset Service:      http://$HOST_IP:3002"
echo "  Automation Service: http://$HOST_IP:3003"
echo "  Communication:      http://$HOST_IP:3004"
echo "  Frontend:           http://$HOST_IP:3000"
echo "  Flower (Celery):    http://$HOST_IP:5555"
echo ""
echo "🔍 Health Checks:"
echo "  curl http://$HOST_IP:8080/health"
echo "  curl http://$HOST_IP:3001/health"
echo ""
echo "📝 View logs:"
echo "  docker compose logs -f [service-name]"
