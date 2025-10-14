#!/bin/bash
# Verification script for PR #5 monitoring infrastructure
# Usage: ./monitoring/verify-monitoring.sh

set -e

echo "🔍 OpsConductor NG - Monitoring Verification"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
METRICS_URL="${AUTOMATION_SERVICE_URL:-http://localhost:8010}/metrics"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"

# Required metrics
REQUIRED_METRICS=(
    "ai_requests_total"
    "ai_request_duration_seconds"
    "ai_request_errors_total"
    "selector_requests_total"
    "selector_request_duration_seconds"
    "selector_build_info"
)

# Test counter
PASSED=0
FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Test 1: Metrics endpoint reachable
echo "1. Testing metrics endpoint..."
if curl -fsS "$METRICS_URL" > /dev/null 2>&1; then
    pass "Metrics endpoint reachable at $METRICS_URL"
else
    fail "Metrics endpoint unreachable at $METRICS_URL"
fi
echo ""

# Test 2: Required metrics present
echo "2. Checking required metrics..."
METRICS_OUTPUT=$(curl -fsS "$METRICS_URL" 2>/dev/null || echo "")
if [ -z "$METRICS_OUTPUT" ]; then
    fail "Could not fetch metrics"
else
    for metric in "${REQUIRED_METRICS[@]}"; do
        if echo "$METRICS_OUTPUT" | grep -q "^# HELP $metric"; then
            pass "Metric present: $metric"
        else
            fail "Metric missing: $metric"
        fi
    done
fi
echo ""

# Test 3: HELP and TYPE annotations
echo "3. Checking metric annotations..."
for metric in "${REQUIRED_METRICS[@]}"; do
    if echo "$METRICS_OUTPUT" | grep -q "^# HELP $metric"; then
        if echo "$METRICS_OUTPUT" | grep -q "^# TYPE $metric"; then
            pass "Annotations present: $metric"
        else
            fail "TYPE annotation missing: $metric"
        fi
    fi
done
echo ""

# Test 4: Histogram structure
echo "4. Checking histogram metrics..."
HISTOGRAM_METRICS=("ai_request_duration_seconds" "selector_request_duration_seconds")
for metric in "${HISTOGRAM_METRICS[@]}"; do
    if echo "$METRICS_OUTPUT" | grep -q "${metric}_bucket"; then
        if echo "$METRICS_OUTPUT" | grep -q "${metric}_sum"; then
            if echo "$METRICS_OUTPUT" | grep -q "${metric}_count"; then
                pass "Histogram complete: $metric"
            else
                fail "Histogram missing _count: $metric"
            fi
        else
            fail "Histogram missing _sum: $metric"
        fi
    else
        fail "Histogram missing _bucket: $metric"
    fi
done
echo ""

# Test 5: Prometheus (if running)
echo "5. Checking Prometheus..."
if curl -fsS "$PROMETHEUS_URL/-/healthy" > /dev/null 2>&1; then
    pass "Prometheus healthy at $PROMETHEUS_URL"
    
    # Check targets
    if curl -fsS "$PROMETHEUS_URL/api/v1/targets" | grep -q "automation-service"; then
        pass "Prometheus scraping automation-service"
    else
        warn "Prometheus not scraping automation-service (may not be configured)"
    fi
    
    # Check rules
    if curl -fsS "$PROMETHEUS_URL/api/v1/rules" | grep -q "AIExecutionErrorRateHigh"; then
        pass "Alert rules loaded"
    else
        warn "Alert rules not loaded (check configuration)"
    fi
else
    warn "Prometheus not running at $PROMETHEUS_URL (optional for dev)"
fi
echo ""

# Test 6: Grafana (if running)
echo "6. Checking Grafana..."
if curl -fsS "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
    pass "Grafana healthy at $GRAFANA_URL"
else
    warn "Grafana not running at $GRAFANA_URL (optional for dev)"
fi
echo ""

# Test 7: Run pytest tests
echo "7. Running CI tests..."
if command -v pytest &> /dev/null; then
    if pytest tests/monitoring/test_metrics_presence.py -q --tb=no 2>&1 | grep -q "passed"; then
        pass "CI tests passed"
    else
        fail "CI tests failed"
    fi
else
    warn "pytest not available (skipping CI tests)"
fi
echo ""

# Summary
echo "=============================================="
echo "Summary:"
echo -e "  ${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "  ${RED}Failed: $FAILED${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start monitoring: docker compose -f docker-compose.yml -f monitoring/compose.monitoring.yml -f monitoring/compose.grafana.yml up -d"
    echo "  2. View Prometheus: $PROMETHEUS_URL"
    echo "  3. View Grafana: $GRAFANA_URL (admin/opsconductor)"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure automation-service is running: docker ps | grep automation"
    echo "  2. Check service logs: docker logs opsconductor-automation-service"
    echo "  3. Verify metrics endpoint: curl $METRICS_URL"
    exit 1
fi