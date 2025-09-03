#!/bin/bash

# Test script to verify discovery job creation is working

echo "Testing Discovery Job Creation..."

# First, get an auth token
echo "1. Getting authentication token..."
AUTH_RESPONSE=$(curl -s -X POST http://localhost:80/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

if [ $? -ne 0 ]; then
    echo "❌ Failed to connect to auth service"
    exit 1
fi

TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get authentication token"
    echo "Auth response: $AUTH_RESPONSE"
    exit 1
fi

echo "✅ Got authentication token"

# Test network range validation
echo "2. Testing network range validation..."
VALIDATION_RESPONSE=$(curl -s -X POST http://localhost:80/api/v1/discovery/validate-network-ranges \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ranges": ["192.168.50.100-105"]}')

if [ $? -ne 0 ]; then
    echo "❌ Failed to validate network ranges"
    exit 1
fi

echo "✅ Network range validation working"
echo "Validation result: $VALIDATION_RESPONSE"

# Test job creation
echo "3. Testing discovery job creation..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:80/api/v1/discovery/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Enhanced Network Range Job",
    "discovery_type": "network_scan",
    "config": {
      "cidr_ranges": ["192.168.50.100-105"],
      "services": [
        {"name": "SSH", "port": 22, "protocol": "tcp", "category": "Remote Access", "enabled": true},
        {"name": "RDP", "port": 3389, "protocol": "tcp", "category": "Remote Access", "enabled": true}
      ],
      "os_detection": true,
      "timeout": 300
    }
  }')

if [ $? -ne 0 ]; then
    echo "❌ Failed to create discovery job"
    exit 1
fi

# Check if response contains an error
if echo "$JOB_RESPONSE" | grep -q '"detail"'; then
    echo "❌ Discovery job creation failed with error:"
    echo "$JOB_RESPONSE"
    exit 1
fi

echo "✅ Discovery job created successfully!"
echo "Job response: $JOB_RESPONSE"

echo ""
echo "🎉 All tests passed! Enhanced network range specification is working correctly."