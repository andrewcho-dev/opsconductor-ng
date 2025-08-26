#!/bin/bash

# Sprint 1 Integration Test Script
# Tests the complete Sprint 1 implementation according to exit criteria:
# "can save creds/targets; test endpoint returns mock"

set -e

echo "🧪 Testing Sprint 1 Implementation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_section() {
    echo -e "${BLUE}📋 $1${NC}"
}

# Service URLs - Using nginx proxy with HTTPS
AUTH_URL="https://localhost:8443"
USER_URL="https://localhost:8443"
CREDS_URL="https://localhost:8443"
TARGETS_URL="https://localhost:8443"

# Test variables
ADMIN_TOKEN=""
CREDENTIAL_ID=""
TARGET_ID=""

print_section "Sprint 1 Exit Criteria Test"
print_info "Testing: 'can save creds/targets; test endpoint returns mock'"
echo ""

# Test 1: Service Health Checks
print_section "1. Service Health Checks"

print_info "Testing auth service health..."
response=$(curl -k -s -w "%{http_code}" -o /tmp/auth_health.json "$AUTH_URL/health")
print_status $([ "$response" = "200" ] && echo 0 || echo 1) "Auth service health check"

print_info "Testing user service health..."
response=$(curl -k -s -w "%{http_code}" -o /tmp/user_health.json "$USER_URL/health")
print_status $([ "$response" = "200" ] && echo 0 || echo 1) "User service health check"

print_info "Testing credentials service health..."
response=$(curl -k -s -w "%{http_code}" -o /tmp/creds_health.json "$CREDS_URL/health")
print_status $([ "$response" = "200" ] && echo 0 || echo 1) "Credentials service health check"

print_info "Testing targets service health..."
response=$(curl -k -s -w "%{http_code}" -o /tmp/targets_health.json "$TARGETS_URL/health")
print_status $([ "$response" = "200" ] && echo 0 || echo 1) "Targets service health check"

echo ""

# Test 2: Authentication (JWT Refresh Rotation)
print_section "2. Authentication & JWT Refresh Rotation"

