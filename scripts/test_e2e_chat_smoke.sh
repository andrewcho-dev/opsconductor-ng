#!/bin/bash

###############################################################################
# End-to-End Chat Smoke Test
# Tests all 5 acceptance criteria for PR #7
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:3000}"
TIMEOUT=5

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST $1:${NC} $2"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1\n"
    ((PASSED_TESTS++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    echo -e "${RED}  Error: $2${NC}\n"
    ((FAILED_TESTS++))
}

test_api() {
    local test_num=$1
    local test_name=$2
    local method=$3
    local endpoint=$4
    local data=$5
    local expected_field=$6
    local expected_value=$7
    
    ((TOTAL_TESTS++))
    print_test "$test_num" "$test_name"
    
    # Make request
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
            -X "$method" \
            -H "Content-Type: application/json" \
            -H "X-Trace-Id: test-$(date +%s)" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi
    
    # Extract HTTP code and body
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    # Check HTTP status
    if [ "$http_code" != "200" ]; then
        print_fail "$test_name" "HTTP $http_code (expected 200)"
        echo "Response: $body"
        return 1
    fi
    
    # Check expected field if provided
    if [ -n "$expected_field" ]; then
        actual_value=$(echo "$body" | jq -r ".$expected_field" 2>/dev/null || echo "")
        
        if [ "$expected_value" = "EXISTS" ]; then
            if [ -n "$actual_value" ] && [ "$actual_value" != "null" ]; then
                print_pass "$test_name (${expected_field} exists)"
                return 0
            else
                print_fail "$test_name" "${expected_field} not found in response"
                echo "Response: $body"
                return 1
            fi
        elif [ "$actual_value" = "$expected_value" ]; then
            print_pass "$test_name (${expected_field}=${expected_value})"
            return 0
        else
            print_fail "$test_name" "${expected_field}=${actual_value} (expected ${expected_value})"
            echo "Response: $body"
            return 1
        fi
    else
        print_pass "$test_name"
        return 0
    fi
}

###############################################################################
# ACCEPTANCE CRITERIA TESTS
###############################################################################

print_header "PR #7 - End-to-End Execution Smoke Tests"

echo "Testing against: $BASE_URL"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Test 1: "ping" → "pong" (<=2s)
print_header "AC1: Echo 'ping' → 'pong' (<=2s)"

test_api "1.1" "Echo execution: ping" \
    "POST" "/ai/execute" \
    '{"tool":"echo","input":"ping"}' \
    "success" "true"

test_api "1.2" "Echo output verification" \
    "POST" "/ai/execute" \
    '{"tool":"echo","input":"ping"}' \
    "output" "pong"

# Test 2: Exact echo
print_header "AC2: Exact Echo 'OpsConductor is live'"

test_api "2.1" "Exact echo execution" \
    "POST" "/ai/execute" \
    '{"tool":"echo","input":"OpsConductor is live"}' \
    "success" "true"

test_api "2.2" "Exact echo output verification" \
    "POST" "/ai/execute" \
    '{"tool":"echo","input":"OpsConductor is live"}' \
    "output" "OpsConductor is live"

# Test 3: Tool selector search
print_header "AC3: Selector Search for DNS Tools"

test_api "3.1" "Selector search execution" \
    "GET" "/api/selector/search?query=DNS+troubleshooting+tools&k=3" \
    "" \
    "tools" "EXISTS"

test_api "3.2" "Selector returns results" \
    "GET" "/api/selector/search?query=network+diagnostics&k=5" \
    "" \
    "count" "EXISTS"

# Test 4: Tool execution - Port check
print_header "AC4: Tool Execution - Port Check"

test_api "4.1" "TCP port check on localhost:3000" \
    "POST" "/ai/tools/execute" \
    '{"name":"tcp_port_check","params":{"host":"127.0.0.1","port":3000}}' \
    "success" "true"

test_api "4.2" "DNS lookup example.com" \
    "POST" "/ai/tools/execute" \
    '{"name":"dns_lookup","params":{"domain":"example.com","record_type":"A"}}' \
    "success" "true"

test_api "4.3" "HTTP check localhost" \
    "POST" "/ai/tools/execute" \
    '{"name":"http_check","params":{"url":"http://localhost:3000","method":"GET"}}' \
    "success" "true"

# Test 5: Windows directory listing (will fail without credentials, but should return structured error)
print_header "AC5: Windows Directory Listing (Error Handling)"

echo -e "${YELLOW}NOTE:${NC} This test expects a structured error response (no credentials provided)"
echo ""

((TOTAL_TESTS++))
print_test "5.1" "Windows list directory (expect auth error)"

response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST \
    -H "Content-Type: application/json" \
    -H "X-Trace-Id: test-$(date +%s)" \
    -d '{"name":"windows_list_directory","params":{"host":"192.168.50.211","path":"C:\\","username":"test","password":"test"}}' \
    "$BASE_URL/ai/tools/execute" 2>/dev/null || echo -e "\n500")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

# For Windows tool, we expect either success OR a structured error
if [ "$http_code" = "200" ]; then
    has_tool=$(echo "$body" | jq -r '.tool' 2>/dev/null || echo "")
    has_output=$(echo "$body" | jq -r '.output' 2>/dev/null || echo "")
    
    if [ "$has_tool" = "windows_list_directory" ] && [ -n "$has_output" ]; then
        print_pass "Windows tool returns structured response"
        ((PASSED_TESTS++))
    else
        print_fail "Windows tool" "Response missing required fields"
        echo "Response: $body"
        ((FAILED_TESTS++))
    fi
else
    print_fail "Windows tool" "HTTP $http_code (expected 200 with error details)"
    echo "Response: $body"
    ((FAILED_TESTS++))
fi

###############################################################################
# METRICS CHECK
###############################################################################

print_header "Metrics Verification"

((TOTAL_TESTS++))
print_test "6.1" "Prometheus metrics endpoint"

metrics_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BASE_URL/metrics" 2>/dev/null || echo -e "\n500")
metrics_code=$(echo "$metrics_response" | tail -n1)
metrics_body=$(echo "$metrics_response" | sed '$d')

if [ "$metrics_code" = "200" ]; then
    # Check for tool metrics
    if echo "$metrics_body" | grep -q "ai_tool_requests_total"; then
        print_pass "Metrics endpoint exposes ai_tool_requests_total"
        ((PASSED_TESTS++))
    else
        print_fail "Metrics" "ai_tool_requests_total not found"
        ((FAILED_TESTS++))
    fi
else
    print_fail "Metrics endpoint" "HTTP $metrics_code (expected 200)"
    ((FAILED_TESTS++))
fi

###############################################################################
# TOOL REGISTRY CHECK
###############################################################################

print_header "Tool Registry Verification"

test_api "7.1" "List all tools" \
    "GET" "/ai/tools/list" \
    "" \
    "tools" "EXISTS"

((TOTAL_TESTS++))
print_test "7.2" "Verify 6 tools registered (5 network + 1 Windows)"

tools_response=$(curl -s --max-time $TIMEOUT "$BASE_URL/ai/tools/list")
tool_count=$(echo "$tools_response" | jq -r '.tools | length' 2>/dev/null || echo "0")

if [ "$tool_count" -ge "6" ]; then
    print_pass "Tool registry has $tool_count tools (expected ≥6)"
    ((PASSED_TESTS++))
else
    print_fail "Tool count" "Found $tool_count tools (expected ≥6)"
    ((FAILED_TESTS++))
fi

###############################################################################
# SUMMARY
###############################################################################

print_header "Test Summary"

echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ALL TESTS PASSED! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  SOME TESTS FAILED ✗${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi