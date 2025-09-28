#!/bin/bash

# OpsConductor Remote Probe Readiness Check
# This script verifies that the central system is ready to accept remote probes

set -e

echo "🔍 OpsConductor Remote Probe Readiness Check"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
TOTAL_CHECKS=0

check_status() {
    local check_name="$1"
    local status="$2"
    local details="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "✅ ${GREEN}PASS${NC} - $check_name"
        [ -n "$details" ] && echo -e "   ${BLUE}ℹ️  $details${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif [ "$status" = "WARN" ]; then
        echo -e "⚠️  ${YELLOW}WARN${NC} - $check_name"
        [ -n "$details" ] && echo -e "   ${YELLOW}⚠️  $details${NC}"
    else
        echo -e "❌ ${RED}FAIL${NC} - $check_name"
        [ -n "$details" ] && echo -e "   ${RED}❌ $details${NC}"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
    echo ""
}

# Database connection parameters - use Docker service name for internal communication
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-opsconductor}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres123}

# 1. Check Docker Compose Configuration
echo "🐳 Checking Docker Compose Configuration..."
if [ -f "docker-compose.yml" ]; then
    # Check if network-analyzer-service port is exposed
    if grep -q "3006:3006" docker-compose.yml; then
        check_status "Network Analyzer Port Exposure" "PASS" "Port 3006 is exposed for remote probe connections"
    else
        check_status "Network Analyzer Port Exposure" "FAIL" "Port 3006 is not exposed in docker-compose.yml"
    fi
    
    # Check if network-analyzer-service exists
    if grep -q "network-analyzer-service:" docker-compose.yml; then
        check_status "Network Analyzer Service Definition" "PASS" "Service is defined in docker-compose.yml"
    else
        check_status "Network Analyzer Service Definition" "FAIL" "network-analyzer-service not found in docker-compose.yml"
    fi
else
    check_status "Docker Compose File" "FAIL" "docker-compose.yml not found"
fi

# 2. Check Database Connection
echo "📊 Checking Database Connection..."
# Check if Docker containers are running first
if docker compose ps postgres | grep -q "Up"; then
    # Use Docker container's psql to test database connection
    if docker compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
        check_status "Database Connection" "PASS" "Successfully connected to PostgreSQL database"
        
        # Check if network_analysis schema exists
        SCHEMA_EXISTS=$(docker compose exec -T postgres psql -U $DB_USER -d $DB_NAME -t -c "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'network_analysis');" | tr -d ' ')
        if [ "$SCHEMA_EXISTS" = "t" ]; then
            check_status "Network Analysis Schema" "PASS" "network_analysis schema exists"
            
            # Check if remote_probes table exists
            TABLE_EXISTS=$(docker compose exec -T postgres psql -U $DB_USER -d $DB_NAME -t -c "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'network_analysis' AND table_name = 'remote_probes');" | tr -d ' ')
            if [ "$TABLE_EXISTS" = "t" ]; then
                check_status "Remote Probes Table" "PASS" "remote_probes table exists"
            else
                check_status "Remote Probes Table" "FAIL" "remote_probes table missing - run migration script"
            fi
        else
            check_status "Network Analysis Schema" "FAIL" "network_analysis schema missing - run migration script"
        fi
    else
        check_status "Database Connection" "FAIL" "Cannot connect to database in container"
    fi
else
    check_status "Database Connection" "WARN" "PostgreSQL container not running - start with 'docker compose up -d'"
fi

# 3. Check Network Analyzer Service Files
echo "🔧 Checking Network Analyzer Service Files..."
if [ -d "network-analyzer-service" ]; then
    check_status "Network Analyzer Directory" "PASS" "Service directory exists"
    
    if [ -f "network-analyzer-service/main.py" ]; then
        check_status "Main Service File" "PASS" "main.py exists"
        
        # Check for remote probe endpoints
        if grep -q "/api/v1/remote/register-probe" network-analyzer-service/main.py; then
            check_status "Remote Probe Endpoints" "PASS" "Remote probe registration endpoints found"
        else
            check_status "Remote Probe Endpoints" "FAIL" "Remote probe endpoints missing from main.py"
        fi
    else
        check_status "Main Service File" "FAIL" "main.py not found"
    fi
    
    if [ -f "network-analyzer-service/Dockerfile" ]; then
        check_status "Service Dockerfile" "PASS" "Dockerfile exists"
    else
        check_status "Service Dockerfile" "FAIL" "Dockerfile missing"
    fi
