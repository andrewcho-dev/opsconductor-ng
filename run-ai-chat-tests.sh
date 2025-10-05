#!/bin/bash

# AI Chat Intensive Testing Runner
# This script helps run the AI chat tests with various options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BASE_URL="${BASE_URL:-http://localhost:3000}"
TEST_USERNAME="${TEST_USERNAME:-admin}"
TEST_PASSWORD="${TEST_PASSWORD:-admin}"
MODE="all"
HEADED=false
DEBUG=false
UI=false

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║        AI CHAT INTENSIVE TESTING SUITE                     ║"
    echo "║        OpsConductor - Real-World Performance Testing      ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -m, --mode MODE       Test mode: all, asset, performance, multi-turn, error (default: all)"
    echo "  -h, --headed          Run with headed browser (watch tests execute)"
    echo "  -d, --debug           Run in debug mode (step through tests)"
    echo "  -u, --ui              Run in UI mode (interactive)"
    echo "  -b, --base-url URL    Base URL for testing (default: http://localhost:3000)"
    echo "  --username USER       Test username (default: admin)"
    echo "  --password PASS       Test password (default: admin)"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests"
    echo "  $0 -m asset                           # Run only asset query tests"
    echo "  $0 -m performance --headed            # Run performance tests with visible browser"
    echo "  $0 -u                                 # Run in interactive UI mode"
    echo "  $0 -d                                 # Run in debug mode"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -h|--headed)
            HEADED=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -u|--ui)
            UI=true
            shift
            ;;
        -b|--base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --username)
            TEST_USERNAME="$2"
            shift 2
            ;;
        --password)
            TEST_PASSWORD="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

print_banner

# Check if Playwright is installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! command -v npx &> /dev/null; then
    echo -e "${RED}Error: npx not found. Please install Node.js${NC}"
    exit 1
fi

# Check if Playwright is installed
if ! npx playwright --version &> /dev/null; then
    echo -e "${YELLOW}Playwright not found. Installing...${NC}"
    npm install -D @playwright/test
    npx playwright install chromium
fi

# Check if services are running
echo -e "${YELLOW}Checking if services are running...${NC}"
if ! curl -s "${BASE_URL}" > /dev/null; then
    echo -e "${RED}Warning: Cannot reach ${BASE_URL}${NC}"
    echo -e "${YELLOW}Make sure the frontend is running!${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build test command
TEST_CMD="npx playwright test tests/e2e/test_ai_chat_intensive.spec.ts"

# Add grep filter based on mode
case $MODE in
    asset)
        TEST_CMD="$TEST_CMD -g \"Asset Query\""
        echo -e "${GREEN}Running Asset Query tests...${NC}"
        ;;
    performance)
        TEST_CMD="$TEST_CMD -g \"Performance\""
        echo -e "${GREEN}Running Performance tests...${NC}"
        ;;
    multi-turn)
        TEST_CMD="$TEST_CMD -g \"Multi-turn\""
        echo -e "${GREEN}Running Multi-turn Conversation tests...${NC}"
        ;;
    error)
        TEST_CMD="$TEST_CMD -g \"Error Handling\""
        echo -e "${GREEN}Running Error Handling tests...${NC}"
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        ;;
    *)
        echo -e "${RED}Invalid mode: $MODE${NC}"
        usage
        exit 1
        ;;
esac

# Add flags
if [ "$HEADED" = true ]; then
    TEST_CMD="$TEST_CMD --headed"
    echo -e "${BLUE}Running with visible browser${NC}"
fi

if [ "$DEBUG" = true ]; then
    TEST_CMD="$TEST_CMD --debug"
    echo -e "${BLUE}Running in debug mode${NC}"
fi

if [ "$UI" = true ]; then
    TEST_CMD="$TEST_CMD --ui"
    echo -e "${BLUE}Running in UI mode${NC}"
fi

# Export environment variables
export BASE_URL
export TEST_USERNAME
export TEST_PASSWORD

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Base URL: ${GREEN}${BASE_URL}${NC}"
echo -e "  Username: ${GREEN}${TEST_USERNAME}${NC}"
echo -e "  Mode: ${GREEN}${MODE}${NC}"
echo ""

# Run tests
echo -e "${YELLOW}Starting tests...${NC}"
echo ""

eval $TEST_CMD
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
fi

# Show report location
echo ""
echo -e "${BLUE}Test artifacts:${NC}"
echo -e "  Screenshots: ${GREEN}tests/e2e/screenshots/ai-chat-intensive/${NC}"
echo -e "  Reports: ${GREEN}tests/e2e/reports/${NC}"
echo -e "  HTML Report: ${GREEN}npx playwright show-report tests/e2e/reports/html${NC}"
echo ""

# Offer to open HTML report
if [ $TEST_EXIT_CODE -eq 0 ] && [ "$UI" = false ] && [ "$DEBUG" = false ]; then
    read -p "Open HTML report? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npx playwright show-report tests/e2e/reports/html
    fi
fi

exit $TEST_EXIT_CODE