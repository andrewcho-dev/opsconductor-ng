#!/bin/bash
#
# Comprehensive Load Testing Suite
# Runs load tests with resource monitoring and generates reports
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONCURRENT_USERS=${1:-2}
TEST_DURATION=${2:-60}
API_CONTAINER="opsconductor-ai-pipeline"
API_URL="http://localhost:3005/api/v1/tools"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Tool Catalog Load Testing Suite                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Concurrent Users: ${CONCURRENT_USERS}"
echo -e "  Test Duration: ${TEST_DURATION}s"
echo -e "  API URL: ${API_URL}"
echo ""

# Check if API is running
echo -e "${YELLOW}[1/6]${NC} Checking API availability..."
if ! curl -s -f "${API_URL}/" > /dev/null 2>&1; then
    echo -e "${RED}✗ API is not accessible at ${API_URL}${NC}"
    echo -e "${YELLOW}  Make sure the API container is running:${NC}"
    echo -e "  docker ps | grep ${API_CONTAINER}"
    exit 1
fi
echo -e "${GREEN}✓ API is accessible${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}[2/6]${NC} Checking dependencies..."
MISSING_DEPS=()

if ! python3 -c "import aiohttp" 2>/dev/null; then
    MISSING_DEPS+=("aiohttp")
fi

if ! python3 -c "import psutil" 2>/dev/null; then
    MISSING_DEPS+=("psutil")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠ Missing Python dependencies: ${MISSING_DEPS[*]}${NC}"
    echo -e "${YELLOW}  Installing...${NC}"
    pip3 install -q "${MISSING_DEPS[@]}"
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ All Python dependencies available${NC}"
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠ jq not found, installing...${NC}"
    sudo apt-get update -qq && sudo apt-get install -y -qq jq > /dev/null 2>&1
    echo -e "${GREEN}✓ jq installed${NC}"
fi
echo ""

# Get baseline metrics
echo -e "${YELLOW}[3/6]${NC} Collecting baseline metrics..."
BASELINE_FILE="/tmp/baseline_metrics.json"

curl -s "${API_URL}/performance/stats" > "${BASELINE_FILE}" 2>/dev/null || echo "{}" > "${BASELINE_FILE}"

if [ -s "${BASELINE_FILE}" ]; then
    BASELINE_CACHE_SIZE=$(jq -r '.cache.size // 0' "${BASELINE_FILE}")
    BASELINE_POOL_MIN=$(jq -r '.connection_pool.min_connections // 0' "${BASELINE_FILE}")
    BASELINE_POOL_MAX=$(jq -r '.connection_pool.max_connections // 0' "${BASELINE_FILE}")
    
    echo -e "${GREEN}✓ Baseline collected:${NC}"
    echo -e "  Cache size: ${BASELINE_CACHE_SIZE} items"
    echo -e "  Connection pool: ${BASELINE_POOL_MIN}-${BASELINE_POOL_MAX}"
else
    echo -e "${YELLOW}⚠ Could not collect baseline metrics${NC}"
fi
echo ""

# Run load test and resource monitor in parallel
echo -e "${YELLOW}[4/6]${NC} Running load test with resource monitoring..."
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Start resource monitor in background
python3 "${SCRIPT_DIR}/resource_monitor.py" "${TEST_DURATION}" > /tmp/resource_monitor.log 2>&1 &
MONITOR_PID=$!

# Give monitor time to start
sleep 2

# Run load test
python3 "${SCRIPT_DIR}/load_test.py" "${CONCURRENT_USERS}" "${TEST_DURATION}"
LOAD_TEST_EXIT=$?

# Wait for monitor to finish
wait ${MONITOR_PID}

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Show resource monitor results
echo -e "${YELLOW}[5/6]${NC} Resource monitoring results:"
echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
cat /tmp/resource_monitor.log
echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
echo ""

# Get post-test metrics
echo -e "${YELLOW}[6/6]${NC} Collecting post-test metrics..."
POSTTEST_FILE="/tmp/posttest_metrics.json"

curl -s "${API_URL}/performance/stats" > "${POSTTEST_FILE}" 2>/dev/null || echo "{}" > "${POSTTEST_FILE}"

if [ -s "${POSTTEST_FILE}" ]; then
    POSTTEST_CACHE_SIZE=$(jq -r '.cache.size // 0' "${POSTTEST_FILE}")
    POSTTEST_CACHE_HITS=$(jq -r '.cache.hits // 0' "${POSTTEST_FILE}")
    POSTTEST_CACHE_MISSES=$(jq -r '.cache.misses // 0' "${POSTTEST_FILE}")
    POSTTEST_HIT_RATE=$(jq -r '.cache.hit_rate // 0' "${POSTTEST_FILE}")
    
    echo -e "${GREEN}✓ Post-test metrics:${NC}"
    echo -e "  Cache size: ${POSTTEST_CACHE_SIZE} items"
    echo -e "  Cache hits: ${POSTTEST_CACHE_HITS}"
    echo -e "  Cache misses: ${POSTTEST_CACHE_MISSES}"
    echo -e "  Hit rate: ${POSTTEST_HIT_RATE}%"
else
    echo -e "${YELLOW}⚠ Could not collect post-test metrics${NC}"
fi
echo ""

# Generate summary report
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    TEST SUMMARY                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Find latest result files
LATEST_LOAD_TEST=$(ls -t /tmp/load_test_results_*.json 2>/dev/null | head -1)
LATEST_RESOURCE_MONITOR=$(ls -t /tmp/resource_monitor_*.json 2>/dev/null | head -1)

