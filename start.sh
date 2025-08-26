#!/bin/bash

echo "🚀 Starting Microservice System..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🔧 Building and starting services..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "🔍 Checking service health..."

# Check if containers are running
services=("user-db" "auth-db" "user-service" "auth-service" "frontend" "nginx")
all_healthy=true

for service in "${services[@]}"; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service.*Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    echo "🎉 All services are running successfully!"
    echo ""
    echo "🌐 Access your application:"
    echo "   HTTPS: https://localhost (with self-signed certificate)"
    echo "   HTTP:  http://localhost (redirects to HTTPS)"
    echo ""
    echo "📝 Test credentials (register first or use these after registering):"
    echo "   Username: testuser"
    echo "   Password: testpass123"
    echo ""
    echo "🔧 Service endpoints (for debugging):"
    echo "   Frontend:  https://localhost/"
    echo "   Auth API:  https://localhost/auth/"
    echo "   User API:  https://localhost/users/"
    echo ""
    echo "📊 View logs:"
    echo "   sg docker -c 'docker compose logs -f [service-name]'"
    echo ""
    echo "🛑 Stop services:"
    echo "   sg docker -c 'docker compose down'"
else
    echo "❌ Some services failed to start. Check logs with:"
    echo "   docker-compose logs"
fi