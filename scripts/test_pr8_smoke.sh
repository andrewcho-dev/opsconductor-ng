#!/bin/bash
# PR #8 Smoke Tests - Tools Proxy & Selector→ToolRegistry Fallback
# Tests all acceptance criteria for PR #8

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:3000}"
TRACE_ID="test-pr8-$(date +%s)"

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
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}[TEST $TOTAL_TESTS]${NC} $1"
}

print_pass() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "${GREEN}✓ PASS${NC} $1\n"
}

print_fail() {
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}✗ FAIL${NC} $1\n"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Test 1: GET /ai/tools/list returns 200 with tool array
test_tools_list() {
    print_test "GET /ai/tools/list returns 200 with tool array"
    
    response=$(curl -s -w "\n%{http_code}" \
        -H "X-Trace-Id: ${TRACE_ID}-list" \
        "${BASE_URL}/ai/tools/list")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        # Check if response contains tools array
        tool_count=$(echo "$body" | jq -r '.total // 0')
        if [ "$tool_count" -gt 0 ]; then
            print_pass "Tools list returned $tool_count tools"
            print_info "Sample tool: $(echo "$body" | jq -r '.tools[0].name // "N/A"')"
        else
            print_fail "Tools list returned 0 tools"
        fi
    else
        print_fail "Expected HTTP 200, got $http_code"
        print_info "Response: $body"
    fi
}

# Test 2: POST /ai/tools/execute with tcp_port_check
test_tools_execute_tcp() {
    print_test "POST /ai/tools/execute with tcp_port_check"
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-Trace-Id: ${TRACE_ID}-tcp" \
        -d '{
            "name": "tcp_port_check",
            "params": {
                "host": "127.0.0.1",
                "port": 80
            }
        }' \
        "${BASE_URL}/ai/tools/execute")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        success=$(echo "$body" | jq -r '.success')
        tool=$(echo "$body" | jq -r '.tool')
        
        if [ "$tool" = "tcp_port_check" ]; then
            print_pass "TCP port check executed successfully (success=$success)"
            print_info "Output: $(echo "$body" | jq -r '.output' | head -c 100)"
        else
            print_fail "Expected tool=tcp_port_check, got $tool"
        fi
    else
        print_fail "Expected HTTP 200, got $http_code"
        print_info "Response: $body"
    fi
}

# Test 3: POST /ai/tools/execute with dns_lookup
test_tools_execute_dns() {
    print_test "POST /ai/tools/execute with dns_lookup"
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-Trace-Id: ${TRACE_ID}-dns" \
        -d '{
            "name": "dns_lookup",
            "params": {
                "domain": "example.com",
                "record_type": "A"
            }
        }' \
        "${BASE_URL}/ai/tools/execute")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        success=$(echo "$body" | jq -r '.success')
        tool=$(echo "$body" | jq -r '.tool')
        
        if [ "$tool" = "dns_lookup" ]; then
            print_pass "DNS lookup executed successfully (success=$success)"
            print_info "Duration: $(echo "$body" | jq -r '.duration_ms')ms"
        else
            print_fail "Expected tool=dns_lookup, got $tool"
        fi
    else
        print_fail "Expected HTTP 200, got $http_code"
        print_info "Response: $body"
    fi
}

# Test 4: POST /ai/tools/execute with http_check
test_tools_execute_http() {
    print_test "POST /ai/tools/execute with http_check"
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-Trace-Id: ${TRACE_ID}-http" \
        -d '{
            "name": "http_check",
            "params": {
                "url": "https://www.google.com",
                "method": "GET"
            }
        }' \
        "${BASE_URL}/ai/tools/execute")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        success=$(echo "$body" | jq -r '.success')
        tool=$(echo "$body" | jq -r '.tool')
        
        if [ "$tool" = "http_check" ]; then
            print_pass "HTTP check executed successfully (success=$success)"
        else
            print_fail "Expected tool=http_check, got $tool"
        fi
    else
        print_fail "Expected HTTP 200, got $http_code"
        print_info "Response: $body"
    fi
}

# Test 5: POST /ai/tools/execute with unknown tool returns error
test_tools_execute_unknown() {
    print_test "POST /ai/tools/execute with unknown tool returns error"
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-Trace-Id: ${TRACE_ID}-unknown" \
        -d '{
            "name": "nonexistent_tool",
            "params": {}
        }' \
        "${BASE_URL}/ai/tools/execute")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        success=$(echo "$body" | jq -r '.success')
        error=$(echo "$body" | jq -r '.error')
        
        if [ "$success" = "false" ] && [ "$error" != "null" ]; then
            print_pass "Unknown tool correctly returned error: $error"
        else
            print_fail "Expected success=false with error message"
        fi
    else
        print_fail "Expected HTTP 200, got $http_code"
    fi
}

