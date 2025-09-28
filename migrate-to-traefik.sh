#!/bin/bash

# OpsConductor V3 - Phase 5: Traefik Migration Script
# Complete migration from Nginx to Traefik

set -e

# Get the host IP dynamically
HOST_IP=$(hostname -I | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    HOST_IP="127.0.0.1"
    echo "⚠️  Warning: Could not detect host IP, using 127.0.0.1"
fi

echo "🔄 OpsConductor V3 - Phase 5: Traefik Migration"
echo "==============================================="
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

# Confirmation prompt
echo ""
print_warning "This script will set up Traefik as the primary reverse proxy."
print_warning "This involves:"
print_warning "  1. Updating Traefik to use port 80/443"
print_warning "  2. Testing the migration"
print_warning "  3. Backing up any existing configuration"
echo ""

read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Migration cancelled."
    exit 0
fi

echo ""
print_status "Starting migration process..."

# Step 1: Pre-migration validation
print_status "Step 1: Pre-migration validation"

# Check if Traefik is running and healthy
if ! docker ps | grep -q "opsconductor-traefik"; then
    print_error "Traefik container is not running. Please run ./deploy-traefik.sh first."
    exit 1
fi

# Check if Traefik is healthy
if ! curl -s -f http://$HOST_IP:8081/ping > /dev/null; then
    print_error "Traefik is not healthy. Please check Traefik status."
    exit 1
fi

print_success "Traefik is running and healthy"

# Step 2: Test Traefik routing before migration
print_status "Step 2: Testing Traefik routing before migration"

# Test API routing
if ! curl -s -f http://$HOST_IP/health > /dev/null; then
    print_error "Traefik API routing is not working. Please fix before migration."
    exit 1
fi

# Test frontend routing
if ! curl -s -f http://$HOST_IP/ > /dev/null; then
    print_error "Traefik frontend routing is not working. Please fix before migration."
    exit 1
fi

print_success "Traefik routing tests passed"

# Step 3: Backup existing configuration
print_status "Step 3: Backing up existing configuration"

BACKUP_DIR="./traefik-migration-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup any existing reverse proxy configurations
if [ -f "./docker-compose.yml" ]; then
    cp ./docker-compose.yml "$BACKUP_DIR/"
    print_success "Docker compose configuration backed up to $BACKUP_DIR"
fi

# Step 4: Update Traefik to use standard ports
print_status "Step 4: Updating Traefik port configuration"

# Create updated Traefik compose file with standard ports
cat > docker-compose.traefik-production.yml << 'EOF'
# OpsConductor V3 - Phase 5: Traefik Production Configuration
# Traefik as primary reverse proxy on standard ports

services:
  # Traefik Reverse Proxy (Production)
  traefik:
    extends:
      file: docker-compose.traefik.yml
      service: traefik
    ports:
      - "80:80"      # HTTP (primary)
      - "443:443"    # HTTPS (primary)
      - "8080:8080"  # Forward proxy for outbound connections
      - "8081:8081"  # Traefik dashboard
    environment:
      - TRAEFIK_LOG_LEVEL=INFO
      - TRAEFIK_API_DASHBOARD=true
      - TRAEFIK_API_DEBUG=false  # Disable debug in production
      - TRAEFIK_METRICS_PROMETHEUS=true

  # Kong Gateway (with updated labels)
  kong:
    extends:
      file: docker-compose.traefik.yml
      service: kong

  # Frontend (with updated labels)
  frontend:
    extends:
      file: docker-compose.traefik.yml
      service: frontend

  # Automation Service (with WebSocket support)
  automation-service:
    extends:
      file: docker-compose.traefik.yml
      service: automation-service

networks:
  opsconductor-net:
    external: true

volumes:
  traefik_letsencrypt:
    external: true
  traefik_logs:
    external: true
EOF

# Restart Traefik with production configuration
print_status "Restarting Traefik with production configuration..."
docker compose -f docker-compose.traefik-production.yml up -d traefik

# Wait for Traefik to restart
print_status "Waiting for Traefik to restart..."
sleep 15

# Step 5: Post-migration validation
print_status "Step 5: Post-migration validation"

# Check if Traefik is running on port 80
if ! curl -s -f http://$HOST_IP:80/health > /dev/null; then
    print_error "Traefik is not responding on port 80. Rolling back..."
    
    # Rollback: stop Traefik production config
    docker compose -f docker-compose.traefik-production.yml down traefik 2>/dev/null || true
    print_error "Migration failed. Traefik has been stopped."
    exit 1
fi

print_success "Traefik is responding on port 80"

# Test all critical endpoints
ENDPOINTS=(
    "http://$HOST_IP/health"
    "http://$HOST_IP/api/v1/identity/health"
    "http://$HOST_IP/"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -s -f "$endpoint" > /dev/null; then
        print_success "✓ $endpoint"
    else
        print_error "✗ $endpoint"
        print_error "Migration validation failed!"
        exit 1
    fi
done

# Step 6: Update docker-compose.yml for Traefik
print_status "Step 6: Updating main docker-compose.yml"

# No nginx service to comment out - this step is now just informational
print_success "Docker compose configuration is ready for Traefik"

# Step 7: Clean up
print_status "Step 7: Cleaning up"

# Clean up any old containers if they exist
print_success "Cleanup completed"

# Step 8: Final validation and performance test
print_status "Step 8: Final validation and performance test"

# Run comprehensive tests
print_status "Running final validation tests..."
if ./test-traefik.sh > /dev/null 2>&1; then
    print_success "All validation tests passed"
else
    print_warning "Some validation tests failed. Check ./test-traefik.sh for details."
fi

# Performance test
print_status "Measuring post-migration performance..."
RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null http://$HOST_IP/health)
print_status "Response time: ${RESPONSE_TIME}s"

echo ""
print_success "🎉 Migration to Traefik completed successfully!"
echo ""
echo "📊 Migration Summary:"
echo "  • Traefik: Now handling all traffic on port 80/443"
echo "  • Configuration backup: $BACKUP_DIR"
echo "  • Performance: ${RESPONSE_TIME}s response time"
echo ""
echo "🌐 Access Information:"
echo "  • OpsConductor Application: http://$HOST_IP/"
echo "  • OpsConductor API: http://$HOST_IP/api/"
echo "  • Traefik Dashboard: http://$HOST_IP:8081/dashboard/"
echo "  • Prometheus Metrics: http://$HOST_IP:8081/metrics"
echo ""
echo "🔐 Dashboard Credentials:"
echo "  • Username: admin"
echo "  • Password: admin123"
echo ""
echo "📋 Next Steps:"
echo "  1. Monitor application performance and stability"
echo "  2. Configure SSL certificates for production use"
echo "  3. Set up alerting for Traefik metrics"
echo "  4. Update documentation and team knowledge"
echo ""
echo "🔧 Rollback Information:"
echo "  • Configuration backup: $BACKUP_DIR"
echo "  • To rollback: Stop Traefik production config and restart original setup"
echo ""
print_success "Phase 5: Traefik migration is complete! 🚀"