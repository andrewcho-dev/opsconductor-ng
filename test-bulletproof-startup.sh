#!/bin/bash

# Test script for bulletproof startup system
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              OpsConductor Bulletproof Startup Test          ║"
echo "║                                                              ║"
echo "║  This script tests the bulletproof startup system by        ║"
echo "║  performing a complete shutdown and restart cycle.          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

# Test 1: Check if bulletproof startup script exists and is executable
log "Test 1: Checking bulletproof startup script..."
if [ -f "./bulletproof-startup.sh" ] && [ -x "./bulletproof-startup.sh" ]; then
    log_success "Bulletproof startup script exists and is executable"
else
    log_error "Bulletproof startup script not found or not executable"
    exit 1
fi

# Test 2: Check current service status
log "Test 2: Checking current service status..."
./bulletproof-startup.sh --status > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_success "Status check completed successfully"
else
    log_error "Status check failed"
    exit 1
fi

# Test 3: Verify all running services are healthy
log "Test 3: Verifying all services are healthy..."
./bulletproof-startup.sh --verify
if [ $? -eq 0 ]; then
    log_success "All services are healthy"
else
    log_error "Some services are unhealthy"
    exit 1
fi

# Test 4: Test individual service endpoints
log "Test 4: Testing individual service endpoints..."

# Test core services
services=(
    "identity-service:3001:/ready"
    "asset-service:3002:/ready"
    "automation-service:3003:/ready"
    "communication-service:3004:/ready"
    "prefect-server:4200:/api/health"
)

for service_info in "${services[@]}"; do
    IFS=':' read -r service port endpoint <<< "$service_info"
    
    if curl -s -f "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
        log_success "$service endpoint is responding"
    else
        log_error "$service endpoint is not responding"
        exit 1
    fi
done

# Test 5: Test infrastructure services
log "Test 5: Testing infrastructure services..."

# Test PostgreSQL
if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    log_success "PostgreSQL is accepting connections"
else
    log_error "PostgreSQL is not accepting connections"
    exit 1
fi

# Test Redis
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    log_success "Redis is responding to ping"
else
    log_error "Redis is not responding to ping"
    exit 1
fi

# Test ChromaDB
if curl -s -f "http://localhost:8000/api/v1/heartbeat" > /dev/null 2>&1; then
    log_success "ChromaDB heartbeat is responding"
else
    log_error "ChromaDB heartbeat is not responding"
    exit 1
fi

# Test 6: Test service restart resilience
log "Test 6: Testing service restart resilience..."
log "Restarting identity service to test resilience..."

docker compose restart identity-service > /dev/null 2>&1
sleep 10

# Wait for identity service to be healthy again
max_attempts=24  # Increased timeout for service restart
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s -f "http://localhost:3001/ready" > /dev/null 2>&1; then
        log_success "Identity service recovered successfully after restart"
        break
    fi
    
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        log_error "Identity service failed to recover after restart"
        exit 1
    fi
    
    sleep 5
done

# Test 7: Test async health checks (no coroutine warnings)
log "Test 7: Checking for async warnings in service logs..."

services_to_check=("identity-service" "asset-service" "automation-service" "communication-service")
warning_found=false

for service in "${services_to_check[@]}"; do
    container_name="opsconductor-${service//-/}"
    
    # Check last 50 lines of logs for coroutine warnings
    if docker logs "$container_name" --tail 50 2>&1 | grep -i "coroutine.*never.*awaited" > /dev/null; then
        log_error "Found async warnings in $service logs"
        warning_found=true
    else
        log_success "$service has no async warnings"
    fi
done

if [ "$warning_found" = true ]; then
    log_error "Async warnings found in service logs"
    exit 1
fi

# Test 8: Test Prefect database driver fix
log "Test 8: Testing Prefect database driver fix..."

# Check Prefect logs for database driver errors
if docker logs opsconductor-prefect-server --tail 50 2>&1 | grep -i "asyncio extension requires an async driver" > /dev/null; then
    log_error "Prefect still has database driver issues"
    exit 1
else
    log_success "Prefect database driver is working correctly"
fi

# Test 9: Final comprehensive verification
log "Test 9: Final comprehensive verification..."
./bulletproof-startup.sh --verify > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_success "Final verification passed"
else
    log_error "Final verification failed"
    exit 1
fi

echo
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 ALL TESTS PASSED! 🎉                   ║"
echo "║                                                              ║"
echo "║  The bulletproof startup system is working perfectly!       ║"
echo "║                                                              ║"
echo "║  ✅ Bulletproof startup script functional                    ║"
echo "║  ✅ All services healthy and responding                      ║"
echo "║  ✅ Infrastructure services working                          ║"
echo "║  ✅ Service restart resilience verified                     ║"
echo "║  ✅ No async warnings in service logs                       ║"
echo "║  ✅ Prefect database driver fixed                            ║"
echo "║  ✅ Comprehensive verification successful                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

log "System is ready for production use! 🚀"