# Test 6: GET /ai/tools/list with platform filter
test_tools_list_platform_filter() {
    print_test "GET /ai/tools/list with platform=cross-platform filter"
    
    response=$(curl -s -w "\n%{http_code}" \
        -H "X-Trace-Id: ${TRACE_ID}-filter" \
        "${BASE_URL}/ai/tools/list?platform=cross-platform")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        tool_count=$(echo "$body" | jq -r '.total // 0')
        print_pass "Platform filter returned $tool_count cross-platform tools"
    else
        print_fail "Expected HTTP 200, got $http_code"
    fi
}

# Test 7: GET /ai/tools/list with category filter
test_tools_list_category_filter() {
    print_test "GET /ai/tools/list with category=network filter"
    
    response=$(curl -s -w "\n%{http_code}" \
        -H "X-Trace-Id: ${TRACE_ID}-category" \
        "${BASE_URL}/ai/tools/list?category=network")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        tool_count=$(echo "$body" | jq -r '.total // 0')
        if [ "$tool_count" -gt 0 ]; then
            print_pass "Category filter returned $tool_count network tools"
            print_info "Tools: $(echo "$body" | jq -r '.tools[].name' | tr '\n' ', ')"
        else
            print_fail "Expected at least 1 network tool"
        fi
    else
        print_fail "Expected HTTP 200, got $http_code"
    fi
}

# Test 8: Verify all 6 tools are registered
test_all_tools_registered() {
    print_test "Verify all 6 tools are registered"
    
    response=$(curl -s \
        -H "X-Trace-Id: ${TRACE_ID}-all" \
        "${BASE_URL}/ai/tools/list")
    
    expected_tools=("dns_lookup" "http_check" "tcp_port_check" "traceroute" "shell_ping" "windows_list_directory")
    found_count=0
    
    for tool in "${expected_tools[@]}"; do
        if echo "$response" | jq -e ".tools[] | select(.name == \"$tool\")" > /dev/null 2>&1; then
            found_count=$((found_count + 1))
            print_info "✓ Found: $tool"
        else
            print_info "✗ Missing: $tool"
        fi
    done
    
    if [ "$found_count" -eq 6 ]; then
        print_pass "All 6 tools are registered"
    else
        print_fail "Only $found_count/6 tools found"
    fi
}

# Test 9: Test windows_list_directory tool (may fail if no Windows host)
test_windows_tool() {
    print_test "POST /ai/tools/execute with windows_list_directory"
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-Trace-Id: ${TRACE_ID}-windows" \
        -d '{
            "name": "windows_list_directory",
            "params": {
                "host": "192.168.50.211",
                "path": "C:\\",
                "username": "test",
                "password": "test"
            }
        }' \
        "${BASE_URL}/ai/tools/execute")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        tool=$(echo "$body" | jq -r '.tool')
        error=$(echo "$body" | jq -r '.error')
        
        if [ "$tool" = "windows_list_directory" ]; then
            if [ "$error" = "null" ]; then
                print_pass "Windows tool executed successfully"
            else
                print_pass "Windows tool executed (expected auth/connection error: ${error:0:50}...)"
            fi
        else
            print_fail "Expected tool=windows_list_directory, got $tool"
        fi
    else
        print_fail "Expected HTTP 200, got $http_code"
    fi
}

# Test 10: Verify metrics endpoint exposes ai_tool_* metrics
test_metrics() {
    print_test "Verify /metrics exposes ai_tool_* metrics"
    
    # Try ai-pipeline metrics endpoint
    response=$(curl -s "${BASE_URL}/metrics" 2>/dev/null || echo "")
    
    if [ -z "$response" ]; then
        # Try alternative metrics endpoint
        response=$(curl -s "http://localhost:8000/metrics" 2>/dev/null || echo "")
    fi
    
    if echo "$response" | grep -q "ai_tool"; then
        metric_count=$(echo "$response" | grep -c "ai_tool" || echo "0")
        print_pass "Found $metric_count ai_tool_* metric lines"
        print_info "Sample: $(echo "$response" | grep "ai_tool" | head -n 1)"
    else
        print_fail "No ai_tool_* metrics found"
    fi
}

# Main execution
main() {
    print_header "PR #8 Smoke Tests - Tools Proxy & Fallback"
    
    echo "Configuration:"
    echo "  BASE_URL: $BASE_URL"
    echo "  TRACE_ID: $TRACE_ID"
    echo ""
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is required but not installed${NC}"
        exit 1
    fi
    
    # Run tests
    test_tools_list
    test_tools_list_platform_filter
    test_tools_list_category_filter
    test_all_tools_registered
    test_tools_execute_tcp
    test_tools_execute_dns
    test_tools_execute_http
    test_tools_execute_unknown
    test_windows_tool
    test_metrics
    
    # Summary
    print_header "Test Summary"
    echo "Total Tests:  $TOTAL_TESTS"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests passed!${NC}\n"
        exit 0
    else
        echo -e "\n${RED}✗ Some tests failed${NC}\n"
        exit 1
    fi
}

# Run main
main