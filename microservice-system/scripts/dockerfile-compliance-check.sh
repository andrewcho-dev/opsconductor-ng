#!/bin/bash

# Dockerfile Compliance Checker
# Enforces architectural standards across all services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Compliance tracking
TOTAL_SERVICES=0
COMPLIANT_SERVICES=0
VIOLATIONS=()

echo -e "${BLUE}=== DOCKERFILE COMPLIANCE CHECKER ===${NC}"
echo "Checking all services against architectural standards..."
echo

# Function to check individual Dockerfile
check_dockerfile() {
    local service_dir="$1"
    local service_name="$(basename "$service_dir")"
    local dockerfile="$service_dir/Dockerfile"
    
    # Skip non-service directories
    if [[ "$service_name" == "scripts" || "$service_name" == "database" || "$service_name" == "nginx" || "$service_name" == "frontend" || "$service_name" == "service-template" ]]; then
        return 0
    fi
    
    if [[ ! -f "$dockerfile" ]]; then
        echo -e "${RED}❌ $service_name: No Dockerfile found${NC}"
        VIOLATIONS+=("$service_name: Missing Dockerfile")
        return 1
    fi
    
    TOTAL_SERVICES=$((TOTAL_SERVICES + 1))
    local violations_found=0
    local service_violations=()
    
    echo -e "${BLUE}Checking $service_name...${NC}"
    
    # Check 1: Base image
    if ! grep -q "FROM python:3.11-slim" "$dockerfile"; then
        service_violations+=("Wrong base image (must be python:3.11-slim)")
        violations_found=1
    fi
    
    # Check 2: Required dependencies (gcc, curl)
    if ! grep -q "gcc" "$dockerfile"; then
        service_violations+=("Missing gcc dependency")
        violations_found=1
    fi
    
    if ! grep -q "curl" "$dockerfile"; then
        service_violations+=("Missing curl dependency")
        violations_found=1
    fi
    
    # Check 3: Non-root user setup
    if ! grep -q "addgroup --gid 1001 --system python" "$dockerfile"; then
        service_violations+=("Missing standard group creation")
        violations_found=1
    fi
    
    if ! grep -q "adduser --system --uid 1001 --gid 1001 python" "$dockerfile"; then
        service_violations+=("Missing standard user creation")
        violations_found=1
    fi
    
    if ! grep -q "USER python" "$dockerfile"; then
        service_violations+=("Not running as non-root user")
        violations_found=1
    fi
    
    # Check 4: Health check
    if ! grep -q "HEALTHCHECK" "$dockerfile"; then
        service_violations+=("Missing health check")
        violations_found=1
    fi
    
    if ! grep -q "curl -f http://localhost:" "$dockerfile"; then
        service_violations+=("Health check not using curl standard")
        violations_found=1
    fi
    
    # Check 5: Ownership change
    if ! grep -q "chown -R python:python /app" "$dockerfile"; then
        service_violations+=("Missing ownership change to python user")
        violations_found=1
    fi
    
    # Report results for this service
    if [[ $violations_found -eq 0 ]]; then
        echo -e "${GREEN}✅ $service_name: COMPLIANT${NC}"
        COMPLIANT_SERVICES=$((COMPLIANT_SERVICES + 1))
    else
        echo -e "${RED}❌ $service_name: NON-COMPLIANT${NC}"
        for violation in "${service_violations[@]}"; do
            echo -e "${RED}   - $violation${NC}"
            VIOLATIONS+=("$service_name: $violation")
        done
    fi
    echo
}

# Check all service directories
for service_dir in "$PROJECT_ROOT"/*-service; do
    if [[ -d "$service_dir" ]]; then
        check_dockerfile "$service_dir"
    fi
done

# Final report
echo -e "${BLUE}=== COMPLIANCE REPORT ===${NC}"
echo -e "Total Services Checked: $TOTAL_SERVICES"
echo -e "Compliant Services: ${GREEN}$COMPLIANT_SERVICES${NC}"
echo -e "Non-Compliant Services: ${RED}$((TOTAL_SERVICES - COMPLIANT_SERVICES))${NC}"

if [[ $COMPLIANT_SERVICES -eq $TOTAL_SERVICES ]]; then
    echo -e "${GREEN}🎉 ALL SERVICES ARE COMPLIANT!${NC}"
    exit 0
else
    echo -e "${RED}❌ COMPLIANCE FAILURES DETECTED${NC}"
    echo
    echo -e "${YELLOW}All violations:${NC}"
    for violation in "${VIOLATIONS[@]}"; do
        echo -e "${RED}  - $violation${NC}"
    done
    echo
    echo -e "${YELLOW}Action Required: Fix all violations before deployment${NC}"
    exit 1
fi