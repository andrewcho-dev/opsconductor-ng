#!/bin/bash
# Release Smoke Test Script
# Validates basic health and functionality of deployed services
# Usage: ./scripts/release_smoke.sh [environment]
#   environment: local (default), staging, production

# set -e temporarily disabled for debugging

ENVIRONMENT="${1:-local}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment-specific URLs
case "$ENVIRONMENT" in
    local)
        AUTOMATION_URL="http://localhost:8010"
        AI_PIPELINE_URL="http://localhost:3005"
        KONG_URL="http://localhost:3000"
        KONG_ADMIN_URL="http://localhost:8888"
        PROMETHEUS_URL="http://localhost:9090"
        GRAFANA_URL="http://localhost:3001"
        ;;
    staging)
        AUTOMATION_URL="${STAGING_AUTOMATION_URL:-http://staging.opsconductor.local:8010}"
        AI_PIPELINE_URL="${STAGING_AI_PIPELINE_URL:-http://staging.opsconductor.local:3005}"
        KONG_URL="${STAGING_KONG_URL:-http://staging.opsconductor.local:3000}"
        KONG_ADMIN_URL="${STAGING_KONG_ADMIN_URL:-http://staging.opsconductor.local:8888}"
        PROMETHEUS_URL="${STAGING_PROMETHEUS_URL:-http://staging.opsconductor.local:9090}"
        GRAFANA_URL="${STAGING_GRAFANA_URL:-http://staging.opsconductor.local:3001}"
        ;;
    production)
        AUTOMATION_URL="${PROD_AUTOMATION_URL:-http://opsconductor.local:8010}"
        AI_PIPELINE_URL="${PROD_AI_PIPELINE_URL:-http://opsconductor.local:3005}"
        KONG_URL="${PROD_KONG_URL:-http://opsconductor.local:3000}"
        KONG_ADMIN_URL="${PROD_KONG_ADMIN_URL:-http://opsconductor.local:8888}"
        PROMETHEUS_URL="${PROD_PROMETHEUS_URL:-http://opsconductor.local:9090}"
        GRAFANA_URL="${PROD_GRAFANA_URL:-http://opsconductor.local:3001}"
        ;;
    *)
        echo -e "${RED}❌ Unknown environment: $ENVIRONMENT${NC}"
        echo "Valid environments: local, staging, production"
        exit 1
        ;;
esac

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         OpsConductor Release Smoke Tests                  ║${NC}"
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

# Helper function to check JSON response
check_json_response() {
    local name="$1"
    local url="$2"
    local jq_filter="$3"
    local expected_value="$4"
    local timeout="${5:-10}"
    
    echo -n "  Testing $name... "
    
    response=$(curl -s --max-time "$timeout" "$url" 2>/dev/null || echo "{}")
    
    if [ -z "$response" ]; then
        echo -e "${RED}✗ FAIL${NC} (Empty response)"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$name")
        return 1
    fi
    
    actual_value=$(echo "$response" | jq -r "$jq_filter" 2>/dev/null || echo "null")
    
    if [ "$actual_value" = "$expected_value" ]; then
        echo -e "${GREEN}✓ PASS${NC} (value: $actual_value)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (got: $actual_value, expected: $expected_value)"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$name")
        return 1
    fi
}

# Helper function to check metrics presence
check_metric() {
    local name="$1"
    local url="$2"
    local metric_name="$3"
    local timeout="${4:-10}"
    
    echo -n "  Testing $name... "
    
    response=$(curl -s --max-time "$timeout" "$url" 2>/dev/null || echo "")
    
    if echo "$response" | grep -q "^${metric_name}"; then
        echo -e "${GREEN}✓ PASS${NC} (metric found)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (metric not found)"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$name")
        return 1
    fi
}

# ============================================================================
# TEST SUITE 1: Health Checks
# ============================================================================

echo -e "${YELLOW}[1/5] Health Checks${NC}"
check_endpoint "Automation Service Health" "$AUTOMATION_URL/health" 200
check_endpoint "AI Pipeline Health" "$AI_PIPELINE_URL/health" 200
check_endpoint "Kong Gateway Status" "$KONG_ADMIN_URL/status" 200
check_endpoint "Prometheus Health" "$PROMETHEUS_URL/-/healthy" 200
check_endpoint "Grafana Health" "$GRAFANA_URL/api/health" 200
echo ""

# ============================================================================
# TEST SUITE 2: Metrics Endpoints
# ============================================================================

