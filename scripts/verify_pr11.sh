#!/bin/bash
# Verification script for PR #11: Asset-Intelligent Execution

set -e

echo "=========================================="
echo "PR #11 Verification Script"
echo "=========================================="
echo ""

# Configuration
AUTOMATION_SERVICE_URL="${AUTOMATION_SERVICE_URL:-http://localhost:3003}"
KONG_URL="${KONG_URL:-http://localhost:3000}"

echo "Configuration:"
echo "  Automation Service: $AUTOMATION_SERVICE_URL"
echo "  Kong Gateway: $KONG_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="$3"
    local method="${4:-GET}"
    local data="${5:-}"
    
    echo -n "Testing: $name ... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    fi
    
    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status)"
        PASSED=$((PASSED + 1))
        if [ -n "$body" ] && [ "$body" != "000" ]; then
            echo "  Response: ${body:0:100}..."
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $status)"
        FAILED=$((FAILED + 1))
        if [ -n "$body" ]; then
            echo "  Response: ${body:0:200}"
        fi
    fi
}

echo "=========================================="
echo "1. Asset Façade Tests (Direct)"
echo "=========================================="
echo ""

test_endpoint \
    "Asset count (all)" \
    "$AUTOMATION_SERVICE_URL/assets/count" \
    "200"

test_endpoint \
    "Asset count (Windows 10)" \
    "$AUTOMATION_SERVICE_URL/assets/count?os=Windows%2010" \
    "200"

test_endpoint \
    "Asset search (Windows)" \
    "$AUTOMATION_SERVICE_URL/assets/search?os=windows&limit=5" \
    "200"

test_endpoint \
    "Connection profile (not found)" \
    "$AUTOMATION_SERVICE_URL/assets/connection-profile?host=nonexistent.example.com" \
    "200"

echo ""
echo "=========================================="
echo "2. Asset Façade Tests (via Kong)"
echo "=========================================="
echo ""

test_endpoint \
    "Asset count via Kong" \
    "$KONG_URL/assets/count?os=Windows%2010" \
    "200"

test_endpoint \
    "Asset search via Kong" \
    "$KONG_URL/assets/search?os=windows&limit=5" \
    "200"

echo ""
echo "=========================================="
echo "3. Secrets Broker Tests (Security)"
echo "=========================================="
echo ""

test_endpoint \
    "Secrets API blocked without key (direct)" \
    "$AUTOMATION_SERVICE_URL/internal/secrets/credential-lookup" \
    "403" \
    "POST" \
    '{"host":"test","purpose":"winrm"}'

test_endpoint \
    "Secrets API NOT exposed via Kong" \
    "$KONG_URL/internal/secrets/credential-lookup" \
    "404" \
    "POST" \
    '{"host":"test","purpose":"winrm"}'

echo ""
echo "=========================================="
echo "4. Asset Tools Tests"
echo "=========================================="
echo ""

test_endpoint \
    "asset_count tool" \
    "$AUTOMATION_SERVICE_URL/ai/tools/execute" \
    "200" \
    "POST" \
    '{"name":"asset_count","params":{"os":"Windows 10"}}'

test_endpoint \
    "asset_search tool" \
    "$AUTOMATION_SERVICE_URL/ai/tools/execute" \
    "200" \
    "POST" \
    '{"name":"asset_search","params":{"os":"windows","limit":5}}'

test_endpoint \
    "windows_list_directory (missing creds)" \
    "$AUTOMATION_SERVICE_URL/ai/tools/execute" \
    "400" \
    "POST" \
    '{"name":"windows_list_directory","params":{"host":"192.168.50.211","path":"C:\\"}}'

echo ""
echo "=========================================="
echo "5. Tool Catalog Tests"
echo "=========================================="
echo ""

# Check if tool files exist
if [ -f "/home/opsconductor/opsconductor-ng/tools/catalog/asset_count.yaml" ]; then
    echo -e "${GREEN}✓ PASS${NC} asset_count.yaml exists"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} asset_count.yaml not found"
    FAILED=$((FAILED + 1))
fi

if [ -f "/home/opsconductor/opsconductor-ng/tools/catalog/asset_search.yaml" ]; then
    echo -e "${GREEN}✓ PASS${NC} asset_search.yaml exists"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} asset_search.yaml not found"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "=========================================="
echo "6. Database Schema Tests"
echo "=========================================="
echo ""

# Check if migration file exists
if [ -f "/home/opsconductor/opsconductor-ng/database/migrations/011_secrets_broker.sql" ]; then
    echo -e "${GREEN}✓ PASS${NC} Migration file exists"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} Migration file not found"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "=========================================="
echo "7. Documentation Tests"
echo "=========================================="
echo ""

if [ -f "/home/opsconductor/opsconductor-ng/docs/PR11_ASSET_INTEL_EXEC.md" ]; then
    echo -e "${GREEN}✓ PASS${NC} PR11_ASSET_INTEL_EXEC.md exists"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} PR11_ASSET_INTEL_EXEC.md not found"
    FAILED=$((FAILED + 1))
fi

if [ -f "/home/opsconductor/opsconductor-ng/docs/SECRETS_BROKER.md" ]; then
    echo -e "${GREEN}✓ PASS${NC} SECRETS_BROKER.md exists"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} SECRETS_BROKER.md not found"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "PR #11 is ready for deployment."
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC}"
    echo ""
    echo "Please review the failures above."
    exit 1
fi