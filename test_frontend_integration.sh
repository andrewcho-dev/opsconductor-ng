#!/bin/bash
# Frontend Integration Test Script
# Tests the Selector v3 frontend ↔ backend integration

set -e

echo "🧪 Frontend Integration Test Suite"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="$3"
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "\n%{http_code}" "$url")
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_status, got $status_code)"
        echo "Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test 1: Frontend is accessible
echo "1. Frontend Accessibility"
echo "-------------------------"
test_endpoint "Frontend root" "http://127.0.0.1:3100" "200"
echo ""

# Test 2: Backend health
echo "2. Backend Health"
echo "-----------------"
test_endpoint "Automation service health" "http://127.0.0.1:8010/health" "200"
echo ""

# Test 3: Selector endpoint responds
echo "3. Selector API"
echo "---------------"
echo -n "Testing selector search endpoint... "
response=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:8010/api/selector/search?query=test&k=3")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

# Accept both 200 (success) and 503 (degraded mode) as valid
if [ "$status_code" = "200" ] || [ "$status_code" = "503" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
    PASSED=$((PASSED + 1))
    
    # Check response structure
    if echo "$body" | jq -e '.query' > /dev/null 2>&1; then
        echo "  ✓ Response has 'query' field"
    elif echo "$body" | jq -e '.error' > /dev/null 2>&1; then
        echo "  ✓ Response has 'error' field (degraded mode)"
        retry_after=$(echo "$body" | jq -r '.retry_after_sec // "N/A"')
        echo "  ℹ Retry after: $retry_after seconds"
    fi
else
    echo -e "${RED}✗ FAIL${NC} (Expected HTTP 200 or 503, got $status_code)"
    echo "Response: $body"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: Selector validation
echo "4. Selector Validation"
echo "----------------------"
echo -n "Testing empty query validation... "
response=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:8010/api/selector/search?query=&k=3")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$status_code" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
    PASSED=$((PASSED + 1))
    if command -v jq &> /dev/null; then
        error_code=$(echo "$body" | jq -r '.code // "N/A"')
        echo "  ✓ Error code: $error_code"
    fi
else
    echo -e "${RED}✗ FAIL${NC} (Expected HTTP 400, got $status_code)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 5: Audit endpoint (if enabled)
echo "5. Audit API (Optional)"
echo "-----------------------"
echo -n "Testing audit health endpoint... "
response=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:8010/audit/health")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
    PASSED=$((PASSED + 1))
    if command -v jq &> /dev/null; then
        queue_size=$(echo "$body" | jq -r '.queue_size // "N/A"')
        worker_running=$(echo "$body" | jq -r '.worker_running // "N/A"')
        echo "  ✓ Queue size: $queue_size"
        echo "  ✓ Worker running: $worker_running"
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC} (Audit endpoint not available or not configured)"
fi
echo ""

# Test 6: CORS headers
echo "6. CORS Configuration"
echo "---------------------"
echo -n "Testing CORS headers... "
response=$(curl -s -I -H "Origin: http://127.0.0.1:3100" "http://127.0.0.1:8010/api/selector/search?query=test&k=3")

if echo "$response" | grep -qi "access-control-allow-origin"; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
    cors_origin=$(echo "$response" | grep -i "access-control-allow-origin" | cut -d' ' -f2 | tr -d '\r')
    echo "  ✓ CORS origin: $cors_origin"
else
    echo -e "${RED}✗ FAIL${NC} (No CORS headers found)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo "=================================="
echo "Test Summary"
echo "=================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Frontend Integration Status: ✅ READY"
    echo ""
    echo "Next Steps:"
    echo "1. Navigate to http://127.0.0.1:3100/selector"
    echo "2. Log in with Keycloak credentials"
    echo "3. Test the Tool Selector UI"
    echo "4. Try searching for tools (may return 503 if DB not populated)"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Please review the failures above and fix any issues."
    exit 1
fi