#!/bin/bash

# Phase 3: Cache Testing Script
# Tests cache hit/miss performance and validates caching functionality

set -e

API_URL="http://localhost:3000"
PIPELINE_URL="$API_URL/pipeline"
CACHE_URL="$API_URL/api/v1/cache"

echo "🧪 Phase 3: Cache Testing Script"
echo "================================"
echo ""

# Test 1: Cache Statistics (Initial)
echo "📊 Test 1: Initial Cache Statistics"
echo "-----------------------------------"
curl -s "$CACHE_URL/stats" | jq '.'
echo ""

# Test 2: Cache Health Check
echo "🏥 Test 2: Cache Health Check"
echo "-----------------------------"
curl -s "$CACHE_URL/health" | jq '.'
echo ""

# Test 3: First Request (Cache MISS)
echo "❌ Test 3: First Request - Cache MISS Expected"
echo "----------------------------------------------"
echo "Query: 'list all servers in production'"
START_TIME=$(date +%s%3N)
curl -s -X POST "$PIPELINE_URL" \
  -H "Content-Type: application/json" \
  -d '{"request": "list all servers in production"}' | jq '.stage_a_time_ms, .cache_hit'
END_TIME=$(date +%s%3N)
FIRST_REQUEST_TIME=$((END_TIME - START_TIME))
echo "⏱️  First request took: ${FIRST_REQUEST_TIME}ms"
echo ""

# Test 4: Second Request (Cache HIT)
echo "✅ Test 4: Second Request - Cache HIT Expected"
echo "----------------------------------------------"
echo "Query: 'list all servers in production' (same as Test 3)"
START_TIME=$(date +%s%3N)
curl -s -X POST "$PIPELINE_URL" \
  -H "Content-Type: application/json" \
  -d '{"request": "list all servers in production"}' | jq '.stage_a_time_ms, .cache_hit'
END_TIME=$(date +%s%3N)
SECOND_REQUEST_TIME=$((END_TIME - START_TIME))
echo "⏱️  Second request took: ${SECOND_REQUEST_TIME}ms"
echo ""

# Calculate improvement
if [ $FIRST_REQUEST_TIME -gt 0 ]; then
    IMPROVEMENT=$(( (FIRST_REQUEST_TIME - SECOND_REQUEST_TIME) * 100 / FIRST_REQUEST_TIME ))
    echo "📈 Performance Improvement: ${IMPROVEMENT}% faster"
else
    echo "⚠️  Could not calculate improvement"
fi
echo ""

# Test 5: Cache Statistics (After Requests)
echo "📊 Test 5: Cache Statistics After Requests"
echo "------------------------------------------"
curl -s "$CACHE_URL/stats" | jq '.cache_stats'
echo ""

# Test 6: Different Query (Cache MISS)
echo "❌ Test 6: Different Query - Cache MISS Expected"
echo "------------------------------------------------"
echo "Query: 'restart nginx service on web-prod-01'"
START_TIME=$(date +%s%3N)
curl -s -X POST "$PIPELINE_URL" \
  -H "Content-Type: application/json" \
  -d '{"request": "restart nginx service on web-prod-01"}' | jq '.stage_a_time_ms, .cache_hit'
END_TIME=$(date +%s%3N)
THIRD_REQUEST_TIME=$((END_TIME - START_TIME))
echo "⏱️  Third request took: ${THIRD_REQUEST_TIME}ms"
echo ""

# Test 7: Repeat Different Query (Cache HIT)
echo "✅ Test 7: Repeat Different Query - Cache HIT Expected"
echo "------------------------------------------------------"
echo "Query: 'restart nginx service on web-prod-01' (same as Test 6)"
START_TIME=$(date +%s%3N)
curl -s -X POST "$PIPELINE_URL" \
  -H "Content-Type: application/json" \
  -d '{"request": "restart nginx service on web-prod-01"}' | jq '.stage_a_time_ms, .cache_hit'
END_TIME=$(date +%s%3N)
FOURTH_REQUEST_TIME=$((END_TIME - START_TIME))
echo "⏱️  Fourth request took: ${FOURTH_REQUEST_TIME}ms"
echo ""

# Test 8: Final Cache Statistics
echo "📊 Test 8: Final Cache Statistics"
echo "---------------------------------"
curl -s "$CACHE_URL/stats" | jq '.cache_stats'
echo ""

# Test 9: Cache Invalidation
echo "🗑️  Test 9: Cache Invalidation"
echo "------------------------------"
curl -s -X POST "$CACHE_URL/invalidate/all" | jq '.'
echo ""

# Test 10: Verify Cache Cleared
echo "✅ Test 10: Verify Cache Cleared"
echo "--------------------------------"
curl -s "$CACHE_URL/stats" | jq '.cache_stats'
echo ""

# Summary
echo "🎉 Cache Testing Complete!"
echo "=========================="
echo ""
echo "Summary:"
echo "--------"
echo "First request (cache miss):  ${FIRST_REQUEST_TIME}ms"
echo "Second request (cache hit):  ${SECOND_REQUEST_TIME}ms"
echo "Third request (cache miss):  ${THIRD_REQUEST_TIME}ms"
echo "Fourth request (cache hit):  ${FOURTH_REQUEST_TIME}ms"
echo ""
echo "Expected Results:"
echo "- Cache hits should be 90%+ faster than cache misses"
echo "- Hit rate should be 50% (2 hits, 2 misses)"
echo "- After invalidation, hit rate should reset to 0%"
echo ""
echo "✅ If all tests passed, Phase 3 caching is working correctly!"