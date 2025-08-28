#!/bin/bash

echo "🔍 Testing OS Type API Implementation"
echo "===================================="

# Get auth token
TOKEN=$(curl -s -X POST "http://localhost:3001/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

echo "✅ Got auth token"

# Test creating a new target with os_type
echo ""
echo "Creating new target with os_type..."
CREATE_RESPONSE=$(curl -s -X POST "http://localhost:3005/targets" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Linux Server",
    "hostname": "test.example.com",
    "protocol": "ssh",
    "port": 22,
    "os_type": "linux",
    "credential_ref": 1,
    "tags": ["test"],
    "metadata": {"test": true}
  }')

echo "Create Response:"
echo $CREATE_RESPONSE | jq '.'

TARGET_ID=$(echo $CREATE_RESPONSE | jq -r '.id // empty')

if [ -n "$TARGET_ID" ]; then
  echo ""
  echo "✅ Target created with ID: $TARGET_ID"
  
  # Get the target back
  echo ""
  echo "Retrieving target..."
  GET_RESPONSE=$(curl -s -X GET "http://localhost:3005/targets/$TARGET_ID" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "Get Response:"
  echo $GET_RESPONSE | jq '{id, name, hostname, protocol, os_type, port}'
  
  # Clean up
  echo ""
  echo "Cleaning up test target..."
  curl -s -X DELETE "http://localhost:3005/targets/$TARGET_ID" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "✅ Test target deleted"
else
  echo "❌ Failed to create test target"
fi

echo ""
echo "🔍 Direct database check:"
docker exec -i opsconductor-postgres psql -U postgres -d opsconductor -c "SELECT id, name, os_type FROM targets ORDER BY id DESC LIMIT 3;"