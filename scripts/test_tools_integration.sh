#!/bin/bash
# Integration tests for Tool Registry, Runner, and Proxy
# Tests the full stack: Kong → Automation Service → AI Pipeline → Tool Execution

set -e

KONG_URL="${KONG_URL:-http://localhost:3000}"
TRACE_ID="test-$(date +%s)"

echo "============================================================"
echo "TOOL REGISTRY & RUNNER INTEGRATION TESTS"
echo "============================================================"
echo "Kong URL: $KONG_URL"
echo "Trace ID: $TRACE_ID"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run test
run_test() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_success="$5"
    
    echo "----------------------------------------"
    echo "TEST: $test_name"
    echo "----------------------------------------"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "X-Trace-Id: $TRACE_ID" \
            "$KONG_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            -H "X-Trace-Id: $TRACE_ID" \
            -d "$data" \
            "$KONG_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    echo "HTTP Status: $http_code"
    echo "Response: $body" | jq '.' 2>/dev/null || echo "$body"
    
    # Check HTTP status
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        # Check success field if expected
        if [ -n "$expected_success" ]; then
            success=$(echo "$body" | jq -r '.success' 2>/dev/null || echo "null")
            if [ "$success" = "$expected_success" ]; then
                echo -e "${GREEN}✅ PASS${NC}"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                echo -e "${RED}❌ FAIL: Expected success=$expected_success, got $success${NC}"
                TESTS_FAILED=$((TESTS_FAILED + 1))
            fi
        else
            echo -e "${GREEN}✅ PASS${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        fi
    else
        echo -e "${RED}❌ FAIL: HTTP $http_code${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    echo ""
}

# Test 1: List all tools
run_test "List All Tools" \
    "GET" \
    "/ai/tools/list" \
    "" \
    "true"

# Test 2: List tools by platform
run_test "List Tools (platform=cross-platform)" \
    "GET" \
    "/ai/tools/list?platform=cross-platform" \
    "" \
    "true"

# Test 3: List tools by category
run_test "List Tools (category=network)" \
    "GET" \
    "/ai/tools/list?category=network" \
    "" \
    "true"

# Test 4: Execute DNS lookup
run_test "Execute DNS Lookup (example.com)" \
    "POST" \
    "/ai/tools/execute" \
    '{"name":"dns_lookup","params":{"domain":"example.com","record_type":"A"}}' \
    "true"

# Test 5: Execute HTTP check
run_test "Execute HTTP Check (google.com)" \
    "POST" \
    "/ai/tools/execute" \
    '{"name":"http_check","params":{"url":"https://www.google.com","method":"GET","timeout_s":5}}' \
    "true"

# Test 6: Execute TCP port check (Kong)
run_test "Execute TCP Port Check (localhost:3000)" \
    "POST" \
    "/ai/tools/execute" \
    '{"name":"tcp_port_check","params":{"host":"localhost","port":3000,"timeout_s":3}}' \
    "true"

# Test 7: Execute ping
run_test "Execute Ping (8.8.8.8)" \
    "POST" \
    "/ai/tools/execute" \
    '{"name":"shell_ping","params":{"host":"8.8.8.8","count":2,"timeout_s":2}}' \
    "true"

# Test 8: Invalid tool (should fail gracefully)
run_test "Execute Invalid Tool (should fail)" \
    "POST" \
    "/ai/tools/execute" \
    '{"name":"nonexistent_tool","params":{}}' \
    "false"

# Test 9: Missing required parameter (should fail)
run_test "Execute DNS Lookup (missing domain - should fail)" \
    "POST" \
    "/ai/tools/execute" \
    '{"name":"dns_lookup","params":{"record_type":"A"}}' \
    "false"

# Test 10: Invalid parameter value (should fail)
run_test "Execute TCP Port Check (invalid port - should fail)" \
    "POST" \
    "/ai/tools/execute" \
    '{"name":"tcp_port_check","params":{"host":"localhost","port":99999}}' \
    "false"

# Summary
echo "============================================================"
echo "TEST SUMMARY"
echo "============================================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi