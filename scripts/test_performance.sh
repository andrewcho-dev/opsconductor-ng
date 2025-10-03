#!/bin/bash

# ============================================================================
# Performance Testing Script for Tool Catalog
# Phase 3, Task 3.2: Performance Optimization
# ============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000/api/v1/tools"
CONTAINER="opsconductor-ai-pipeline"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Performance Testing - Tool Catalog System${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# Test 1: Connection Pool Configuration
# ============================================================================

echo -e "${GREEN}Test 1: Connection Pool Configuration${NC}"
echo "--------------------------------------"

PERF_STATS=$(docker exec $CONTAINER curl -s $API_BASE/performance/stats)

MIN_CONN=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['connection_pool']['min_connections'])")
MAX_CONN=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['connection_pool']['max_connections'])")
POOL_STATUS=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['connection_pool']['status'])")

echo "  Min Connections: $MIN_CONN"
echo "  Max Connections: $MAX_CONN"
echo "  Pool Status: $POOL_STATUS"

if [ "$MIN_CONN" -ge 5 ] && [ "$MAX_CONN" -ge 20 ]; then
    echo -e "  ${GREEN}✓ Connection pool optimized (min=$MIN_CONN, max=$MAX_CONN)${NC}"
else
    echo -e "  ${RED}✗ Connection pool needs optimization${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Test 2: LRU Cache Implementation
# ============================================================================

echo -e "${GREEN}Test 2: LRU Cache Implementation${NC}"
echo "--------------------------------------"

# Get initial cache stats
CACHE_SIZE=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['cache']['size'])")
MAX_SIZE=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['cache']['max_size'])")

echo "  Cache Size: $CACHE_SIZE"
echo "  Max Size: $MAX_SIZE"

if [ "$MAX_SIZE" -ge 1000 ]; then
    echo -e "  ${GREEN}✓ LRU cache configured with max_size=$MAX_SIZE${NC}"
else
    echo -e "  ${RED}✗ LRU cache not properly configured${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Test 3: Database Indexes
# ============================================================================

echo -e "${GREEN}Test 3: Database Index Verification${NC}"
echo "--------------------------------------"

# Check for composite indexes
INDEXES=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "
SELECT COUNT(*) 
FROM pg_indexes 
WHERE schemaname = 'tool_catalog' 
AND indexname LIKE 'idx_tools_%_enabled%'
")

INDEXES=$(echo $INDEXES | tr -d ' ')

echo "  Composite Indexes Found: $INDEXES"

if [ "$INDEXES" -ge 3 ]; then
    echo -e "  ${GREEN}✓ Performance indexes created ($INDEXES composite indexes)${NC}"
else
    echo -e "  ${YELLOW}⚠ Limited composite indexes found${NC}"
fi

echo ""

# ============================================================================
# Test 4: Query Performance
# ============================================================================

echo -e "${GREEN}Test 4: Query Performance Testing${NC}"
echo "--------------------------------------"

# Test query performance with EXPLAIN ANALYZE
QUERY_TIME=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "
EXPLAIN ANALYZE 
SELECT * FROM tool_catalog.tools 
WHERE tool_name = 'grep' AND is_latest = true AND enabled = true
" | grep "Execution Time" | awk '{print $3}')

echo "  Query Execution Time: ${QUERY_TIME}ms"

# Convert to float comparison
if [ $(echo "$QUERY_TIME < 10" | bc -l) -eq 1 ]; then
    echo -e "  ${GREEN}✓ Query performance excellent (<10ms)${NC}"
elif [ $(echo "$QUERY_TIME < 50" | bc -l) -eq 1 ]; then
    echo -e "  ${YELLOW}⚠ Query performance acceptable (<50ms)${NC}"
else
    echo -e "  ${RED}✗ Query performance needs optimization (>50ms)${NC}"
fi

echo ""

# ============================================================================
# Test 5: Cache Effectiveness Under Load
# ============================================================================

echo -e "${GREEN}Test 5: Cache Effectiveness Under Load${NC}"
echo "--------------------------------------"