else
    check_status "Network Analyzer Directory" "FAIL" "network-analyzer-service directory not found"
fi

# 4. Check Remote Probe Deployment Package
echo "📦 Checking Remote Probe Deployment Package..."
if [ -d "remote-probe-deployment" ]; then
    check_status "Probe Deployment Directory" "PASS" "remote-probe-deployment directory exists"
    
    if [ -f "remote-probe-deployment/probe-standalone.py" ]; then
        check_status "Standalone Probe Application" "PASS" "probe-standalone.py exists"
    else
        check_status "Standalone Probe Application" "FAIL" "probe-standalone.py missing"
    fi
    
    if [ -f "remote-probe-deployment/build/build-linux.sh" ]; then
        check_status "Linux Build Script" "PASS" "build-linux.sh exists"
    else
        check_status "Linux Build Script" "FAIL" "build-linux.sh missing"
    fi
    
    if [ -f "remote-probe-deployment/config-template.yaml" ]; then
        check_status "Configuration Template" "PASS" "config-template.yaml exists"
    else
        check_status "Configuration Template" "FAIL" "config-template.yaml missing"
    fi
else
    check_status "Probe Deployment Directory" "FAIL" "remote-probe-deployment directory not found"
fi

# 5. Check Network Connectivity
echo "🌐 Checking Network Connectivity..."
# Check if services are running, start them if not
if ! docker compose ps | grep -q "Up"; then
    echo "   🚀 Starting OpsConductor services..."
    if docker compose up -d > /dev/null 2>&1; then
        echo "   ✅ Services started successfully"
        # Wait a moment for services to initialize
        sleep 5
    else
        check_status "Service Startup" "FAIL" "Failed to start Docker services"
    fi
fi

if command -v curl >/dev/null 2>&1; then
    # Get dynamic host IP for external service testing
    HOST_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$HOST_IP" ]; then
        HOST_IP="127.0.0.1"
    fi
    
    # Try to connect to the network analyzer service using host IP
    if curl -s -f http://${HOST_IP}:3006/health > /dev/null 2>&1; then
        check_status "Network Analyzer Service Health" "PASS" "Service is running and responding on port 3006 at ${HOST_IP}"
    else
        # Give it another try after a short wait
        sleep 3
        if curl -s -f http://${HOST_IP}:3006/health > /dev/null 2>&1; then
            check_status "Network Analyzer Service Health" "PASS" "Service is running and responding on port 3006 at ${HOST_IP}"
        else
            check_status "Network Analyzer Service Health" "WARN" "Service not responding at ${HOST_IP}:3006 - check service logs"
        fi
    fi
else
    check_status "Network Connectivity Tools" "WARN" "curl not available - cannot test service connectivity"
fi

# 6. Check Required Dependencies
echo "🔨 Checking Required Dependencies..."
if command -v docker >/dev/null 2>&1; then
    check_status "Docker" "PASS" "Docker is installed"
else
    check_status "Docker" "FAIL" "Docker is not installed"
fi

if command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
    check_status "Docker Compose" "PASS" "Docker Compose is available"
else
    check_status "Docker Compose" "FAIL" "Docker Compose is not available"
fi

if command -v python3 >/dev/null 2>&1; then
    check_status "Python 3" "PASS" "Python 3 is installed"
else
    check_status "Python 3" "WARN" "Python 3 not found (needed for building probe packages)"
fi

# Summary
echo "📋 Summary"
echo "=========="
echo -e "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "🎉 ${GREEN}All critical checks passed! Your OpsConductor system is ready to accept remote probes.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start your OpsConductor services: docker-compose up -d"
    echo "2. Build remote probe packages: cd remote-probe-deployment/build && ./build-linux.sh"
    echo "3. Deploy probes to remote systems using the generated packages"
    echo ""
    exit 0
else
    echo -e "⚠️  ${YELLOW}Some checks failed. Please address the issues above before deploying remote probes.${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Run database migration: ./scripts/migrate-network-analysis.sh"
    echo "2. Ensure Docker services are properly configured"
    echo "3. Verify all required files are present"
    echo ""
    exit 1
fi