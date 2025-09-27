#!/bin/bash

# OpsConductor V3 Phase 3: Monitoring Stack Startup Script
# This script starts the complete OpsConductor system with monitoring

set -e

echo "🚀 Starting OpsConductor V3 with Monitoring Stack..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

print_status "Stopping any existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose -f docker-compose.monitoring.yml down --remove-orphans 2>/dev/null || true

print_status "Creating shared network..."
docker network create opsconductor-net 2>/dev/null || print_warning "Network already exists"

print_status "Starting core OpsConductor services..."
docker-compose up -d

print_status "Waiting for core services to be healthy..."
sleep 30

# Check core services health
print_status "Checking core services health..."
SERVICES=("postgres" "redis" "keycloak" "kong" "identity-service" "asset-service")
for service in "${SERVICES[@]}"; do
    if docker-compose ps | grep -q "$service.*healthy\|$service.*Up"; then
        print_success "$service is running"
    else
        print_warning "$service may not be fully ready yet"
    fi
done

print_status "Starting monitoring stack..."
docker-compose -f docker-compose.monitoring.yml up -d

print_status "Waiting for monitoring services to start..."
sleep 20

# Check monitoring services
print_status "Checking monitoring services..."
MONITORING_SERVICES=("prometheus" "grafana" "alertmanager" "node-exporter" "cadvisor")
for service in "${MONITORING_SERVICES[@]}"; do
    if docker ps | grep -q "opsconductor-$service"; then
        print_success "$service is running"
    else
        print_warning "$service may not be ready yet"
    fi
done

echo ""
print_success "🎉 OpsConductor V3 with Monitoring Stack is starting up!"
echo ""
print_status "📊 Access URLs:"
echo "  • Main Application: http://localhost (Nginx)"
echo "  • Kong Gateway: http://localhost:3000"
echo "  • Keycloak Admin: http://localhost:8090"
echo "  • Grafana Dashboard: http://localhost:3100 (admin/admin123)"
echo "  • Prometheus: http://localhost:9090"
echo "  • AlertManager: http://localhost:9093"
echo "  • Celery Monitor: http://localhost:5555"
echo ""
print_status "🔧 Monitoring Endpoints:"
echo "  • Node Exporter: http://localhost:9100"
echo "  • cAdvisor: http://localhost:8081"
echo "  • Redis Exporter: http://localhost:9121"
echo "  • Postgres Exporter: http://localhost:9187"
echo ""
print_status "📝 To view logs:"
echo "  • Core services: docker-compose logs -f [service-name]"
echo "  • Monitoring: docker-compose -f docker-compose.monitoring.yml logs -f [service-name]"
echo ""
print_status "🛑 To stop everything:"
echo "  • ./stop-monitoring.sh"
echo ""

# Wait a bit more and do final health check
sleep 10
print_status "Final health check..."

# Check if Prometheus is accessible
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    print_success "Prometheus is healthy"
else
    print_warning "Prometheus may still be starting up"
fi

# Check if Grafana is accessible
if curl -s http://localhost:3100/api/health > /dev/null; then
    print_success "Grafana is healthy"
else
    print_warning "Grafana may still be starting up"
fi

print_success "✅ Phase 3 Monitoring Stack deployment complete!"
print_status "🔍 Check service status with: docker-compose ps && docker-compose -f docker-compose.monitoring.yml ps"