#!/bin/bash

# Test Discovery Service
echo "=== Testing Discovery Service ==="

# Get auth token first
echo "1. Getting authentication token..."
AUTH_RESPONSE=$(curl -s -X POST http://localhost:3001/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get authentication token"
    echo "Response: $AUTH_RESPONSE"
    exit 1
fi

echo "✅ Got authentication token"

# Test health endpoint
echo ""
echo "2. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:3010/health)
echo "Health Response: $HEALTH_RESPONSE"

# Test discovery jobs endpoint (should require auth)
echo ""
echo "3. Testing discovery jobs endpoint..."
JOBS_RESPONSE=$(curl -s -X GET http://localhost:3010/api/v1/discovery/jobs \
  -H "Authorization: Bearer $TOKEN")
echo "Jobs Response: $JOBS_RESPONSE"

# Create a test discovery job
echo ""
echo "4. Creating test discovery job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:3010/api/v1/discovery/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Local Network Scan",
    "discovery_type": "network_scan",
    "config": {
      "cidr_ranges": ["127.0.0.1/32"],
      "scan_intensity": "light",
      "os_detection": true,
      "service_detection": true,
      "timeout": 60
    }
  }')

echo "Job Creation Response: $JOB_RESPONSE"

# Wait a moment for job to process
echo ""
echo "5. Waiting for job to process..."
sleep 5

# Check job status
echo ""
echo "6. Checking job status..."
JOBS_STATUS=$(curl -s -X GET http://localhost:3010/api/v1/discovery/jobs \
  -H "Authorization: Bearer $TOKEN")
echo "Jobs Status: $JOBS_STATUS"

# Check discovered targets
echo ""
echo "7. Checking discovered targets..."
TARGETS_RESPONSE=$(curl -s -X GET http://localhost:3010/api/v1/discovery/targets \
  -H "Authorization: Bearer $TOKEN")
echo "Discovered Targets: $TARGETS_RESPONSE"

echo ""
echo "=== Discovery Service Test Complete ==="