echo "  Generating load (20 requests)..."

# Make multiple requests to populate cache
for i in {1..20}; do
    docker exec $CONTAINER curl -s $API_BASE/grep > /dev/null 2>&1 || true
    docker exec $CONTAINER curl -s $API_BASE/htop > /dev/null 2>&1 || true
done

# Get updated cache stats
PERF_STATS=$(docker exec $CONTAINER curl -s $API_BASE/performance/stats)

CACHE_HITS=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['cache']['hits'])")
CACHE_MISSES=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['cache']['misses'])")
HIT_RATE=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['cache']['hit_rate'])")

echo "  Cache Hits: $CACHE_HITS"
echo "  Cache Misses: $CACHE_MISSES"
echo "  Hit Rate: ${HIT_RATE}%"

if [ $(echo "$HIT_RATE >= 80" | bc -l) -eq 1 ]; then
    echo -e "  ${GREEN}✓ Cache hit rate excellent (>80%)${NC}"
elif [ $(echo "$HIT_RATE >= 50" | bc -l) -eq 1 ]; then
    echo -e "  ${YELLOW}⚠ Cache hit rate acceptable (>50%)${NC}"
else
    echo -e "  ${YELLOW}⚠ Cache warming up (hit rate will improve with usage)${NC}"
fi

echo ""

# ============================================================================
# Test 6: Database Cache Hit Ratio
# ============================================================================

echo -e "${GREEN}Test 6: Database Cache Hit Ratio${NC}"
echo "--------------------------------------"

DB_CACHE_RATIO=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['database']['cache_hit_ratio'])")

echo "  Database Cache Hit Ratio: ${DB_CACHE_RATIO}%"

if [ $(echo "$DB_CACHE_RATIO >= 99" | bc -l) -eq 1 ]; then
    echo -e "  ${GREEN}✓ Database cache excellent (>99%)${NC}"
elif [ $(echo "$DB_CACHE_RATIO >= 95" | bc -l) -eq 1 ]; then
    echo -e "  ${YELLOW}⚠ Database cache good (>95%)${NC}"
else
    echo -e "  ${RED}✗ Database cache needs tuning (<95%)${NC}"
fi

echo ""

# ============================================================================
# Test 7: Concurrent Request Handling
# ============================================================================

echo -e "${GREEN}Test 7: Concurrent Request Handling${NC}"
echo "--------------------------------------"

echo "  Testing with 10 concurrent requests..."

START_TIME=$(date +%s%N)

# Run 10 concurrent requests
for i in {1..10}; do
    docker exec $CONTAINER curl -s $API_BASE/grep > /dev/null 2>&1 &
done

# Wait for all background jobs
wait

END_TIME=$(date +%s%N)
DURATION=$(( ($END_TIME - $START_TIME) / 1000000 ))

echo "  Total Time: ${DURATION}ms"
echo "  Average per Request: $((DURATION / 10))ms"

if [ $DURATION -lt 1000 ]; then
    echo -e "  ${GREEN}✓ Concurrent handling excellent (<1s for 10 requests)${NC}"
elif [ $DURATION -lt 2000 ]; then
    echo -e "  ${YELLOW}⚠ Concurrent handling acceptable (<2s for 10 requests)${NC}"
else
    echo -e "  ${RED}✗ Concurrent handling needs optimization (>2s for 10 requests)${NC}"
fi

echo ""

# ============================================================================
# Test 8: Memory Usage
# ============================================================================

echo -e "${GREEN}Test 8: Memory Usage${NC}"
echo "--------------------------------------"

# Get cache size
CACHE_SIZE=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['cache']['size'])")
MAX_SIZE=$(echo $PERF_STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['performance']['cache']['max_size'])")

USAGE_PERCENT=$((CACHE_SIZE * 100 / MAX_SIZE))

echo "  Cache Usage: $CACHE_SIZE / $MAX_SIZE ($USAGE_PERCENT%)"

