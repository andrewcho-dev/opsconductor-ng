#!/bin/bash
# ============================================================================
# Run Windows Tools Enhancement (Docker Version)
# ============================================================================
# Purpose: Execute SQL enhancement script via Docker to improve tool quality
# Expected Result: 12 Windows tools enhanced from B+ (85%) to A+ (95%+)
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "WINDOWS TOOLS ENHANCEMENT"
echo "============================================================================"
echo ""
echo "This script will enhance 12 Windows tools with:"
echo "  ✅ Enhanced descriptions with synonyms"
echo "  ✅ Expanded use cases (7-10 items)"
echo "  ✅ Validation patterns on inputs"
echo "  ✅ Concrete examples (2-3 per tool)"
echo ""
echo "Expected Impact:"
echo "  📈 Semantic search accuracy: 75-85% → 95%+"
echo "  📈 Parameter generation: 70-80% → 90%+"
echo "  📈 Overall quality grade: B+ (85) → A+ (95)"
echo ""
echo "============================================================================"
echo ""

# Check if Docker container is running
if ! docker ps | grep -q opsconductor-postgres; then
    echo "❌ ERROR: PostgreSQL container 'opsconductor-postgres' is not running"
    echo "Please start the container with: docker-compose up -d postgres"
    exit 1
fi

echo "📊 Step 1: Checking current tool quality..."
echo ""

# Count tools with examples (before enhancement)
BEFORE_COUNT=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "
SELECT COUNT(*) 
FROM tool_catalog.tool_patterns tp
JOIN tool_catalog.tool_capabilities tc ON tc.id = tp.capability_id
JOIN tool_catalog.tools t ON t.id = tc.tool_id
WHERE t.tool_name IN (
    'Set-Content', 'Add-Content', 'Where-Object', 'Sort-Object', 'Select-Object',
    'Resolve-DnsName', 'ipconfig', 'Get-NetTCPConnection', 'Invoke-RestMethod',
    'Start-Process', 'Compress-Archive', 'Expand-Archive'
)
AND tp.examples != '[]'::jsonb;
" | tr -d ' ' | tr -d '\r')

echo "Tools with examples (before): $BEFORE_COUNT / 12"
echo ""

echo "🚀 Step 2: Running enhancement script..."
echo ""

# Copy SQL file to container and execute
docker cp /home/opsconductor/opsconductor-ng/scripts/enhance_all_windows_tools.sql opsconductor-postgres:/tmp/enhance.sql
docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -f /tmp/enhance.sql

echo ""
echo "📊 Step 3: Validating enhancements..."
echo ""

# Count tools with examples (after enhancement)
AFTER_COUNT=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "
SELECT COUNT(*) 
FROM tool_catalog.tool_patterns tp
JOIN tool_catalog.tool_capabilities tc ON tc.id = tp.capability_id
JOIN tool_catalog.tools t ON t.id = tc.tool_id
WHERE t.tool_name IN (
    'Set-Content', 'Add-Content', 'Where-Object', 'Sort-Object', 'Select-Object',
    'Resolve-DnsName', 'ipconfig', 'Get-NetTCPConnection', 'Invoke-RestMethod',
    'Start-Process', 'Compress-Archive', 'Expand-Archive'
)
AND tp.examples != '[]'::jsonb;
" | tr -d ' ' | tr -d '\r')

echo "Tools with examples (after): $AFTER_COUNT / 12"
echo ""

# Calculate improvement
IMPROVEMENT=$((AFTER_COUNT - BEFORE_COUNT))

if [ $IMPROVEMENT -gt 0 ]; then
    echo "✅ SUCCESS: Enhanced $IMPROVEMENT tools"
else
    echo "⚠️  WARNING: No new tools enhanced (may already be enhanced)"
fi

echo ""
echo "📋 Step 4: Displaying sample enhanced tool..."
echo ""

# Show one enhanced tool as example
docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -c "
SELECT 
    t.tool_name,
    tc.capability_name,
    LEFT(tp.description, 80) || '...' as description,
    jsonb_array_length(tp.typical_use_cases) as use_case_count,
    jsonb_array_length(tp.examples) as example_count
FROM tool_catalog.tools t
JOIN tool_catalog.tool_capabilities tc ON tc.tool_id = t.id
JOIN tool_catalog.tool_patterns tp ON tp.capability_id = tc.id
WHERE t.tool_name = 'Where-Object'
LIMIT 1;
"

echo ""
echo "============================================================================"
echo "ENHANCEMENT COMPLETE"
echo "============================================================================"
echo ""
echo "Next Steps:"
echo "  1. ✅ Review enhanced tools in database"
echo "  2. ⏳ Test tool selector with enhanced metadata"
echo "  3. ⏳ Complete remaining tools (Tier 2 + Tier 3)"
echo "  4. ⏳ Run quality audit: python scripts/audit_tool_quality.py"
echo "  5. ⏳ Backfill embeddings: python scripts/backfill_tool_embeddings.py"
echo ""
echo "============================================================================"