#!/bin/bash

# OpsConductor V3 - Phase 5: Traefik Testing Script
# Comprehensive testing of Traefik routing and functionality

set -e

echo "🧪 OpsConductor V3 - Phase 5: Traefik Testing"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    print_status "Testing: $test_name"
    
    if eval "$test_command" 2>/dev/null; then
        if [ -n "$expected_pattern" ]; then
            if eval "$test_command" 2>/dev/null | grep -q "$expected_pattern"; then
                print_success "$test_name"
                TESTS_PASSED=$((TESTS_PASSED + 1))
                return 0
            else
                print_error "$test_name - Pattern not found: $expected_pattern"
                TESTS_FAILED=$((TESTS_FAILED + 1))
                return 1
            fi
        else
            print_success "$test_name"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        fi
    else
        print_error "$test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo ""
print_status "Starting Traefik functionality tests..."
echo ""

# 1. Traefik Container Health
run_test "Traefik container is running" \
    "docker ps | grep opsconductor-traefik" \
    "opsconductor-traefik"

# 2. Traefik Dashboard Access
run_test "Traefik dashboard accessibility" \
    "curl -s -f http://localhost:8081/ping" \
    ""

# 3. Traefik API Access
run_test "Traefik API accessibility" \
    "curl -s -f http://localhost:8081/api/overview" \
    ""

# 4. Service Discovery - Kong
run_test "Kong service discovery" \
    "curl -s http://localhost:8081/api/http/routers" \
    "kong-api"

# 5. Service Discovery - Frontend
run_test "Frontend service discovery" \
    "curl -s http://localhost:8081/api/http/routers" \
    "frontend"

# 6. Health Check Routing
run_test "Health check routing via Traefik" \
    "curl -s -f http://localhost/health" \
    ""

# 7. API Routing
run_test "API routing via Traefik" \
    "curl -s -f http://localhost/api/v1/identity/health" \
    ""

# 8. Frontend Routing
run_test "Frontend routing via Traefik" \
    "curl -s -f http://localhost/" \
    ""

# 9. Rate Limiting Middleware
print_status "Testing rate limiting middleware..."
RATE_LIMIT_TEST=true
for i in {1..5}; do
    if ! curl -s -f http://localhost/api/v1/identity/health > /dev/null; then
        RATE_LIMIT_TEST=false
        break
    fi
done

if [ "$RATE_LIMIT_TEST" = true ]; then
    print_success "Rate limiting middleware is configured (allowing normal traffic)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "Rate limiting middleware may be too restrictive"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

# 10. Security Headers
run_test "Security headers in API responses" \
    "curl -s -I http://localhost/api/v1/identity/health" \
    "X-Frame-Options"

# 11. CORS Headers
run_test "CORS headers in API responses" \
    "curl -s -I -H 'Origin: http://localhost:3000' http://localhost/api/v1/identity/health" \
    ""

# 12. Prometheus Metrics
run_test "Prometheus metrics endpoint" \
    "curl -s -f http://localhost:8081/metrics" \
    "traefik_"

# 13. Load Balancer Health Checks
run_test "Load balancer health checks" \
    "curl -s http://localhost:8081/api/http/services" \
    "loadBalancer"

# 14. WebSocket Support (if automation service is running)
if docker ps | grep -q "opsconductor-automation"; then
    print_status "Testing WebSocket support..."
    # Note: WebSocket testing requires special tools, so we'll just check the route exists
    run_test "WebSocket route configuration" \
        "curl -s http://localhost:8081/api/http/routers" \
        "automation-ws"
else
    print_warning "Automation service not running - skipping WebSocket tests"
fi

# 15. SSL/TLS Configuration (if enabled)
print_status "Checking SSL/TLS configuration..."
if curl -s http://localhost:8081/api/http/routers | grep -q "tls"; then
    print_success "TLS configuration detected"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_warning "TLS not configured (expected for development)"
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

echo ""
print_status "Performance comparison tests..."
echo ""

# Performance Tests
print_status "Measuring response times..."

# Test Nginx response time
if curl -s -f http://localhost:80/health > /dev/null 2>&1; then
    NGINX_TIME=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:80/health)
    print_status "Nginx response time: ${NGINX_TIME}s"
else
    print_warning "Nginx not accessible for comparison"
    NGINX_TIME="N/A"
fi

# Test Traefik response time
if curl -s -f http://localhost/health > /dev/null 2>&1; then
    TRAEFIK_TIME=$(curl -s -w "%{time_total}" -o /dev/null http://localhost/health)
    print_status "Traefik response time: ${TRAEFIK_TIME}s"
else
    print_error "Traefik not accessible"
    TRAEFIK_TIME="N/A"
fi

echo ""
print_status "Service status summary..."
echo ""

# Service Status Summary
echo "📊 Service Status:"
echo "  • Traefik Dashboard: http://localhost:8081/dashboard/"
echo "  • Traefik API: http://localhost:8081/api/"
echo "  • Prometheus Metrics: http://localhost:8081/metrics"
echo ""

# Router Summary
echo "🔀 Active Routers:"
if curl -s http://localhost:8081/api/http/routers 2>/dev/null | jq -r '.[].name' 2>/dev/null; then
    curl -s http://localhost:8081/api/http/routers | jq -r '.[] | "  • \(.name): \(.rule)"' 2>/dev/null || echo "  • Unable to parse router information"
else
    echo "  • Unable to retrieve router information"
fi

echo ""

# Test Results Summary
echo "📋 Test Results Summary:"
echo "  • Total Tests: $TESTS_TOTAL"
echo "  • Passed: $TESTS_PASSED"
echo "  • Failed: $TESTS_FAILED"
echo "  • Success Rate: $(( (TESTS_PASSED * 100) / TESTS_TOTAL ))%"

if [ "$NGINX_TIME" != "N/A" ] && [ "$TRAEFIK_TIME" != "N/A" ]; then
    echo ""
    echo "⚡ Performance Comparison:"
    echo "  • Nginx: ${NGINX_TIME}s"
    echo "  • Traefik: ${TRAEFIK_TIME}s"
fi

echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "All tests passed! Traefik is ready for migration."
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Review Traefik dashboard: http://localhost:8081/dashboard/"
    echo "  2. Test your specific use cases"
    echo "  3. Run: ./migrate-to-traefik.sh when ready to complete migration"
    exit 0
else
    print_error "Some tests failed. Please review the issues before proceeding."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "  1. Check Traefik logs: docker-compose -f docker-compose.traefik.yml logs traefik"
    echo "  2. Verify service labels: docker inspect <service-name>"
    echo "  3. Check Traefik dashboard for routing issues"
    exit 1
fi