if [ $USAGE_PERCENT -lt 80 ]; then
    echo -e "  ${GREEN}✓ Memory usage healthy (<80%)${NC}"
elif [ $USAGE_PERCENT -lt 95 ]; then
    echo -e "  ${YELLOW}⚠ Memory usage high (>80%)${NC}"
else
    echo -e "  ${RED}✗ Memory usage critical (>95%)${NC}"
fi

echo ""

# ============================================================================
# Test 9: Index Usage Statistics
# ============================================================================

echo -e "${GREEN}Test 9: Index Usage Statistics${NC}"
echo "--------------------------------------"

# Get index usage stats
INDEX_STATS=$(docker exec opsconductor-postgres psql -U opsconductor -d opsconductor -t -c "
SELECT 
    indexrelname,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'tool_catalog'
AND indexrelname LIKE 'idx_tools_name%'
ORDER BY idx_scan DESC
LIMIT 3
")

echo "  Top Used Indexes:"
echo "$INDEX_STATS" | while read -r line; do
    if [ ! -z "$line" ]; then
        echo "    $line"
    fi
done

echo -e "  ${GREEN}✓ Index statistics collected${NC}"

echo ""

# ============================================================================
# Test 10: Overall Performance Score
# ============================================================================

echo -e "${GREEN}Test 10: Overall Performance Score${NC}"
echo "--------------------------------------"

# Calculate performance score based on metrics
SCORE=0

# Connection pool (20 points)
if [ "$MIN_CONN" -ge 5 ] && [ "$MAX_CONN" -ge 20 ]; then
    SCORE=$((SCORE + 20))
fi

# LRU cache (20 points)
if [ "$MAX_SIZE" -ge 1000 ]; then
    SCORE=$((SCORE + 20))
fi

# Query performance (20 points)
if [ $(echo "$QUERY_TIME < 10" | bc -l) -eq 1 ]; then
    SCORE=$((SCORE + 20))
elif [ $(echo "$QUERY_TIME < 50" | bc -l) -eq 1 ]; then
    SCORE=$((SCORE + 10))
fi

# Database cache (20 points)
if [ $(echo "$DB_CACHE_RATIO >= 99" | bc -l) -eq 1 ]; then
    SCORE=$((SCORE + 20))
elif [ $(echo "$DB_CACHE_RATIO >= 95" | bc -l) -eq 1 ]; then
    SCORE=$((SCORE + 10))
fi

# Concurrent handling (20 points)
if [ $DURATION -lt 1000 ]; then
    SCORE=$((SCORE + 20))
elif [ $DURATION -lt 2000 ]; then
    SCORE=$((SCORE + 10))
fi

echo "  Performance Score: $SCORE / 100"

if [ $SCORE -ge 90 ]; then
    echo -e "  ${GREEN}✓ EXCELLENT - System is highly optimized${NC}"
elif [ $SCORE -ge 70 ]; then
    echo -e "  ${YELLOW}⚠ GOOD - System is well optimized${NC}"
elif [ $SCORE -ge 50 ]; then
    echo -e "  ${YELLOW}⚠ ACCEPTABLE - Some optimization needed${NC}"
else
    echo -e "  ${RED}✗ NEEDS WORK - Significant optimization required${NC}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Performance Test Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo "Optimizations Applied:"
echo "  ✓ Connection pool: $MIN_CONN-$MAX_CONN connections"
echo "  ✓ LRU cache: max_size=$MAX_SIZE"
echo "  ✓ Composite indexes: $INDEXES indexes"
echo "  ✓ Query time: ${QUERY_TIME}ms"
echo "  ✓ Cache hit rate: ${HIT_RATE}%"
echo "  ✓ DB cache ratio: ${DB_CACHE_RATIO}%"
echo ""
echo "Overall Performance Score: $SCORE / 100"
echo ""

if [ $SCORE -ge 70 ]; then
    echo -e "${GREEN}✓ Performance optimization SUCCESSFUL${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Performance optimization needs more work${NC}"
    exit 1
fi