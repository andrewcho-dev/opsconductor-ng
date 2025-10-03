#!/bin/bash
#
# Simple Load Testing Script (no external dependencies)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONCURRENT_USERS=${1:-2}
TEST_DURATION=${2:-60}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Tool Catalog Load Testing Suite                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Concurrent Users: ${CONCURRENT_USERS}"
echo -e "  Test Duration: ${TEST_DURATION}s"
echo ""

# Check Python dependencies
echo -e "${YELLOW}[1/3]${NC} Checking Python dependencies..."
MISSING_DEPS=()

if ! python3 -c "import aiohttp" 2>/dev/null; then
    MISSING_DEPS+=("aiohttp")
fi

if ! python3 -c "import psutil" 2>/dev/null; then
    MISSING_DEPS+=("psutil")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠ Missing dependencies: ${MISSING_DEPS[*]}${NC}"
    echo -e "${YELLOW}  Installing...${NC}"
    pip3 install -q "${MISSING_DEPS[@]}"
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ All dependencies available${NC}"
fi
echo ""

# Run load test and resource monitor in parallel
echo -e "${YELLOW}[2/3]${NC} Running load test with resource monitoring..."
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
wait ${MONITOR_PID} 2>/dev/null || true

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Show resource monitor results
echo -e "${YELLOW}[3/3]${NC} Resource monitoring results:"
echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
cat /tmp/resource_monitor.log
echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    TEST COMPLETE                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Find latest result files
LATEST_LOAD_TEST=$(ls -t /tmp/load_test_results_*.json 2>/dev/null | head -1)
LATEST_RESOURCE_MONITOR=$(ls -t /tmp/resource_monitor_*.json 2>/dev/null | head -1)

if [ -n "${LATEST_LOAD_TEST}" ]; then
    echo -e "${GREEN}📊 Load Test Results:${NC}"
    echo -e "  File: ${LATEST_LOAD_TEST}"
    echo ""
fi

if [ -n "${LATEST_RESOURCE_MONITOR}" ]; then
    echo -e "${GREEN}📊 Resource Monitor Results:${NC}"
    echo -e "  File: ${LATEST_RESOURCE_MONITOR}"
    echo ""
fi

if [ ${LOAD_TEST_EXIT} -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ ALL TESTS PASSED - System is ready for production!     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠ Some issues found - Review results above               ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi