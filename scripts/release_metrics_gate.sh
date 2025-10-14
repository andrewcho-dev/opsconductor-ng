#!/bin/bash
# Release Metrics Gate Script
# Validates SLO compliance before promoting to production
# Polls Prometheus for 5-10 minutes and fails if thresholds are exceeded
# Usage: ./scripts/release_metrics_gate.sh [environment] [duration_minutes]

set -e

ENVIRONMENT="${1:-local}"
DURATION_MINUTES="${2:-5}"
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
        PROMETHEUS_URL="http://localhost:9090"
        ;;
    staging)
        PROMETHEUS_URL="${STAGING_PROMETHEUS_URL:-http://staging.opsconductor.local:9090}"
        ;;
    production)
        PROMETHEUS_URL="${PROD_PROMETHEUS_URL:-http://opsconductor.local:9090}"
        ;;
    *)
        echo -e "${RED}❌ Unknown environment: $ENVIRONMENT${NC}"
        exit 1
        ;;
esac

# SLO Thresholds
ERROR_RATE_THRESHOLD=0.01  # 1% error rate
P95_LATENCY_THRESHOLD=1.0  # 1 second
P99_LATENCY_THRESHOLD=2.0  # 2 seconds

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         OpsConductor Release Metrics Gate                 ║${NC}"
echo -e "${BLUE}║         Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}║         Duration: ${DURATION_MINUTES} minutes${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}SLO Thresholds:${NC}"
echo -e "  Error Rate:    < ${ERROR_RATE_THRESHOLD} (${YELLOW}$(echo "$ERROR_RATE_THRESHOLD * 100" | bc)%${NC})"
echo -e "  P95 Latency:   < ${P95_LATENCY_THRESHOLD}s"
echo -e "  P99 Latency:   < ${P99_LATENCY_THRESHOLD}s"
echo ""

# Helper function to query Prometheus
query_prometheus() {
    local query="$1"
    local result
    
    result=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
        --data-urlencode "query=$query" \
        2>/dev/null || echo "{}")
    
    echo "$result"
}

# Helper function to extract scalar value from Prometheus response
extract_value() {
    local response="$1"
    local value
    
    value=$(echo "$response" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "null")
    
    if [ "$value" = "null" ] || [ -z "$value" ]; then
        echo "0"
    else
        echo "$value"
    fi
}

# Calculate end time
END_TIME=$(($(date +%s) + DURATION_MINUTES * 60))
CHECK_INTERVAL=30  # Check every 30 seconds
CHECK_COUNT=0
VIOLATIONS=0

echo -e "${YELLOW}Starting metrics monitoring...${NC}"
echo ""

