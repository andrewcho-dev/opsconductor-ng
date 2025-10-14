#!/bin/bash
# PR #8 Verification Script - Fix Tools 404 Errors
# Tests that /ai/tools endpoints are accessible through Kong gateway

set -e

BASE_URL="${BASE_URL:-http://localhost:3000}"

echo "========================================"
echo "PR #8 Verification - Fix Tools 404"
echo "========================================"
echo ""

# Test 1: GET /ai/tools/list returns 200 (not 404)
echo "[Test 1] GET /ai/tools/list"
response=$(curl -s -w "\n%{http_code}" "${BASE_URL}/ai/tools/list")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    tool_count=$(echo "$body" | jq -r '.total // 0')
    echo "✓ PASS: Returns 200 OK (found $tool_count tools)"
else
    echo "✗ FAIL: Expected 200, got $http_code"
    exit 1
fi
echo ""

# Test 2: POST /ai/tools/execute with tcp_port_check returns 200 (not 404)
echo "[Test 2] POST /ai/tools/execute (tcp_port_check)"
response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/ai/tools/execute" \
    -H "Content-Type: application/json" \
    -d '{"name":"tcp_port_check","params":{"host":"127.0.0.1","port":80}}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "✓ PASS: Returns 200 OK (no 404)"
else
    echo "✗ FAIL: Expected 200, got $http_code"
    exit 1
fi
echo ""

# Test 3: POST /ai/tools/execute with dns_lookup returns 200 (not 404)
echo "[Test 3] POST /ai/tools/execute (dns_lookup)"
response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/ai/tools/execute" \
    -H "Content-Type: application/json" \
    -d '{"name":"dns_lookup","params":{"domain":"example.com","record_type":"A"}}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "✓ PASS: Returns 200 OK (no 404)"
else
    echo "✗ FAIL: Expected 200, got $http_code"
    exit 1
fi
echo ""

echo "========================================"
echo "✓ All tests passed - No 404 errors!"
echo "========================================"