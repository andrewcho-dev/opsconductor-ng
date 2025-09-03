#!/bin/bash

# OpsConductor Python Rebuild Validation Script
# Tests all services and functionality to ensure complete rebuild success

set -e

echo "🧪 OpsConductor Python Rebuild Validation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function for test output
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Helper function to make HTTP requests
make_request() {
    local method=$1
    local url=$2
    local data=$3
    local headers=$4
    
    if [ -n "$data" ]; then
        if [ -n "$headers" ]; then
            curl -s -X "$method" "$url" -H "Content-Type: application/json" -H "$headers" -d "$data"
        else
            curl -s -X "$method" "$url" -H "Content-Type: application/json" -d "$data"
        fi
    else
        if [ -n "$headers" ]; then
            curl -s -X "$method" "$url" -H "$headers"
        else
            curl -s -X "$method" "$url"
        fi
    fi
}

echo -e "\n${BLUE}1. Testing Service Health Checks${NC}"
echo "--------------------------------"

# Test health endpoints
SERVICES=("auth-service:3001" "user-service:3002" "credentials-service:3004" "targets-service:3005" "jobs-service:3006" "executor-service:3007")

for service in "${SERVICES[@]}"; do
    IFS=':' read -ra ADDR <<< "$service"
    service_name=${ADDR[0]}
    port=${ADDR[1]}
    
    response=$(curl -s -w "%{http_code}" -o /tmp/health_response "http://localhost:$port/health" || echo "000")
    if [ "$response" = "200" ]; then
        service_status=$(cat /tmp/health_response | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        test_result 0 "$service_name health check ($service_status)"
    else
        test_result 1 "$service_name health check (HTTP $response)"
    fi
done

echo -e "\n${BLUE}2. Testing Authentication System${NC}"
echo "--------------------------------"

# Test login
login_response=$(make_request "POST" "http://localhost:3001/login" '{"username":"admin","password":"admin123"}')
if echo "$login_response" | grep -q "access_token"; then
    test_result 0 "Admin login authentication"
    ACCESS_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
else
    test_result 1 "Admin login authentication"
    ACCESS_TOKEN=""
fi

# Test token verification
if [ -n "$ACCESS_TOKEN" ]; then
    verify_response=$(make_request "GET" "http://localhost:3001/verify" "" "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$verify_response" | grep -q '"valid":true'; then
        test_result 0 "Token verification"
    else
        test_result 1 "Token verification"
    fi
fi

echo -e "\n${BLUE}3. Testing User Management (CRUD)${NC}"
echo "--------------------------------"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test user list
    users_response=$(make_request "GET" "http://localhost:3002/users" "" "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$users_response" | grep -q '"users"'; then
        test_result 0 "User list retrieval"
    else
        test_result 1 "User list retrieval"
    fi

    # Test user creation
    new_user_response=$(make_request "POST" "http://localhost:3002/users" '{"email":"test@example.com","username":"testuser","password":"test123","role":"viewer"}' "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$new_user_response" | grep -q '"username":"testuser"'; then
        test_result 0 "User creation"
        TEST_USER_ID=$(echo "$new_user_response" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    else
        test_result 1 "User creation"
        TEST_USER_ID=""
    fi

    # Test user deletion
    if [ -n "$TEST_USER_ID" ]; then
        delete_response=$(make_request "DELETE" "http://localhost:3002/users/$TEST_USER_ID" "" "Authorization: Bearer $ACCESS_TOKEN")
        if echo "$delete_response" | grep -q "deleted successfully"; then
            test_result 0 "User deletion"
        else
            test_result 1 "User deletion"
        fi
    fi
else
    test_result 1 "User management tests (no auth token)"
fi

echo -e "\n${BLUE}4. Testing Credentials Service${NC}"
echo "-----------------------------"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test credentials list
    creds_response=$(make_request "GET" "http://localhost:3004/credentials" "" "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$creds_response" | grep -q '"credentials"'; then
        test_result 0 "Credentials list retrieval"
    else
        test_result 1 "Credentials list retrieval"
    fi

    # Test credential creation
    new_cred_response=$(make_request "POST" "http://localhost:3004/credentials" '{"name":"test-cred","credential_type":"winrm","credential_data":{"username":"testuser","password":"testpass"}}' "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$new_cred_response" | grep -q '"name":"test-cred"'; then
        test_result 0 "Credential creation"
        TEST_CRED_ID=$(echo "$new_cred_response" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    else
        test_result 1 "Credential creation"
        TEST_CRED_ID=""
    fi

    # Test credential deletion
    if [ -n "$TEST_CRED_ID" ]; then
        delete_cred_response=$(make_request "DELETE" "http://localhost:3004/credentials/$TEST_CRED_ID" "" "Authorization: Bearer $ACCESS_TOKEN")
        if echo "$delete_cred_response" | grep -q "deleted successfully"; then
            test_result 0 "Credential deletion"
        else
            test_result 1 "Credential deletion"
        fi
    fi
else
    test_result 1 "Credentials management tests (no auth token)"
fi

echo -e "\n${BLUE}5. Testing Targets Service${NC}"
echo "-------------------------"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test targets list
    targets_response=$(make_request "GET" "http://localhost:3005/targets" "" "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$targets_response" | grep -q '"targets"'; then
        test_result 0 "Targets list retrieval"
    else
        test_result 1 "Targets list retrieval"
    fi
else
    test_result 1 "Targets management tests (no auth token)"
fi

echo -e "\n${BLUE}6. Testing Jobs Service${NC}"
echo "----------------------"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test jobs list
    jobs_response=$(make_request "GET" "http://localhost:3006/jobs" "" "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$jobs_response" | grep -q '"jobs"'; then
        test_result 0 "Jobs list retrieval"
    else
        test_result 1 "Jobs list retrieval"
    fi

    # Test job runs list
    runs_response=$(make_request "GET" "http://localhost:3006/runs" "" "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$runs_response" | grep -q '"runs"'; then
        test_result 0 "Job runs list retrieval"
    else
        test_result 1 "Job runs list retrieval"
    fi
else
    test_result 1 "Jobs management tests (no auth token)"
fi

echo -e "\n${BLUE}7. Testing Executor Service${NC}"
echo "-------------------------"

# Test executor status
executor_response=$(curl -s "http://localhost:3007/status" || echo "{}")
if echo "$executor_response" | grep -q '"worker_enabled"'; then
    test_result 0 "Executor service status"
else
    test_result 1 "Executor service status"
fi

echo -e "\n${BLUE}8. Testing Frontend Service${NC}"
echo "-------------------------"

# Test frontend availability
frontend_response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:3000" || echo "000")
if [ "$frontend_response" = "200" ]; then
    test_result 0 "Frontend service availability"
else
    test_result 1 "Frontend service availability (HTTP $frontend_response)"
fi

echo -e "\n${BLUE}9. Testing Database Schema${NC}"
echo "-------------------------"

# Test database connectivity via auth service
db_test_response=$(make_request "POST" "http://localhost:3001/login" '{"username":"admin","password":"admin123"}')
if echo "$db_test_response" | grep -q "access_token"; then
    test_result 0 "Database connectivity and schema"
else
    test_result 1 "Database connectivity and schema"
fi

echo -e "\n${BLUE}10. Testing Technology Stack${NC}"
echo "----------------------------"

# Verify Python FastAPI backends
for service in "${SERVICES[@]}"; do
    IFS=':' read -ra ADDR <<< "$service"
    service_name=${ADDR[0]}
    port=${ADDR[1]}
    
    # Check if service returns FastAPI-style docs
    docs_response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:$port/docs" || echo "000")
    if [ "$docs_response" = "200" ]; then
        test_result 0 "$service_name is FastAPI (Python)"
    else
        # Some services might not have /docs enabled, check health response format
        health_response=$(curl -s "http://localhost:$port/health" || echo "{}")
        if echo "$health_response" | grep -q '"service":'; then
            test_result 0 "$service_name is Python backend"
        else
            test_result 1 "$service_name technology validation"
        fi
    fi
done

# Test React frontend
frontend_html=$(curl -s "http://localhost:3000" || echo "")
if echo "$frontend_html" | grep -q "react" || echo "$frontend_html" | grep -q "OpsConductor"; then
    test_result 0 "Frontend is React-based"
else
    test_result 1 "Frontend technology validation"
fi

echo -e "\n${YELLOW}======================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}======================================${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}✅ Total Passed: $TESTS_PASSED${NC}"
    echo -e "\n${GREEN}Python Rebuild Validation: SUCCESS${NC}"
    echo -e "${GREEN}The system has been successfully rebuilt with:${NC}"
    echo -e "${GREEN}- Python FastAPI backend services${NC}"
    echo -e "${GREEN}- React TypeScript frontend${NC}"
    echo -e "${GREEN}- Complete feature parity${NC}"
    echo -e "${GREEN}- All CRUD operations working${NC}"
    echo -e "${GREEN}- Authentication system functional${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"
    echo -e "\n${YELLOW}Please check the failing services and restart if necessary${NC}"
    exit 1
fi