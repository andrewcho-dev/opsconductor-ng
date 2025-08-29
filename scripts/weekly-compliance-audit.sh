#!/bin/bash

# Weekly Compliance Audit
# Automated architectural standards verification

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_LOG="/tmp/compliance-audit-$(date +%Y%m%d-%H%M%S).log"

echo "📅 WEEKLY COMPLIANCE AUDIT - $(date)" | tee "$AUDIT_LOG"
echo "====================================" | tee -a "$AUDIT_LOG"
echo | tee -a "$AUDIT_LOG"

# 1. Dockerfile Compliance Check
echo "🔍 DOCKERFILE COMPLIANCE CHECK" | tee -a "$AUDIT_LOG"
echo "------------------------------" | tee -a "$AUDIT_LOG"
if "$SCRIPT_DIR/dockerfile-compliance-check.sh" >> "$AUDIT_LOG" 2>&1; then
    echo "✅ Dockerfile compliance: PASSED" | tee -a "$AUDIT_LOG"
    dockerfile_status="PASSED"
else
    echo "❌ Dockerfile compliance: FAILED" | tee -a "$AUDIT_LOG"
    dockerfile_status="FAILED"
fi
echo | tee -a "$AUDIT_LOG"

# 2. System Health Check
echo "🏥 SYSTEM HEALTH CHECK" | tee -a "$AUDIT_LOG"
echo "---------------------" | tee -a "$AUDIT_LOG"
if "$SCRIPT_DIR/system-health-check.sh" >> "$AUDIT_LOG" 2>&1; then
    echo "✅ System health: PASSED" | tee -a "$AUDIT_LOG"
    health_status="PASSED"
else
    echo "❌ System health: FAILED" | tee -a "$AUDIT_LOG"
    health_status="FAILED"
fi
echo | tee -a "$AUDIT_LOG"

# 3. Security Audit (Non-root user check)
echo "🔒 SECURITY AUDIT" | tee -a "$AUDIT_LOG"
echo "----------------" | tee -a "$AUDIT_LOG"
security_violations=0

for container in $(docker ps --format "{{.Names}}" | grep opsconductor | grep -v postgres | grep -v nginx | grep -v frontend); do
    if docker exec "$container" whoami 2>/dev/null | grep -q "root"; then
        echo "❌ $container: Running as root (SECURITY VIOLATION)" | tee -a "$AUDIT_LOG"
        security_violations=$((security_violations + 1))
    else
        echo "✅ $container: Running as non-root user" | tee -a "$AUDIT_LOG"
    fi
done

if [[ $security_violations -eq 0 ]]; then
    echo "✅ Security audit: PASSED" | tee -a "$AUDIT_LOG"
    security_status="PASSED"
else
    echo "❌ Security audit: FAILED ($security_violations violations)" | tee -a "$AUDIT_LOG"
    security_status="FAILED"
fi
echo | tee -a "$AUDIT_LOG"

# 4. Final Report
echo "📊 AUDIT SUMMARY" | tee -a "$AUDIT_LOG"
echo "===============" | tee -a "$AUDIT_LOG"
echo "Dockerfile Compliance: $dockerfile_status" | tee -a "$AUDIT_LOG"
echo "System Health: $health_status" | tee -a "$AUDIT_LOG"
echo "Security Audit: $security_status" | tee -a "$AUDIT_LOG"
echo | tee -a "$AUDIT_LOG"

if [[ "$dockerfile_status" == "PASSED" && "$health_status" == "PASSED" && "$security_status" == "PASSED" ]]; then
    echo "🎉 OVERALL AUDIT STATUS: PASSED" | tee -a "$AUDIT_LOG"
    echo "System is compliant with all architectural standards" | tee -a "$AUDIT_LOG"
    exit_code=0
else
    echo "❌ OVERALL AUDIT STATUS: FAILED" | tee -a "$AUDIT_LOG"
    echo "Immediate action required to fix violations" | tee -a "$AUDIT_LOG"
    exit_code=1
fi

echo | tee -a "$AUDIT_LOG"
echo "📄 Full audit log saved to: $AUDIT_LOG" | tee -a "$AUDIT_LOG"

exit $exit_code