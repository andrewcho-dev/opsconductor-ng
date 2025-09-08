#!/bin/bash

# System Status Check Script
# Verifies all services are running correctly

echo "🔍 OpsConductor System Status Check"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

check_service() {
    local service_name=$1
    local url=$2
    local response=$(curl -k -s -w "%{http_code}" -o /dev/null "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ $service_name${NC} - Running"
    else
        echo -e "${RED}✗ $service_name${NC} - Not responding (HTTP: $response)"
    fi
}

check_auth() {
    local response=$(curl -s -X POST "http://localhost:3001/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}' 2>/dev/null)
    
    if echo "$response" | jq -e '.access_token' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Authentication${NC} - Working"
    else
        echo -e "${RED}✗ Authentication${NC} - Failed"
    fi
}

echo ""
echo "🏥 Service Health Checks"
echo "------------------------"

# Check main nginx proxy
check_service "Nginx Proxy" "https://localhost"

# Check individual service health endpoints  
check_service "Auth Service" "http://localhost:3001/health"
check_service "User Service" "http://localhost:3002/health" 
check_service "Credentials Service" "http://localhost:3004/health"
check_service "Targets Service" "http://localhost:3005/health"
check_service "Jobs Service" "http://localhost:3006/health"
check_service "Executor Service" "http://localhost:3007/health"

echo ""
echo "🔐 Authentication Test"
echo "----------------------"
check_auth

echo ""
echo "🌐 Frontend Check"
echo "----------------"
frontend_response=$(curl -k -s "https://localhost" 2>/dev/null)
if echo "$frontend_response" | grep -q "html"; then
    echo -e "${GREEN}✓ Frontend${NC} - Serving React app"
else
    echo -e "${RED}✗ Frontend${NC} - Not serving properly"
fi

echo ""
echo "📊 Container Status"
echo "------------------"
cd /home/opsconductor
docker compose -f docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "📋 System Summary"
echo "----------------"
echo -e "${BLUE}System HTTPS URL:${NC} https://localhost"
echo -e "${BLUE}System HTTP URL:${NC} http://localhost (redirects to HTTPS)"
echo -e "${BLUE}Local HTTPS URL:${NC} https://localhost"
echo -e "${BLUE}Admin Login:${NC} admin / admin123"
echo -e "${BLUE}Database:${NC} PostgreSQL on localhost:5432"
echo -e "${BLUE}Technology:${NC} Python FastAPI + React + PostgreSQL"
echo -e "${BLUE}SSL:${NC} Self-signed certificate (development)"

echo ""
if curl -k -s "https://localhost:8443" > /dev/null 2>&1; then
    echo -e "${GREEN}🎉 System Status: OPERATIONAL ✅${NC}"
else
    echo -e "${RED}⚠️  System Status: ISSUES DETECTED ❌${NC}"
fi

echo ""