#!/bin/bash

# OpsConductor V3 Phase 3: Stop Monitoring Stack Script

set -e

echo "🛑 Stopping OpsConductor V3 with Monitoring Stack..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_status "Stopping monitoring stack..."
docker-compose -f docker-compose.monitoring.yml down --remove-orphans

print_status "Stopping core services..."
docker-compose down --remove-orphans

print_status "Cleaning up unused containers and networks..."
docker system prune -f --volumes

print_success "✅ All services stopped successfully!"
print_status "💾 Data volumes are preserved. Use 'docker volume prune' to remove them if needed."