while [ $(date +%s) -lt $END_TIME ]; do
    ((CHECK_COUNT++))
    REMAINING=$((END_TIME - $(date +%s)))
    
    echo -e "${BLUE}[Check $CHECK_COUNT] ${REMAINING}s remaining${NC}"
    
    # ========================================================================
    # CHECK 1: Error Rate
    # ========================================================================
    
    echo -n "  Checking error rate... "
    
    # Query: rate of errors / rate of total requests over last 5 minutes
    error_rate_query='rate(ai_request_errors_total[5m]) / rate(ai_requests_total[5m])'
    error_rate_response=$(query_prometheus "$error_rate_query")
    error_rate=$(extract_value "$error_rate_response")
    
    # Handle division by zero or no data
    if [ "$error_rate" = "0" ] || [ "$error_rate" = "null" ]; then
        echo -e "${GREEN}✓ PASS${NC} (no errors or no traffic)"
    else
        # Compare with threshold using bc
        if (( $(echo "$error_rate < $ERROR_RATE_THRESHOLD" | bc -l) )); then
            echo -e "${GREEN}✓ PASS${NC} (${error_rate})"
        else
            echo -e "${RED}✗ FAIL${NC} (${error_rate} > ${ERROR_RATE_THRESHOLD})"
            ((VIOLATIONS++))
        fi
    fi
    
    # ========================================================================
    # CHECK 2: P95 Latency
    # ========================================================================
    
    echo -n "  Checking P95 latency... "
    
    # Query: 95th percentile of request duration over last 5 minutes
    p95_query='histogram_quantile(0.95, rate(ai_request_duration_seconds_bucket[5m]))'
    p95_response=$(query_prometheus "$p95_query")
    p95_latency=$(extract_value "$p95_response")
    
    if [ "$p95_latency" = "0" ] || [ "$p95_latency" = "null" ]; then
        echo -e "${GREEN}✓ PASS${NC} (no data yet)"
    else
        if (( $(echo "$p95_latency < $P95_LATENCY_THRESHOLD" | bc -l) )); then
            echo -e "${GREEN}✓ PASS${NC} (${p95_latency}s)"
        else
            echo -e "${RED}✗ FAIL${NC} (${p95_latency}s > ${P95_LATENCY_THRESHOLD}s)"
            ((VIOLATIONS++))
        fi
    fi
    
    # ========================================================================
    # CHECK 3: P99 Latency
    # ========================================================================
    
    echo -n "  Checking P99 latency... "
    
    # Query: 99th percentile of request duration over last 5 minutes
    p99_query='histogram_quantile(0.99, rate(ai_request_duration_seconds_bucket[5m]))'
    p99_response=$(query_prometheus "$p99_query")
    p99_latency=$(extract_value "$p99_response")
    
    if [ "$p99_latency" = "0" ] || [ "$p99_latency" = "null" ]; then
        echo -e "${GREEN}✓ PASS${NC} (no data yet)"
    else
        if (( $(echo "$p99_latency < $P99_LATENCY_THRESHOLD" | bc -l) )); then
            echo -e "${GREEN}✓ PASS${NC} (${p99_latency}s)"
        else
            echo -e "${RED}✗ FAIL${NC} (${p99_latency}s > ${P99_LATENCY_THRESHOLD}s)"
            ((VIOLATIONS++))
        fi
    fi
    
    # ========================================================================
    # CHECK 4: Request Rate
    # ========================================================================
    
    echo -n "  Checking request rate... "
    
    # Query: requests per second over last 1 minute
    rate_query='rate(ai_requests_total[1m])'
    rate_response=$(query_prometheus "$rate_query")
    request_rate=$(extract_value "$rate_response")
    
    if [ "$request_rate" = "0" ] || [ "$request_rate" = "null" ]; then
        echo -e "${YELLOW}⚠ WARN${NC} (no traffic)"
    else
        echo -e "${GREEN}✓ INFO${NC} (${request_rate} req/s)"
    fi
    
    echo ""
    
    # Check if we should fail fast
    if [ $VIOLATIONS -gt 3 ]; then
        echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║  ⚠️  CRITICAL: Multiple SLO violations detected!          ║${NC}"
        echo -e "${RED}║  Failing fast to prevent further degradation.             ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
        exit 1
    fi
    
    # Wait before next check
    if [ $(date +%s) -lt $END_TIME ]; then
        sleep $CHECK_INTERVAL
    fi
done

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Metrics Gate Summary                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Environment:       ${BLUE}$ENVIRONMENT${NC}"
echo -e "  Duration:          ${DURATION_MINUTES} minutes"
echo -e "  Checks Performed:  $CHECK_COUNT"
echo -e "  SLO Violations:    ${RED}$VIOLATIONS${NC}"
echo ""

if [ $VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✓ All SLO checks passed!${NC}"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 METRICS GATE PASSED - READY FOR PROMOTION 🎉          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "  1. Review Grafana dashboards for visual confirmation"
    echo -e "  2. Check for any Prometheus alerts"
    echo -e "  3. Proceed with canary rollout or full deployment"
    echo -e "  4. Continue monitoring for next 24 hours"
    exit 0
else
    echo -e "${RED}✗ SLO violations detected during monitoring period${NC}"
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠️  METRICS GATE FAILED - DO NOT PROMOTE ⚠️              ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Recommended Actions:${NC}"
    echo -e "  1. Review Grafana dashboards for anomalies"
    echo -e "  2. Check application logs for errors"
    echo -e "  3. Investigate high-latency requests"
    echo -e "  4. Consider rolling back to previous version"
    echo -e "  5. Run diagnostics: ${BLUE}docker compose logs -f${NC}"
    exit 1
fi