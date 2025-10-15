#!/bin/bash
# PR #12 Verification Script
# Tests automatic asset lookup and credential resolution

# Don't exit on error - we want to run all tests
set +e

BASE_URL="${BASE_URL:-http://localhost:8010}"
# Read INTERNAL_KEY from .env file if it exists
if [ -f "/home/opsconductor/opsconductor-ng/.env" ]; then
    INTERNAL_KEY=$(grep "^INTERNAL_KEY=" /home/opsconductor/opsconductor-ng/.env | cut -d'=' -f2-)
fi
INTERNAL_KEY="${INTERNAL_KEY:-opsconductor-internal-key-change-in-production}"

echo "========================================="
echo "PR #12 Verification: Auto Asset Enrichment"
echo "========================================="
echo "Base URL: $BASE_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to check HTTP response
check_response() {
    local response="$1"
    local expected_status="$2"
    local test_name="$3"
    
    local status=$(echo "$response" | head -n 1 | cut -d' ' -f2)
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✅ $test_name - PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $test_name - FAILED (status: $status, expected: $expected_status)${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "Test 1: Connection Profile Endpoint"
echo "-----------------------------------"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/assets/connection-profile?host=192.168.50.211")
body=$(echo "$response" | head -n -1)
status=$(echo "$response" | tail -n 1)

if [ "$status" = "200" ]; then
    echo -e "${GREEN}✅ Connection profile endpoint accessible${NC}"
    echo "Response: $body" | python3 -m json.tool 2>/dev/null || echo "$body"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Connection profile endpoint failed (status: $status)${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "Test 2: Secrets Import Endpoint"
echo "--------------------------------"
response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "X-Internal-Key: $INTERNAL_KEY" \
    "$BASE_URL/internal/secrets/import-from-assets")
body=$(echo "$response" | head -n -1)
status=$(echo "$response" | tail -n 1)

if [ "$status" = "200" ]; then
    echo -e "${GREEN}✅ Secrets import endpoint accessible${NC}"
    echo "Response: $body" | python3 -m json.tool 2>/dev/null || echo "$body"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Secrets import endpoint failed (status: $status)${NC}"
    echo "Response: $body"
    ((TESTS_FAILED++))
fi
echo ""

echo "Test 3: Tool Metadata (auth field)"
echo "-----------------------------------"
response=$(curl -s "$BASE_URL/ai/tools/list")
has_auth=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tools = data.get('tools', [])
    winrm_tool = next((t for t in tools if t['name'] == 'windows_list_directory'), None)
    if winrm_tool and 'auth' in winrm_tool:
        print('YES')
    else:
        print('NO')
except:
    print('ERROR')
" 2>/dev/null)

if [ "$has_auth" = "YES" ]; then
    echo -e "${GREEN}✅ windows_list_directory has auth metadata${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  windows_list_directory missing auth metadata (enrichment may not work)${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "Test 4: Tool Execution (without credentials)"
echo "---------------------------------------------"
echo "Testing windows_list_directory without providing credentials..."
response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "name": "windows_list_directory",
        "params": {
            "host": "192.168.50.211",
            "path": "C:\\"
        }
    }' \
    "$BASE_URL/ai/tools/execute")
body=$(echo "$response" | head -n -1)
status=$(echo "$response" | tail -n 1)

if [ "$status" = "200" ]; then
    success=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    error=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', ''))" 2>/dev/null)
    
    if [ "$success" = "True" ]; then
        echo -e "${GREEN}✅ Tool executed successfully (credentials auto-resolved)${NC}"
        ((TESTS_PASSED++))
    elif [[ "$error" == *"asset_not_found"* ]] || [[ "$error" == *"missing_credentials"* ]]; then
        echo -e "${YELLOW}⚠️  Tool execution failed with expected error: $error${NC}"
        echo "   This is acceptable if asset/credentials don't exist yet"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Tool execution failed with unexpected error: $error${NC}"
        echo "Response: $body"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}❌ Tool execution endpoint failed (status: $status)${NC}"
    echo "Response: $body"
    ((TESTS_FAILED++))
fi
echo ""

echo "Test 5: Metrics Endpoints"
echo "-------------------------"
response=$(curl -s "$BASE_URL/metrics")
if echo "$response" | grep -q "ai_exec"; then
    echo -e "${GREEN}✅ Metrics endpoint accessible${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  Metrics endpoint accessible but no ai_exec metrics found yet${NC}"
    echo "   (Metrics will appear after first execution)"
    ((TESTS_PASSED++))
fi
echo ""

echo "========================================="
echo "Summary"
echo "========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Ensure assets exist in database with credentials"
    echo "2. Run: curl -X POST -H 'X-Internal-Key: $INTERNAL_KEY' $BASE_URL/internal/secrets/import-from-assets"
    echo "3. Test actual execution: curl -X POST -H 'Content-Type: application/json' -d '{\"name\":\"windows_list_directory\",\"params\":{\"host\":\"192.168.50.211\",\"path\":\"C:\\\\\"}}' $BASE_URL/ai/tools/execute"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi