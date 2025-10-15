#!/bin/bash
# verify_tools.sh - Verify tool registry contains required tools
# Usage: ./scripts/verify_tools.sh

set -e

BASE_URL="${AUTOMATION_SERVICE_URL:-http://localhost:8010}"
REQUIRED_TOOLS=("asset_count" "asset_search" "windows_list_directory")

echo "========================================="
echo "Tool Registry Verification"
echo "========================================="
echo "Base URL: $BASE_URL"
echo ""

# Fetch tool list
echo "Fetching tool list from $BASE_URL/ai/tools/list..."
RESPONSE=$(curl -s "$BASE_URL/ai/tools/list")

if [ $? -ne 0 ]; then
    echo "❌ FAILED: Could not connect to automation-service"
    exit 1
fi

echo "✅ Connected to automation-service"
echo ""

# Extract tool names (without jq)
echo "Available tools:"
echo "$RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | while read -r tool; do
    echo "  - $tool"
done
echo ""

# Check for required tools
echo "Checking for required tools..."
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if echo "$RESPONSE" | grep -q "\"name\":\"$tool\""; then
        echo "  ✅ $tool - FOUND"
    else
        echo "  ❌ $tool - MISSING"
        MISSING_TOOLS+=("$tool")
    fi
done

echo ""

# Final result
if [ ${#MISSING_TOOLS[@]} -eq 0 ]; then
    echo "========================================="
    echo "✅ SUCCESS: All required tools present"
    echo "========================================="
    exit 0
else
    echo "========================================="
    echo "❌ FAILED: Missing required tools:"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo "  - $tool"
    done
    echo "========================================="
    exit 1
fi