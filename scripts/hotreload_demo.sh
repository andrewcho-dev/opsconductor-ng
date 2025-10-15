#!/bin/bash
# hotreload_demo.sh - Demonstrate hot-reload of tool catalog
# Usage: ./scripts/hotreload_demo.sh

set -e

BASE_URL="${AUTOMATION_SERVICE_URL:-http://localhost:8010}"
CONTAINER_NAME="${AUTOMATION_CONTAINER:-opsconductor-automation}"
CATALOG_DIR="/app/tools/catalog"
TEMP_TOOL="$CATALOG_DIR/demo_temp_tool.yaml"

echo "========================================="
echo "Tool Hot-Reload Demo"
echo "========================================="
echo "Base URL: $BASE_URL"
echo "Catalog Dir: $CATALOG_DIR"
echo ""

# Step 1: Show initial tool count
echo "Step 1: Fetching initial tool list..."
INITIAL_RESPONSE=$(curl -s "$BASE_URL/ai/tools/list")
INITIAL_COUNT=$(echo "$INITIAL_RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo "Initial tool count: $INITIAL_COUNT"
echo ""

# Step 2: Create a temporary tool
echo "Step 2: Creating temporary tool in container..."
cat > /tmp/demo_temp_tool.yaml <<'EOF'
name: demo_temp_tool
display_name: Demo Temporary Tool
description: A temporary tool for hot-reload demonstration
category: demo
platform: cross-platform
version: 1.0.0
source: local

parameters:
  - name: message
    type: string
    description: Message to display
    required: true

timeout_seconds: 5
requires_admin: false

tags:
  - demo
  - temporary
EOF

docker cp /tmp/demo_temp_tool.yaml "$CONTAINER_NAME:$TEMP_TOOL"
echo "✅ Created temporary tool: $TEMP_TOOL"
echo ""

# Step 3: Trigger reload
echo "Step 3: Triggering tool registry reload..."
RELOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/tools/reload")
echo "$RELOAD_RESPONSE" | grep -o '"success":[^,]*' | head -1
RELOAD_COUNT=$(echo "$RELOAD_RESPONSE" | grep -o '"count":[0-9]*' | cut -d':' -f2)
echo "Tool count after reload: $RELOAD_COUNT"
echo ""

# Step 4: Verify new tool is present
echo "Step 4: Verifying new tool is present..."
VERIFY_RESPONSE=$(curl -s "$BASE_URL/ai/tools/list")
if echo "$VERIFY_RESPONSE" | grep -q '"name":"demo_temp_tool"'; then
    echo "✅ demo_temp_tool FOUND in registry"
else
    echo "❌ demo_temp_tool NOT FOUND in registry"
fi
echo ""

# Step 5: Remove temporary tool
echo "Step 5: Removing temporary tool from container..."
docker exec "$CONTAINER_NAME" rm -f "$TEMP_TOOL"
echo "✅ Removed temporary tool: $TEMP_TOOL"
echo ""

# Step 6: Trigger reload again
echo "Step 6: Triggering tool registry reload again..."
RELOAD2_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/tools/reload")
RELOAD2_COUNT=$(echo "$RELOAD2_RESPONSE" | grep -o '"count":[0-9]*' | cut -d':' -f2)
echo "Tool count after second reload: $RELOAD2_COUNT"
echo ""

# Step 7: Verify tool is removed
echo "Step 7: Verifying tool is removed..."
VERIFY2_RESPONSE=$(curl -s "$BASE_URL/ai/tools/list")
if echo "$VERIFY2_RESPONSE" | grep -q '"name":"demo_temp_tool"'; then
    echo "❌ demo_temp_tool still FOUND in registry (should be removed)"
else
    echo "✅ demo_temp_tool NOT FOUND in registry (correctly removed)"
fi
echo ""

# Final result
echo "========================================="
echo "✅ Hot-Reload Demo Complete"
echo "========================================="
echo "Initial count: $INITIAL_COUNT"
echo "After add:     $RELOAD_COUNT"
echo "After remove:  $RELOAD2_COUNT"
echo ""