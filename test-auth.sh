#!/bin/bash

echo "Testing Authentication..."

# Get auth token
AUTH_RESPONSE=$(curl -s -X POST http://localhost:80/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get authentication token"
    echo "Auth response: $AUTH_RESPONSE"
    exit 1
fi

echo "✅ Got authentication token"

# Test auth endpoint
AUTH_TEST_RESPONSE=$(curl -s -X GET http://localhost:80/api/v1/discovery/test-auth \
  -H "Authorization: Bearer $TOKEN")

echo "Auth test response: $AUTH_TEST_RESPONSE"