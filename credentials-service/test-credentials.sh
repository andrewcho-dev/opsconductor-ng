#!/bin/bash

# Test script for credentials service
# This script tests the basic functionality of the credentials service

set -e

echo "🔐 Testing Credentials Service..."

# Service URL
SERVICE_URL="http://localhost:3004"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Test 1: Health check
print_info "Testing health check..."
response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$SERVICE_URL/health")
if [ "$response" = "200" ]; then
    print_status 0 "Health check passed"
    cat /tmp/health_response.json | jq '.'
else
    print_status 1 "Health check failed (HTTP $response)"
fi

echo ""

# Test 2: Service info
print_info "Testing service info..."
response=$(curl -s -w "%{http_code}" -o /tmp/info_response.json "$SERVICE_URL/info")
if [ "$response" = "200" ]; then
    print_status 0 "Service info retrieved"
    cat /tmp/info_response.json | jq '.'
else
    print_status 1 "Service info failed (HTTP $response)"
fi

echo ""

# Test 3: Authentication required endpoints (should fail without token)
print_info "Testing authentication requirement..."
response=$(curl -s -w "%{http_code}" -o /tmp/auth_test.json "$SERVICE_URL/credentials")
if [ "$response" = "401" ]; then
    print_status 0 "Authentication properly required"
else
    print_status 1 "Authentication check failed (expected 401, got $response)"
fi

echo ""

# Note: Further tests would require a valid JWT token from the auth service
print_info "Note: Full CRUD tests require authentication with admin role"
print_info "To test with authentication:"
print_info "1. Start the auth service"
print_info "2. Login to get a JWT token"
print_info "3. Use the token in Authorization header for credential operations"

echo ""
echo -e "${GREEN}🎉 Basic credentials service tests completed successfully!${NC}"

# Cleanup
rm -f /tmp/health_response.json /tmp/info_response.json /tmp/auth_test.json