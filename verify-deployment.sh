#!/bin/bash

# OpsConductor NG Deployment Verification Script
# This script verifies that all components are properly deployed and working

set -e

echo "=========================================="
echo "OpsConductor NG Deployment Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print info
info() {
    echo -e "ℹ️  $1"
}

echo "1. Checking Prerequisites..."
echo "----------------------------"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    success "Docker installed: $DOCKER_VERSION"
else
    error "Docker not found"
    exit 1
fi

# Check Docker Compose
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    success "Docker Compose installed: $COMPOSE_VERSION"
else
    error "Docker Compose not found"
    exit 1
fi

# Check NVIDIA Driver
if command -v nvidia-smi &> /dev/null; then
    success "NVIDIA Driver installed"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | while read line; do
        info "GPU: $line"
    done
else
    error "NVIDIA Driver not found"
    exit 1
fi

echo ""
echo "2. Checking Container Status..."
echo "--------------------------------"

# Check if containers are running
CONTAINERS=$(docker compose ps --format json 2>/dev/null | jq -r '.Name' 2>/dev/null || docker compose ps --services)

if [ -z "$CONTAINERS" ]; then
    error "No containers found. Run 'docker compose up -d' first."
    exit 1
fi

# Check each container
FAILED=0
while IFS= read -r container; do
    if [ -n "$container" ]; then
        STATUS=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not found")
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no healthcheck")
        
        if [ "$STATUS" = "running" ]; then
            if [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "no healthcheck" ]; then
                success "$container: $STATUS ($HEALTH)"
            else
                warning "$container: $STATUS ($HEALTH)"
                FAILED=$((FAILED + 1))
            fi
        else
            error "$container: $STATUS"
            FAILED=$((FAILED + 1))
        fi
    fi
done <<< "$(docker compose ps --format '{{.Name}}')"

if [ $FAILED -gt 0 ]; then
    error "$FAILED container(s) not healthy"
fi

echo ""
echo "3. Testing Service Endpoints..."
echo "--------------------------------"

# Test vLLM health
info "Testing vLLM health endpoint..."
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    success "vLLM health check passed"
else
    error "vLLM health check failed"
    FAILED=$((FAILED + 1))
fi

# Test vLLM models endpoint
info "Testing vLLM models endpoint..."
if curl -f -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    success "vLLM models endpoint accessible"
else
    warning "vLLM models endpoint not accessible (may still be loading)"
fi

# Test AI Pipeline health
info "Testing AI Pipeline health endpoint..."
if curl -f -s http://localhost:3005/health > /dev/null 2>&1; then
    success "AI Pipeline health check passed"
else
    error "AI Pipeline health check failed"
    FAILED=$((FAILED + 1))
fi

# Test Frontend
info "Testing Frontend..."
if curl -f -s http://localhost:3100 > /dev/null 2>&1; then
    success "Frontend accessible"
else
    error "Frontend not accessible"
    FAILED=$((FAILED + 1))
fi

# Test Kong Admin
info "Testing Kong Admin API..."
if curl -f -s http://localhost:8888 > /dev/null 2>&1; then
    success "Kong Admin API accessible"
else
    warning "Kong Admin API not accessible"
fi

echo ""
echo "4. Testing vLLM Inference..."
echo "----------------------------"

info "Sending test completion request to vLLM..."
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
    "prompt": "Hello",
    "max_tokens": 10
  }' 2>&1)

if echo "$RESPONSE" | grep -q "choices"; then
    success "vLLM inference test passed"
    info "Response preview: $(echo $RESPONSE | jq -r '.choices[0].text' 2>/dev/null | head -c 50)..."
else
    error "vLLM inference test failed"
    info "Response: $RESPONSE"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "5. Checking GPU Utilization..."
echo "-------------------------------"

if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader | while read line; do
        info "GPU: $line"
    done
    success "GPU information retrieved"
else
    warning "nvidia-smi not available"
fi

echo ""
echo "6. Checking Disk Space..."
echo "--------------------------"

DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    success "Disk usage: ${DISK_USAGE}%"
else
    warning "Disk usage high: ${DISK_USAGE}%"
fi

echo ""
echo "7. Checking Docker Volumes..."
echo "------------------------------"

VOLUMES=$(docker volume ls --filter name=opsconductor --format '{{.Name}}')
if [ -n "$VOLUMES" ]; then
    while IFS= read -r volume; do
        success "Volume exists: $volume"
    done <<< "$VOLUMES"
else
    warning "No OpsConductor volumes found"
fi

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}"
    echo "✅ ALL CHECKS PASSED!"
    echo ""
    echo "Your OpsConductor NG deployment is fully operational."
    echo ""
    echo "Access Points:"
    echo "  - Frontend:    http://localhost:3100"
    echo "  - AI Pipeline: http://localhost:3005"
    echo "  - vLLM API:    http://localhost:8000"
    echo "  - Kong Admin:  http://localhost:8888"
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}"
    echo "❌ VERIFICATION FAILED"
    echo ""
    echo "$FAILED check(s) failed. Please review the output above."
    echo ""
    echo "Common fixes:"
    echo "  - Wait a few minutes for services to fully start"
    echo "  - Check logs: docker compose logs -f"
    echo "  - Restart services: docker compose restart"
    echo "  - Rebuild: docker compose up -d --build"
    echo -e "${NC}"
    exit 1
fi