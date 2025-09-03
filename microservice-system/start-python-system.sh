#!/bin/bash

# OpsConductor Python System Startup Script
# Complete rebuild with Python FastAPI backend and React TypeScript frontend

set -e

echo "🚀 Starting OpsConductor Python System..."

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
$COMPOSE_CMD -f docker-compose-python.yml down --remove-orphans || true

# Run compliance check before building
echo "🔍 Running compliance check..."
if ! ./scripts/pre-build-check.sh; then
    echo "❌ Build aborted due to compliance violations"
    exit 1
fi

# Build and start services
echo "🏗️  Building and starting services..."
$COMPOSE_CMD -f docker-compose-python.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🩺 Checking service health..."

SERVICES=("auth-service:3001" "user-service:3002" "credentials-service:3004" "targets-service:3005" "jobs-service:3006" "executor-service:3007" "scheduler-service:3008" "notification-service:3009" "discovery-service:3010" "step-libraries-service:3011")

for service in "${SERVICES[@]}"; do
    IFS=':' read -ra ADDR <<< "$service"
    service_name=${ADDR[0]}
    port=${ADDR[1]}
    
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo "✅ $service_name is healthy"
    else
        echo "❌ $service_name is not responding"
    fi
done

# Check frontend
if curl -f -s "http://localhost:3000" > /dev/null; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend is not responding"
fi

echo "🎉 System startup complete!"
echo ""
echo "🌐 Access the system:"
echo "   Frontend: http://localhost:3000"
echo "   Auth Service: http://localhost:3001"
echo "   User Service: http://localhost:3002" 
echo "   Credentials Service: http://localhost:3004"
echo "   Targets Service: http://localhost:3005"
echo "   Jobs Service: http://localhost:3006"
echo "   Executor Service: http://localhost:3007"
echo "   Scheduler Service: http://localhost:3008"
echo "   Notification Service: http://localhost:3009"
echo "   Discovery Service: http://localhost:3010"
echo "   Step Libraries Service: http://localhost:3011"
echo ""
echo "📋 Default login credentials:"
echo "   Admin: admin / admin123"
echo "   Operator: operator / admin123"
echo "   Viewer: viewer / admin123"
echo ""
echo "📊 To view logs: docker-compose -f docker-compose-python.yml logs -f [service-name]"
echo "🛑 To stop system: docker-compose -f docker-compose-python.yml down"