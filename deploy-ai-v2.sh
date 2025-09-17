#!/bin/bash
#
# OpsConductor AI System V2 Deployment Script
# Deploys the enhanced AI system with all new features
#

set -e

echo "=================================================="
echo "OpsConductor AI System V2 Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the OpsConductor root directory"
    exit 1
fi

echo ""
echo "Step 1: Copying shared modules to services"
echo "-------------------------------------------"

# List of services that need shared modules
SERVICES=("api-gateway" "ai-command" "ai-orchestrator" "nlp-service" "llm-service" "vector-service")

for SERVICE in "${SERVICES[@]}"; do
    if [ -d "$SERVICE" ]; then
        # Create shared directory if it doesn't exist
        mkdir -p "$SERVICE/shared"
        
        # Copy shared modules
        if [ -f "shared/vector_client.py" ]; then
            cp shared/vector_client.py "$SERVICE/shared/" 2>/dev/null || true
            print_status "Copied vector_client.py to $SERVICE"
        fi
        
        if [ -f "shared/learning_engine.py" ]; then
            cp shared/learning_engine.py "$SERVICE/shared/" 2>/dev/null || true
            print_status "Copied learning_engine.py to $SERVICE"
        fi
        
        if [ -f "shared/ai_common.py" ]; then
            cp shared/ai_common.py "$SERVICE/shared/" 2>/dev/null || true
            print_status "Copied ai_common.py to $SERVICE"
        fi
        
        if [ -f "shared/ai_monitoring.py" ]; then
            cp shared/ai_monitoring.py "$SERVICE/shared/" 2>/dev/null || true
            print_status "Copied ai_monitoring.py to $SERVICE"
        fi
    fi
done

# Special case for API Gateway - copy AI Router
if [ -f "api-gateway/ai_router.py" ]; then
    print_status "AI Router already in place"
else
    print_warning "AI Router not found in api-gateway"
fi

echo ""
echo "Step 2: Building Docker images"
echo "-------------------------------"

# Build only the updated services
UPDATED_SERVICES=("api-gateway" "ai-command")

for SERVICE in "${UPDATED_SERVICES[@]}"; do
    print_status "Building $SERVICE..."
    docker compose build $SERVICE --no-cache || {
        print_error "Failed to build $SERVICE"
        exit 1
    }
done

echo ""
echo "Step 3: Updating running services"
echo "----------------------------------"

# Stop and recreate only updated services
for SERVICE in "${UPDATED_SERVICES[@]}"; do
    print_status "Recreating $SERVICE..."
    docker compose up -d $SERVICE --force-recreate || {
        print_error "Failed to recreate $SERVICE"
        exit 1
    }
done

echo ""
echo "Step 4: Waiting for services to be ready"
echo "-----------------------------------------"

# Wait for services to be healthy
sleep 5

# Check health of services
print_status "Checking service health..."

# Function to check service health
check_service() {
    local service=$1
    local port=$2
    local max_attempts=10
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            print_status "$service is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_warning "$service health check timed out"
    return 1
}

# Check main services
check_service "API Gateway" 3000
check_service "AI Command" 3005

echo ""
echo "Step 5: Verifying AI System V2"
echo "-------------------------------"

# Test the unified AI endpoint
print_status "Testing unified AI endpoint..."

# Get auth token
TOKEN=$(curl -s -X POST http://localhost:3000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' | \
    grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    print_warning "Could not obtain auth token"
else
    print_status "Authentication successful"
    
    # Test AI chat
    RESPONSE=$(curl -s -X POST http://localhost:3000/api/v1/ai/chat \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"query":"What is the system status?"}' | head -c 100)
    
    if [ ! -z "$RESPONSE" ]; then
        print_status "AI chat endpoint responding"
    else
        print_warning "AI chat endpoint not responding"
    fi
    
    # Test AI health
    HEALTH=$(curl -s http://localhost:3000/api/v1/ai/health \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$HEALTH" | grep -q "status"; then
        print_status "AI health endpoint working"
    else
        print_warning "AI health endpoint not responding"
    fi
fi

echo ""
echo "Step 6: Running AI System Tests (Optional)"
echo "-------------------------------------------"

if [ -f "test_ai_system_v2.py" ]; then
    read -p "Run AI system tests? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Running tests..."
        python3 test_ai_system_v2.py || print_warning "Some tests failed"
    fi
else
    print_warning "Test file not found"
fi

echo ""
echo "=================================================="
echo "AI System V2 Deployment Complete!"
echo "=================================================="
echo ""
echo "Available endpoints:"
echo "  - Unified AI Chat: POST http://localhost:3000/api/v1/ai/chat"
echo "  - AI Health: GET http://localhost:3000/api/v1/ai/health"
echo "  - AI Dashboard: GET http://localhost:3000/api/v1/ai/monitoring/dashboard"
echo "  - Submit Feedback: POST http://localhost:3000/api/v1/ai/feedback"
echo ""
echo "To test the system:"
echo "  python3 test_ai_system_v2.py"
echo ""
echo "To view logs:"
echo "  docker compose logs -f api-gateway"
echo "  docker compose logs -f ai-command"
echo ""
print_status "Deployment successful!"