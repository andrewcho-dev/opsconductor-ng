#!/bin/bash
# Frontend API Testing Script
# Tests the ACTUAL running system through HTTP API calls
# This matches what the frontend does - no mocks, no local imports

set -e

API_URL="http://localhost:3005"
TIMEOUT=120

echo "=========================================="
echo "🧪 FRONTEND API TESTING"
echo "Testing actual Docker containers via HTTP"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to test a query
test_query() {
    local query="$1"
    local expected_tool_type="$2"  # "asset" or "prometheus"
    local test_name="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo "----------------------------------------"
    echo "Test #$TOTAL_TESTS: $test_name"
    echo "Query: \"$query\""
    echo "Expected: $expected_tool_type tool"
    echo ""
    
    # Make the actual API call
    response=$(curl -s -X POST "$API_URL/pipeline" \
        -H "Content-Type: application/json" \
        -d "{\"user_request\": \"$query\"}" \
        --max-time $TIMEOUT)
    
    # Check if request succeeded
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ FAILED: API request failed${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Extract key information
    stage_a_category=$(echo "$response" | jq -r '.stage_a_result.intent.category // "null"')
    stage_a_action=$(echo "$response" | jq -r '.stage_a_result.intent.action // "null"')
    stage_b_tool=$(echo "$response" | jq -r '.stage_b_result.selected_tools[0].tool_name // "null"')
    error=$(echo "$response" | jq -r '.error // "null"')
    
    echo "Stage A Category: $stage_a_category"
    echo "Stage A Action: $stage_a_action"
    echo "Stage B Tool: $stage_b_tool"
    
    if [ "$error" != "null" ]; then
        echo -e "${RED}❌ FAILED: Pipeline error: $error${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Validate based on expected tool type
    if [ "$expected_tool_type" == "asset" ]; then
        # Should NOT be prometheus
        if echo "$stage_b_tool" | grep -iq "prometheus"; then
            echo -e "${RED}❌ FAILED: Selected prometheus instead of asset tool!${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
        
        # Should be asset-related
        if echo "$stage_b_tool" | grep -iq "asset\|inventory\|cmdb"; then
            echo -e "${GREEN}✅ PASSED: Correctly selected asset tool${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            echo -e "${RED}❌ FAILED: Did not select asset tool (got: $stage_b_tool)${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
        
    elif [ "$expected_tool_type" == "prometheus" ]; then
        # Should be prometheus
        if echo "$stage_b_tool" | grep -iq "prometheus"; then
            echo -e "${GREEN}✅ PASSED: Correctly selected prometheus tool${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            echo -e "${RED}❌ FAILED: Did not select prometheus tool (got: $stage_b_tool)${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    fi
    
    echo -e "${RED}❌ FAILED: Unknown validation result${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    return 1
}

# Check if API is reachable
echo "Checking API health..."
health_check=$(curl -s "$API_URL/health" || echo "FAILED")
if echo "$health_check" | grep -q "healthy"; then
    echo -e "${GREEN}✅ API is healthy${NC}"
    echo ""
else
    echo -e "${RED}❌ API is not reachable at $API_URL${NC}"
    exit 1
fi

# Run tests - Asset queries (should select asset tools)
echo "=========================================="
echo "📦 ASSET QUERY TESTS"
echo "=========================================="
echo ""

test_query "Show me all assets" "asset" "Basic asset listing"
test_query "Show me all Linux servers" "asset" "Filtered asset listing"
test_query "How many assets do we have?" "asset" "Asset count query"
test_query "Find all Windows servers" "asset" "Asset search query"
test_query "List all database servers" "asset" "Asset listing with filter"
test_query "Get asset info for server web-01" "asset" "Specific asset query"
test_query "Search for assets with IP 10.0.1.5" "asset" "Asset search by IP"
test_query "Show me all production assets" "asset" "Asset filter by environment"
test_query "How many Linux servers are there?" "asset" "Asset count with filter"
test_query "What servers do we have?" "asset" "Natural language asset query"

# Run tests - Monitoring queries (should select prometheus)
echo ""
echo "=========================================="
echo "📊 MONITORING QUERY TESTS"
echo "=========================================="
echo ""

test_query "Show me CPU usage" "prometheus" "Basic monitoring query"

# Summary
echo ""
echo "=========================================="
echo "📊 TEST SUMMARY"
echo "=========================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi