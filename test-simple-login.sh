#!/bin/bash

echo "🧪 Testing Simple Login Functionality"
echo "====================================="

# Test user service health first
echo "1. Testing user service health..."
HEALTH_RESPONSE=$(curl -s http://localhost:3001/health)
if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    echo "✅ User service is healthy"
else
    echo "❌ User service health check failed"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

echo ""
echo "2. Testing direct login to user service..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

echo "Login response: $LOGIN_RESPONSE"

if [[ "$LOGIN_RESPONSE" == *"accessToken"* ]]; then
    echo "✅ Login successful!"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
    echo "Access token obtained: ${ACCESS_TOKEN:0:50}..."
else
    echo "❌ Login failed"
    echo "Full response: $LOGIN_RESPONSE"
fi

echo ""
echo "3. Testing user lookup..."
USER_RESPONSE=$(curl -s http://localhost:3001/users/admin)
echo "User lookup response: $USER_RESPONSE"

echo ""
echo "4. Checking available users in database..."
echo "Getting users list..."
USERS_RESPONSE=$(curl -s http://localhost:3001/users)
echo "Users response: $USERS_RESPONSE"