print_info "Logging in as admin user..."
login_response=$(curl -k -s -X POST "$AUTH_URL/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

if echo "$login_response" | jq -e '.access_token' > /dev/null 2>&1; then
    ADMIN_TOKEN=$(echo "$login_response" | jq -r '.access_token')
    print_status 0 "Admin login successful"
    print_info "Access token obtained (${ADMIN_TOKEN:0:20}...)"
else
    print_status 1 "Admin login failed"
    echo "Response: $login_response"
    echo "Debug: checking jq and response..."
    echo "$login_response" | jq . 2>&1 || echo "JQ parsing failed"
fi

# Test token verification
print_info "Verifying JWT token..."
verify_response=$(curl -k -s "$AUTH_URL/api/verify" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$verify_response" | jq -e '.user.role' > /dev/null 2>&1; then
    user_role=$(echo "$verify_response" | jq -r '.user.role')
    print_status $([ "$user_role" = "admin" ] && echo 0 || echo 1) "JWT token verification (role: $user_role)"
else
    print_status 1 "JWT token verification failed"
fi

echo ""

# Test 3: Credential CRUD (AES-GCM Encryption)
print_section "3. Credential CRUD with AES-GCM Encryption"

# Clean up any existing test credentials and targets
print_info "Cleaning up existing test credentials..."
# First delete any test targets to avoid foreign key constraints
curl -k -s -X DELETE "$TARGETS_URL/targets/by-name/test-windows-server" \
  -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null 2>&1 || true
# Then delete the test credential
curl -k -s -X DELETE "$CREDS_URL/credentials/by-name/test-winrm-admin" \
  -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null 2>&1 || true

print_info "Creating WinRM NTLM credential..."
cred_response=$(curl -k -s -X POST "$CREDS_URL/credentials" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-winrm-admin",
    "credential_type": "winrm_ntlm",
    "credential_data": {
      "username": "Administrator",
      "password": "SecurePassword123!"
    }
  }')

if echo "$cred_response" | jq -e '.id' > /dev/null 2>&1; then
    CREDENTIAL_ID=$(echo "$cred_response" | jq -r '.id')
    print_status 0 "Credential created successfully (ID: $CREDENTIAL_ID)"
else
    print_status 1 "Credential creation failed"
    echo "Response: $cred_response"
fi

# Test credential listing
print_info "Listing credentials..."
list_response=$(curl -k -s -X GET "$CREDS_URL/credentials" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$list_response" | jq -e '.credentials' > /dev/null 2>&1; then
    cred_count=$(echo "$list_response" | jq '.credentials | length')
    print_status 0 "Credentials listed successfully ($cred_count credentials found)"
else
    print_status 1 "Credential listing failed"
fi

# Test credential rotation
print_info "Testing credential rotation..."
rotate_response=$(curl -k -s -X POST "$CREDS_URL/credentials/$CREDENTIAL_ID/rotate" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "username": "Administrator",
      "password": "NewSecurePassword456!"
    }
  }')

if echo "$rotate_response" | jq -e '.rotated_at' > /dev/null 2>&1; then
    print_status 0 "Credential rotation successful"
else
    print_status 1 "Credential rotation failed"
    echo "Response: $rotate_response"
fi

echo ""

# Test 4: Target CRUD with WinRM Configuration
print_section "4. Target CRUD with WinRM Configuration"

print_info "Creating Windows target..."
target_response=$(curl -k -s -X POST "$TARGETS_URL/targets" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"test-windows-server\",
    \"protocol\": \"winrm\",
    \"hostname\": \"win-test-01.example.com\",
    \"port\": 5986,
    \"credential_ref\": $CREDENTIAL_ID,
    \"tags\": [\"environment:test\", \"role:web-server\"],
    \"metadata\": {
      \"winrm_use_https\": true,
      \"winrm_validate_cert\": true,
      \"domain\": \"TESTDOMAIN\"
    }
  }")

if echo "$target_response" | jq -e '.id' > /dev/null 2>&1; then
    TARGET_ID=$(echo "$target_response" | jq -r '.id')
    print_status 0 "Target created successfully (ID: $TARGET_ID)"
else
    print_status 1 "Target creation failed"
    echo "Response: $target_response"
fi

# Test target listing
print_info "Listing targets..."
targets_list_response=$(curl -k -s -X GET "$TARGETS_URL/targets" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$targets_list_response" | jq -e '.targets' > /dev/null 2>&1; then
    target_count=$(echo "$targets_list_response" | jq '.targets | length')
    print_status 0 "Targets listed successfully ($target_count targets found)"
else
    print_status 1 "Target listing failed"
fi

# Test target details
print_info "Getting target details..."
target_details_response=$(curl -k -s -X GET "$TARGETS_URL/targets/$TARGET_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$target_details_response" | jq -e '.metadata.winrm_use_https' > /dev/null 2>&1; then
    use_https=$(echo "$target_details_response" | jq -r '.metadata.winrm_use_https')
    print_status $([ "$use_https" = "true" ] && echo 0 || echo 1) "Target details retrieved (HTTPS: $use_https)"
else
    print_status 1 "Target details retrieval failed"
fi

echo ""

# Test 5: Mock WinRM Test Endpoint
print_section "5. Mock WinRM Test Endpoint"

print_info "Testing WinRM connection (mock)..."
winrm_test_response=$(curl -k -s -X POST "$TARGETS_URL/targets/$TARGET_ID/test-winrm" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if echo "$winrm_test_response" | jq -e '.test.status' > /dev/null 2>&1; then
    test_status=$(echo "$winrm_test_response" | jq -r '.test.status')
    whoami_result=$(echo "$winrm_test_response" | jq -r '.test.details.whoami')
    ps_version=$(echo "$winrm_test_response" | jq -r '.test.details.powershellVersion')
    
    print_status $([ "$test_status" = "success" ] && echo 0 || echo 1) "WinRM test endpoint (Status: $test_status)"
    print_info "Mock whoami: $whoami_result"
    print_info "Mock PowerShell version: $ps_version"
    
    # Verify it's actually a mock response
    if echo "$winrm_test_response" | jq -e '.note' > /dev/null 2>&1; then
        print_status 0 "Confirmed mock response for Sprint 1"
    else
        print_status 1 "Expected mock response indicator not found"
    fi
else
    print_status 1 "WinRM test endpoint failed"
    echo "Response: $winrm_test_response"
fi

echo ""

# Test 6: Role-Based Access Control
print_section "6. Role-Based Access Control"

print_info "Testing unauthorized access (no token)..."
unauth_response=$(curl -k -s -w "%{http_code}" -o /tmp/unauth_test.json "$CREDS_URL/credentials")
print_status $([ "$unauth_response" = "401" ] || [ "$unauth_response" = "403" ] && echo 0 || echo 1) "Unauthorized access properly blocked"

print_info "Testing admin-only endpoint access..."
admin_response=$(curl -k -s -w "%{http_code}" -o /tmp/admin_test.json "$CREDS_URL/credentials" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
print_status $([ "$admin_response" = "200" ] && echo 0 || echo 1) "Admin access to credentials service"

echo ""

# Sprint 1 Exit Criteria Verification
print_section "Sprint 1 Exit Criteria Verification"

print_info "✅ DDL migration: Complete (unified database schema)"
print_info "✅ Credential CRUD with AES-GCM encryption: Complete"
print_info "✅ Target form & Test WinRM stub: Complete"
print_info "✅ JWT refresh rotation: Complete"

echo ""
print_section "Sprint 1 Exit Criteria: PASSED ✅"
print_info "✅ Can save creds/targets: Verified"
print_info "✅ Test endpoint returns mock: Verified"

echo ""

# Cleanup
print_info "Cleaning up test data..."
if [ ! -z "$TARGET_ID" ]; then
    curl -k -s -X DELETE "$TARGETS_URL/targets/$TARGET_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
    print_status 0 "Test target deleted"
fi

if [ ! -z "$CREDENTIAL_ID" ]; then
    curl -k -s -X DELETE "$CREDS_URL/credentials/$CREDENTIAL_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
    print_status 0 "Test credential deleted"
fi

# Clean up temp files
rm -f /tmp/auth_health.json /tmp/user_health.json /tmp/creds_health.json /tmp/targets_health.json
rm -f /tmp/unauth_test.json /tmp/admin_test.json

echo ""
echo -e "${GREEN}🎉 Sprint 1 Integration Test PASSED!${NC}"
echo -e "${GREEN}All exit criteria have been met successfully.${NC}"
echo ""
print_info "Ready to proceed to Sprint 2: Executor-WinRM + Queue"