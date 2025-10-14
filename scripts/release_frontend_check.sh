#!/bin/bash
# Release Frontend Check Script
# Validates frontend is accessible and Exec Sandbox is functional
# Usage: ./scripts/release_frontend_check.sh [environment]

set -e

ENVIRONMENT="${1:-local}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment-specific URLs
case "$ENVIRONMENT" in
    local)
        FRONTEND_URL="http://localhost:3100"
        ;;
    staging)
        FRONTEND_URL="${STAGING_FRONTEND_URL:-http://staging.opsconductor.local:3100}"
        ;;
    production)
        FRONTEND_URL="${PROD_FRONTEND_URL:-http://opsconductor.local:3100}"
        ;;
    *)
        echo -e "${RED}❌ Unknown environment: $ENVIRONMENT${NC}"
        exit 1
        ;;
esac

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         OpsConductor Frontend Health Check                ║${NC}"
echo -e "${BLUE}║         Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Helper function to check HTTP endpoint
check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local timeout="${4:-10}"
    
    echo -n "  Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected_status)"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$name")
        return 1
    fi
}

# Helper function to check HTML content
check_html_content() {
    local name="$1"
    local url="$2"
    local search_string="$3"
    local timeout="${4:-10}"
    
    echo -n "  Testing $name... "
    
    response=$(curl -s --max-time "$timeout" "$url" 2>/dev/null || echo "")
    
    if [ -z "$response" ]; then
        echo -e "${RED}✗ FAIL${NC} (Empty response)"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$name")
        return 1
    fi
    
    if echo "$response" | grep -q "$search_string"; then
        echo -e "${GREEN}✓ PASS${NC} (content found)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (content not found)"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$name")
        return 1
    fi
}

# ============================================================================
# TEST SUITE 1: Basic Frontend Accessibility
# ============================================================================

echo -e "${YELLOW}[1/3] Basic Frontend Accessibility${NC}"
check_endpoint "Frontend Root" "$FRONTEND_URL/" 200
check_endpoint "Frontend Static Assets" "$FRONTEND_URL/static/js/bundle.js" 200 15
echo ""

# ============================================================================
# TEST SUITE 2: HTML Content Validation
# ============================================================================

echo -e "${YELLOW}[2/3] HTML Content Validation${NC}"
check_html_content "React Root Element" "$FRONTEND_URL/" "root"
check_html_content "OpsConductor Title" "$FRONTEND_URL/" "OpsConductor"
echo ""

# ============================================================================
# TEST SUITE 3: Exec Sandbox Component (Basic DOM Check)
# ============================================================================

echo -e "${YELLOW}[3/3] Exec Sandbox Component Check${NC}"

echo -n "  Testing Exec Sandbox page load... "

# Try to fetch the main page and check for React app initialization
response=$(curl -s --max-time 10 "$FRONTEND_URL/" 2>/dev/null || echo "")

if [ -z "$response" ]; then
    echo -e "${RED}✗ FAIL${NC} (Empty response)"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("Exec Sandbox Page Load")
else
    # Check for React app div
    if echo "$response" | grep -q 'id="root"'; then
        echo -e "${GREEN}✓ PASS${NC} (React app container found)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (React app container not found)"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Exec Sandbox Page Load")
    fi
fi

echo ""
echo -e "${BLUE}Note:${NC} Full Exec Sandbox functionality testing requires browser automation."
echo -e "      For comprehensive E2E tests, run: ${BLUE}npm test${NC} in the frontend directory."
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Test Summary                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Environment:     ${BLUE}$ENVIRONMENT${NC}"
echo -e "  Tests Passed:    ${GREEN}$TESTS_PASSED${NC}"
echo -e "  Tests Failed:    ${RED}$TESTS_FAILED${NC}"
echo -e "  Total Tests:     $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All frontend checks passed!${NC}"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 FRONTEND CHECKS PASSED - READY FOR USE 🎉             ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Access the frontend at:${NC} ${BLUE}$FRONTEND_URL${NC}"
    exit 0
else
    echo -e "${RED}✗ Some frontend checks failed:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}•${NC} $test"
    done
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠️  FRONTEND CHECKS FAILED - INVESTIGATE ⚠️               ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. Check frontend container: ${BLUE}docker logs opsconductor-frontend${NC}"
    echo -e "  2. Verify frontend is running: ${BLUE}docker ps | grep frontend${NC}"
    echo -e "  3. Check build errors: ${BLUE}docker compose logs frontend${NC}"
    exit 1
fi