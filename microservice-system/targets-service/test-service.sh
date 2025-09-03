#!/bin/bash

echo "🧪 Testing New Service"
echo "====================="

BASE_URL="https://localhost"
SERVICE_NAME="new-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local headers=$5
    local data=$6
    
    if [ -n "$data" ]; then
        response=$(curl -k -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            $headers \
            -d "$data" \
            -w "%{http_code}")
    else
        response=$(curl -k -s -X $method "$BASE_URL$endpoint" \
            $headers \
            -w "%{http_code}")
    fi
    
    status_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$status_code" = "$expected_status" ]; then
        print_result 0 "$description"
        return 0
    else
        print_result 1 "$description (Expected: $expected_status, Got: $status_code)"
        echo "Response: $response_body"
        return 1
    fi
}

echo ""
echo "1. Testing service health endpoint..."
test_endpoint "GET" "/api/$SERVICE_NAME/health" "200" "Health check endpoint"

echo ""
echo "2. Testing service info endpoint..."
test_endpoint "GET" "/api/$SERVICE_NAME/info" "200" "Service info endpoint"

echo ""
echo "3. Getting authentication token..."
LOGIN_RESPONSE=$(curl -k -s -X POST $BASE_URL/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}')

if [[ "$LOGIN_RESPONSE" == *"token"* ]]; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    print_result 0 "Authentication token obtained"
    AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""
else
    print_result 1 "Failed to get authentication token"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo ""
echo "4. Testing protected endpoints..."

# Test GET /data endpoint
echo "   Testing GET /data..."
test_endpoint "GET" "/api/$SERVICE_NAME/data" "200" "Get data endpoint" "$AUTH_HEADER"

# Test POST /data endpoint
echo "   Testing POST /data..."
test_endpoint "POST" "/api/$SERVICE_NAME/data" "201" "Create data endpoint" \
    "$AUTH_HEADER" '{"name":"Test Item","description":"Test description"}'

# Test GET /data with pagination
echo "   Testing GET /data with pagination..."
test_endpoint "GET" "/api/$SERVICE_NAME/data?page=1&limit=5" "200" "Get data with pagination" "$AUTH_HEADER"

echo ""
echo "5. Testing service-to-service communication..."
# Get current user ID from token verification
USER_INFO=$(curl -k -s -X POST $BASE_URL/api/verify -H "Authorization: Bearer $TOKEN")
if [[ "$USER_INFO" == *"user"* ]]; then
    USER_ID=$(echo "$USER_INFO" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    test_endpoint "GET" "/api/$SERVICE_NAME/user-info/$USER_ID" "200" "Service-to-service communication" "$AUTH_HEADER"
else
    print_result 1 "Could not get user ID for service-to-service test"
fi

echo ""
echo "6. Testing error handling..."

# Test unauthorized access
echo "   Testing unauthorized access..."
test_endpoint "GET" "/api/$SERVICE_NAME/data" "401" "Unauthorized access handling"

# Test invalid endpoint
echo "   Testing invalid endpoint..."
test_endpoint "GET" "/api/$SERVICE_NAME/nonexistent" "404" "404 error handling" "$AUTH_HEADER"

# Test invalid data
echo "   Testing invalid data..."
test_endpoint "POST" "/api/$SERVICE_NAME/data" "400" "Invalid data handling" \
    "$AUTH_HEADER" '{"invalid":"data"}'

echo ""
echo "7. Testing service integration..."

# Check if service is accessible through nginx
NGINX_RESPONSE=$(curl -k -s -o /dev/null -w "%{http_code}" $BASE_URL/api/$SERVICE_NAME/health)
if [ "$NGINX_RESPONSE" = "200" ]; then
    print_result 0 "Service accessible through nginx gateway"
else
    print_result 1 "Service not accessible through nginx gateway"
fi

# Check if service can communicate with other services
AUTH_HEALTH=$(curl -k -s -o /dev/null -w "%{http_code}" $BASE_URL/api/verify -H "Authorization: Bearer $TOKEN")
if [ "$AUTH_HEALTH" = "200" ]; then
    print_result 0 "Service can communicate with auth service"
else
    print_result 1 "Service cannot communicate with auth service"
fi

echo ""
echo "🎉 Service Testing Complete!"
echo ""
echo "📋 Test Summary:"
echo "   - Health check endpoint"
echo "   - Service info endpoint"
echo "   - Authentication integration"
echo "   - Protected endpoints"
echo "   - CRUD operations"
echo "   - Service-to-service communication"
echo "   - Error handling"
echo "   - Gateway integration"
echo ""
echo "🌐 Service accessible at: $BASE_URL/api/$SERVICE_NAME/"
echo "📚 API Documentation: See README.md"