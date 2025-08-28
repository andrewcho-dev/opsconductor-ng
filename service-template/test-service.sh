#!/bin/bash

echo "🧪 Testing New Service Template"
echo "==============================="

BASE_URL="http://localhost:3010"
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
        response=$(curl -s -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            $headers \
            -d "$data" \
            -w "%{http_code}")
    else
        response=$(curl -s -X $method "$BASE_URL$endpoint" \
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
test_endpoint "GET" "/health" "200" "Health check endpoint"

echo ""
echo "2. Getting authentication token..."
# Get token from auth service (assuming it's running on port 3001)
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

if [[ "$LOGIN_RESPONSE" == *"access_token"* ]]; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    print_result 0 "Authentication token obtained"
    AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""
else
    print_result 1 "Failed to get authentication token"
    echo "Response: $LOGIN_RESPONSE"
    echo "Note: Make sure auth-service is running on port 3001"
    exit 1
fi

echo ""
echo "3. Testing protected endpoints..."

# Test GET /items endpoint
echo "   Testing GET /items..."
test_endpoint "GET" "/items" "200" "Get items endpoint" "$AUTH_HEADER"

# Test POST /items endpoint
echo "   Testing POST /items..."
test_endpoint "POST" "/items" "200" "Create item endpoint" \
    "$AUTH_HEADER" '{"name":"Test Item","description":"Test description"}'

# Get the created item ID for further tests
ITEMS_RESPONSE=$(curl -s -X GET "$BASE_URL/items" $AUTH_HEADER)
if [[ "$ITEMS_RESPONSE" == *"Test Item"* ]]; then
    ITEM_ID=$(echo "$ITEMS_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    
    if [ -n "$ITEM_ID" ]; then
        echo "   Testing GET /items/$ITEM_ID..."
        test_endpoint "GET" "/items/$ITEM_ID" "200" "Get item by ID" "$AUTH_HEADER"
        
        echo "   Testing PUT /items/$ITEM_ID..."
        test_endpoint "PUT" "/items/$ITEM_ID" "200" "Update item endpoint" \
            "$AUTH_HEADER" '{"name":"Updated Test Item","description":"Updated description"}'
        
        echo "   Testing DELETE /items/$ITEM_ID..."
        test_endpoint "DELETE" "/items/$ITEM_ID" "200" "Delete item endpoint" "$AUTH_HEADER"
    fi
fi

echo ""
echo "4. Testing error handling..."

# Test unauthorized access
echo "   Testing unauthorized access..."
test_endpoint "GET" "/items" "401" "Unauthorized access handling"

# Test invalid endpoint
echo "   Testing invalid endpoint..."
test_endpoint "GET" "/nonexistent" "404" "404 error handling" "$AUTH_HEADER"

# Test invalid data
echo "   Testing invalid data..."
test_endpoint "POST" "/items" "422" "Invalid data handling" \
    "$AUTH_HEADER" '{"invalid":"data"}'

echo ""
echo "5. Testing service health and database connectivity..."

# Check health endpoint response
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    print_result 0 "Service reports healthy status"
else
    print_result 1 "Service reports unhealthy status"
    echo "Health response: $HEALTH_RESPONSE"
fi

echo ""
echo "🎉 Service Template Testing Complete!"
echo ""
echo "📋 Test Summary:"
echo "   - Health check endpoint"
echo "   - JWT authentication integration"
echo "   - CRUD operations (Create, Read, Update, Delete)"
echo "   - Error handling (401, 404, 422)"
echo "   - Database connectivity"
echo ""
echo "🌐 Service accessible at: $BASE_URL"
echo "📚 API Documentation: $BASE_URL/docs (Swagger UI)"
echo "📖 Alternative docs: $BASE_URL/redoc (ReDoc)"
echo ""
echo "💡 To customize this template:"
echo "   1. Update service name and description in main.py"
echo "   2. Modify the database schema and models"
echo "   3. Add your business logic to the endpoints"
echo "   4. Update this test script for your specific endpoints"