if [ -n "${LATEST_LOAD_TEST}" ]; then
    echo -e "${GREEN}📊 Load Test Results:${NC}"
    echo -e "  File: ${LATEST_LOAD_TEST}"
    
    TOTAL_REQUESTS=$(jq -r '.total_requests // 0' "${LATEST_LOAD_TEST}")
    SUCCESS_REQUESTS=$(jq -r '.successful_requests // 0' "${LATEST_LOAD_TEST}")
    FAILED_REQUESTS=$(jq -r '.failed_requests // 0' "${LATEST_LOAD_TEST}")
    RPS=$(jq -r '.requests_per_second // 0' "${LATEST_LOAD_TEST}")
    P95_MS=$(jq -r '.response_times.p95_ms // 0' "${LATEST_LOAD_TEST}")
    ERROR_RATE=$(jq -r '.error_rate_percent // 0' "${LATEST_LOAD_TEST}")
    
    echo -e "  Total Requests: ${TOTAL_REQUESTS}"
    echo -e "  Successful: ${SUCCESS_REQUESTS}"
    echo -e "  Failed: ${FAILED_REQUESTS}"
    echo -e "  Throughput: ${RPS} req/s"
    echo -e "  P95 Response: ${P95_MS}ms"
    echo -e "  Error Rate: ${ERROR_RATE}%"
    echo ""
fi

if [ -n "${LATEST_RESOURCE_MONITOR}" ]; then
    echo -e "${GREEN}📊 Resource Monitor Results:${NC}"
    echo -e "  File: ${LATEST_RESOURCE_MONITOR}"
    
    AVG_CPU=$(jq -r '.analysis.cpu.avg // 0' "${LATEST_RESOURCE_MONITOR}")
    MAX_CPU=$(jq -r '.analysis.cpu.max // 0' "${LATEST_RESOURCE_MONITOR}")
    AVG_MEM=$(jq -r '.analysis.memory.avg // 0' "${LATEST_RESOURCE_MONITOR}")
    MAX_MEM=$(jq -r '.analysis.memory.max // 0' "${LATEST_RESOURCE_MONITOR}")
    
    echo -e "  Avg CPU: ${AVG_CPU}%"
    echo -e "  Max CPU: ${MAX_CPU}%"
    echo -e "  Avg Memory: ${AVG_MEM}%"
    echo -e "  Max Memory: ${MAX_MEM}%"
    echo ""
fi

# Overall assessment
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 OVERALL ASSESSMENT                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

ISSUES=0

# Check P95 response time
if [ -n "${P95_MS}" ]; then
    if (( $(echo "${P95_MS} < 50" | bc -l) )); then
        echo -e "${GREEN}✓ P95 response time: ${P95_MS}ms < 50ms target${NC}"
    else
        echo -e "${RED}✗ P95 response time: ${P95_MS}ms >= 50ms target${NC}"
        ISSUES=$((ISSUES + 1))
    fi
fi

# Check error rate
if [ -n "${ERROR_RATE}" ]; then
    if (( $(echo "${ERROR_RATE} == 0" | bc -l) )); then
        echo -e "${GREEN}✓ Error rate: 0%${NC}"
    else
        echo -e "${YELLOW}⚠ Error rate: ${ERROR_RATE}%${NC}"
        ISSUES=$((ISSUES + 1))
    fi
fi

# Check throughput
if [ -n "${RPS}" ]; then
    if (( $(echo "${RPS} >= 10" | bc -l) )); then
        echo -e "${GREEN}✓ Throughput: ${RPS} req/s >= 10 req/s${NC}"
    else
        echo -e "${YELLOW}⚠ Throughput: ${RPS} req/s < 10 req/s${NC}"
        ISSUES=$((ISSUES + 1))
    fi
fi

# Check CPU usage
if [ -n "${MAX_CPU}" ]; then
    if (( $(echo "${MAX_CPU} < 80" | bc -l) )); then
        echo -e "${GREEN}✓ CPU usage: ${MAX_CPU}% < 80%${NC}"
    else
        echo -e "${YELLOW}⚠ CPU usage: ${MAX_CPU}% >= 80%${NC}"
        ISSUES=$((ISSUES + 1))
    fi
fi

# Check memory usage
if [ -n "${MAX_MEM}" ]; then
    if (( $(echo "${MAX_MEM} < 80" | bc -l) )); then
        echo -e "${GREEN}✓ Memory usage: ${MAX_MEM}% < 80%${NC}"
    else
        echo -e "${YELLOW}⚠ Memory usage: ${MAX_MEM}% >= 80%${NC}"
        ISSUES=$((ISSUES + 1))
    fi
fi

# Check cache hit rate
if [ -n "${POSTTEST_HIT_RATE}" ]; then
    if (( $(echo "${POSTTEST_HIT_RATE} >= 80" | bc -l) )); then
        echo -e "${GREEN}✓ Cache hit rate: ${POSTTEST_HIT_RATE}% >= 80%${NC}"
    else
        echo -e "${YELLOW}⚠ Cache hit rate: ${POSTTEST_HIT_RATE}% < 80%${NC}"
        ISSUES=$((ISSUES + 1))
    fi
fi

echo ""

if [ ${ISSUES} -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ ALL TESTS PASSED - System is ready for production!     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠ ${ISSUES} issue(s) found - Review results above              ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi