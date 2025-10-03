#!/bin/bash

# End-to-End Testing Script for 170-Tool Catalog Integration
# This script runs comprehensive E2E tests to validate the complete system

set -e

echo "=========================================="
echo "Tool Catalog E2E Testing"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo -e "${GREEN}✓${NC} Running inside Docker container"
else
    echo -e "${YELLOW}⚠${NC} Not running in Docker - some tests may fail"
    echo "   Consider running: docker-compose exec api bash -c './scripts/run_e2e_tests.sh'"
fi

echo ""
echo "=========================================="
echo "Test Suite: Tool Catalog E2E"
echo "=========================================="
echo ""

# Run the comprehensive E2E test suite
echo -e "${BLUE}Running tool catalog E2E tests...${NC}"
pytest /home/opsconductor/opsconductor-ng/tests/test_tool_catalog_e2e.py -v -s --tb=short

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All E2E tests passed!${NC}"
    echo ""
    echo "System Status:"
    echo "  ✓ 170 tools deployed and accessible"
    echo "  ✓ Database integration working"
    echo "  ✓ HybridOrchestrator operational"
    echo "  ✓ End-to-end pipeline functional"
    echo "  ✓ Performance within targets"
    echo ""
    echo "The system is ready for production use!"
else
    echo -e "${YELLOW}⚠ Some tests failed${NC}"
    echo ""
    echo "Please review the test output above for details."
    echo "Common issues:"
    echo "  - Database not accessible (check PostgreSQL)"
    echo "  - LLM service not available (check Ollama)"
    echo "  - Missing dependencies (check requirements.txt)"
fi

echo ""
echo "=========================================="

exit $TEST_EXIT_CODE