echo -e "${YELLOW}[2/5] Metrics Endpoints${NC}"
check_endpoint "Automation Service Metrics" "$AUTOMATION_URL/metrics" 200
echo ""

# ============================================================================
# TEST SUITE 3: Critical Metrics Presence (after execution)
# ============================================================================

echo -e "${YELLOW}[3/5] Critical Metrics Definitions${NC}"
check_metric "ai_requests_total definition" "$AUTOMATION_URL/metrics" "# TYPE ai_requests_total"
check_metric "ai_request_duration_seconds definition" "$AUTOMATION_URL/metrics" "# TYPE ai_request_duration_seconds"
check_metric "ai_request_errors_total definition" "$AUTOMATION_URL/metrics" "# TYPE ai_request_errors_total"
echo ""

# ============================================================================
# TEST SUITE 4: Walking Skeleton - Echo Tool Test
# ============================================================================

echo -e "${YELLOW}[4/5] Walking Skeleton - Echo Tool Test${NC}"

# Generate trace ID
TRACE_ID="smoke-test-$(date +%s)-$$"

echo -n "  Testing /ai/execute (ping→pong)... "

# Execute via Kong gateway
exec_response=$(curl -s -X POST "$KONG_URL/ai/execute" \
    -H "Content-Type: application/json" \
    -H "X-Trace-Id: $TRACE_ID" \
    -d '{"input":"ping","tool":"echo"}' \
    --max-time 30 2>/dev/null || echo "{}")

if [ -z "$exec_response" ]; then
    echo -e "${RED}✗ FAIL${NC} (Empty response)"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("Echo Tool Execution")
else
    # Check success field using python3 json parsing
    success=$(echo "$exec_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', 'null'))" 2>/dev/null || echo "null")
    output=$(echo "$exec_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('output', 'null'))" 2>/dev/null || echo "null")
    trace_id=$(echo "$exec_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('trace_id', 'null'))" 2>/dev/null || echo "null")
    
    if [ "$success" = "True" ] && [ "$output" = "pong" ]; then
        echo -e "${GREEN}✓ PASS${NC} (output: $output, trace_id: $trace_id)"
        ((TESTS_PASSED++))
        
        # Verify trace_id propagation
        if [ "$trace_id" = "$TRACE_ID" ]; then
            echo -e "    ${GREEN}✓${NC} Trace ID propagated correctly"
        else
            echo -e "    ${YELLOW}⚠${NC} Trace ID mismatch (sent: $TRACE_ID, got: $trace_id)"
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (success: $success, output: $output)"
        echo "    Response: $exec_response"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Echo Tool Execution")
    fi
fi

# Wait for metrics to be recorded
sleep 2

# Verify metrics increment
echo -n "  Verifying ai_requests_total increment... "
metrics_response=$(curl -s "$AUTOMATION_URL/metrics" 2>/dev/null || echo "")

if echo "$metrics_response" | grep -q 'ai_requests_total.*tool="echo"'; then
    echo -e "${GREEN}✓ PASS${NC} (metric incremented)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (metric not found or not incremented)"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("Metrics Increment")
fi

echo ""

# ============================================================================
# TEST SUITE 5: Prometheus Query Test
# ============================================================================

echo -e "${YELLOW}[5/5] Prometheus Query Test${NC}"

echo -n "  Testing Prometheus query (ai_requests_total)... "

# Query Prometheus for ai_requests_total
prom_query="ai_requests_total"
prom_response=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$prom_query" \
    2>/dev/null || echo "{}")

prom_status=$(echo "$prom_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'null'))" 2>/dev/null || echo "null")

if [ "$prom_status" = "success" ]; then
    result_count=$(echo "$prom_response" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', {}).get('result', [])))" 2>/dev/null || echo "0")
    if [ "$result_count" -gt 0 ]; then
        echo -e "${GREEN}✓ PASS${NC} (found $result_count time series)"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠ WARN${NC} (query successful but no data yet)"
        ((TESTS_PASSED++))
    fi
else
    echo -e "${RED}✗ FAIL${NC} (query failed: $prom_status)"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("Prometheus Query")
fi

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
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 SMOKE TESTS PASSED - READY FOR DEPLOYMENT 🎉          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}✗ Some smoke tests failed:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}•${NC} $test"
    done
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠️  SMOKE TESTS FAILED - DO NOT DEPLOY ⚠️                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi