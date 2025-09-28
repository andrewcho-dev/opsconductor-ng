#!/bin/bash

# OpsConductor V3 - Phase 5: Traefik Deployment Script
# Deploy Traefik reverse proxy alongside existing Kong Gateway

set -e

# Get the host IP dynamically
HOST_IP=$(hostname -I | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    HOST_IP="127.0.0.1"
    echo "⚠️  Warning: Could not detect host IP, using 127.0.0.1"
fi

echo "🚀 OpsConductor V3 - Phase 5: Traefik Deployment"
echo "=================================================="
echo "🌐 Host IP: $HOST_IP"

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
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version > /dev/null 2>&1; then
    print_error "docker compose is not available. Please install Docker Compose and try again."
    exit 1
fi

print_status "Checking current OpsConductor services..."

# Check if OpsConductor network exists
if ! docker network ls | grep -q opsconductor-net; then
    print_warning "OpsConductor network not found. Creating network..."
    docker network create opsconductor-net
    print_success "Created opsconductor-net network"
fi

# Check if core services are running
REQUIRED_SERVICES=("opsconductor-kong" "opsconductor-frontend")
MISSING_SERVICES=()

for service in "${REQUIRED_SERVICES[@]}"; do
    if ! docker ps | grep -q "$service"; then
        MISSING_SERVICES+=("$service")
    fi
done

if [ ${#MISSING_SERVICES[@]} -gt 0 ]; then
    print_warning "Some required services are not running: ${MISSING_SERVICES[*]}"
    print_status "Starting core OpsConductor services first..."
    
    # Start core services if not running
    docker compose up -d kong frontend
    
    # Wait for services to be healthy
    print_status "Waiting for core services to be healthy..."
    sleep 30
fi

print_status "Building Traefik image..."
docker compose -f docker-compose.traefik-simple.yml build traefik

print_status "Starting Traefik reverse proxy..."
docker compose -f docker-compose.traefik-simple.yml up -d traefik

# Wait for Traefik to start
print_status "Waiting for Traefik to start..."
sleep 15

# Check Traefik health
if docker ps | grep -q "opsconductor-traefik"; then
    print_success "Traefik container is running"
    
    # Check if Traefik dashboard is accessible
    if curl -s -f http://$HOST_IP:8081/ping > /dev/null; then
        print_success "Traefik dashboard is accessible"
    else
        print_warning "Traefik dashboard is not yet accessible (may still be starting)"
    fi
else
    print_error "Traefik container failed to start"
    docker compose -f docker-compose.traefik-simple.yml logs traefik
    exit 1
fi

print_status "Checking service discovery..."

# Test if Traefik can discover services
TRAEFIK_API="http://$HOST_IP:8081/api/http/routers"
if curl -s "$TRAEFIK_API" | grep -q "kong-api"; then
    print_success "Traefik discovered Kong Gateway service"
else
    print_warning "Traefik has not yet discovered Kong Gateway (may take a moment)"
fi

if curl -s "$TRAEFIK_API" | grep -q "frontend"; then
    print_success "Traefik discovered Frontend service"
else
    print_warning "Traefik has not yet discovered Frontend service (may take a moment)"
fi

print_status "Testing Traefik routing..."

# Test API routing through Traefik (port 8082)
if curl -s -f http://$HOST_IP:8082/health > /dev/null; then
    print_success "API routing through Traefik is working"
else
    print_warning "API routing through Traefik is not yet working (services may still be starting)"
fi

# Test frontend routing through Traefik
if curl -s -f http://$HOST_IP:8082/ > /dev/null; then
    print_success "Frontend routing through Traefik is working"
else
    print_warning "Frontend routing through Traefik is not yet working"
fi

echo ""
print_success "Traefik deployment completed!"
echo ""
echo "📊 Access Information:"
echo "  • Traefik Dashboard: http://$HOST_IP:8081/dashboard/"
echo "  • Traefik API: http://$HOST_IP:8081/api/"
echo "  • OpsConductor (via Traefik): http://$HOST_IP:8082/"
echo "  • OpsConductor API (via Traefik): http://$HOST_IP:8082/api/"
echo "  • Prometheus Metrics: http://$HOST_IP:8081/metrics"
echo ""
echo "🔐 Dashboard Credentials:"
echo "  • Username: admin"
echo "  • Password: admin123"
echo ""
echo "📋 Next Steps:"
echo "  1. Test all routes through Traefik (port 8082)"
echo "  2. Compare performance with Kong direct access (port 3000)"
echo "  3. Run: ./test-traefik.sh to validate all functionality"
echo "  4. When ready, run: ./migrate-to-traefik.sh to complete migration"
echo ""
print_warning "Note: Traefik is running on port 8082 for testing alongside Kong on port 3000."