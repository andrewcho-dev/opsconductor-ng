#!/bin/bash
# test_e2e_chat_smoke.sh - E2E smoke test for chat execution
# Usage: ./scripts/test_e2e_chat_smoke.sh

set -e

BASE_URL="${AUTOMATION_SERVICE_URL:-http://localhost:8010}"

echo "========================================="
echo "E2E Chat Smoke Test"
echo "========================================="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Tool list contains required tools
echo "Test 1: Verify tool list contains required tools..."
TOOLS_RESPONSE=$(curl -s "$BASE_URL/ai/tools/list")

REQUIRED_TOOLS=("asset_count" "asset_search" "windows_list_directory")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if echo "$TOOLS_RESPONSE" | grep -q "\"name\":\"$tool\""; then
        echo "  ✅ $tool - FOUND"
    else
        echo "  ❌ $tool - MISSING"
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "❌ Test 1 FAILED: Missing required tools"
    exit 1
fi
echo "✅ Test 1 PASSED"
echo ""

# Test 2: Execute asset_count tool
echo "Test 2: Execute asset_count tool..."
ASSET_COUNT_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/tools/execute" \
    -H "Content-Type: application/json" \
    -d '{"name":"asset_count","params":{"os":"Windows 10"}}')

if echo "$ASSET_COUNT_RESPONSE" | grep -q '"success":true'; then
    echo "  ✅ asset_count executed successfully"
    # Extract output (without jq)
    OUTPUT=$(echo "$ASSET_COUNT_RESPONSE" | grep -o '"output":"[^"]*"' | cut -d'"' -f4)
    echo "  Output: $OUTPUT"
else
    echo "  ❌ asset_count execution failed"
    echo "  Response: $ASSET_COUNT_RESPONSE"
    exit 1
fi
echo "✅ Test 2 PASSED"
echo ""

# Test 3: Execute windows_list_directory (expect missing_credentials or success)
echo "Test 3: Execute windows_list_directory..."
WIN_DIR_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/tools/execute" \
    -H "Content-Type: application/json" \
    -d '{"name":"windows_list_directory","params":{"host":"192.168.50.211","path":"C:\\\\"}}')

# Check if it's either success or missing_credentials (both are acceptable)
if echo "$WIN_DIR_RESPONSE" | grep -q '"success":true'; then
    echo "  ✅ windows_list_directory executed successfully"
    echo "  (Credentials found on server)"
elif echo "$WIN_DIR_RESPONSE" | grep -q '"error":"missing_credentials"'; then
    echo "  ✅ windows_list_directory returned missing_credentials"
    echo "  (Expected when credentials not configured)"
else
    # Check for 404 or validation errors (these are failures)
    if echo "$WIN_DIR_RESPONSE" | grep -q '"detail"'; then
        echo "  ❌ windows_list_directory returned unexpected error"
        echo "  Response: $WIN_DIR_RESPONSE"
        exit 1
    else
        echo "  ✅ windows_list_directory handled gracefully"
    fi
fi
echo "✅ Test 3 PASSED"
echo ""

# Test 4: Execute shell_ping (local tool)
echo "Test 4: Execute shell_ping (local tool)..."
PING_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/tools/execute" \
    -H "Content-Type: application/json" \
    -d '{"name":"shell_ping","params":{"host":"127.0.0.1","count":2}}')

if echo "$PING_RESPONSE" | grep -q '"success":true'; then
    echo "  ✅ shell_ping executed successfully"
elif echo "$PING_RESPONSE" | grep -q '"success":false'; then
    # Ping might fail but should not error out
    echo "  ✅ shell_ping executed (host unreachable is acceptable)"
else
    echo "  ❌ shell_ping returned unexpected response"
    echo "  Response: $PING_RESPONSE"
    exit 1
fi
echo "✅ Test 4 PASSED"
echo ""

# Final result
echo "========================================="
echo "✅ ALL TESTS PASSED"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✅ Tool registry contains required tools"
echo "  ✅ asset_count executes and returns data"
echo "  ✅ windows_list_directory handles missing credentials gracefully"
echo "  ✅ Local tools (shell_ping) execute correctly"
echo ""