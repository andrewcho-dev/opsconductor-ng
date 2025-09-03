#!/bin/bash

echo "=== Testing Target Groups Functionality ==="

# Get admin token
echo "Getting admin token..."
ADMIN_TOKEN=$(curl -s -X POST http://localhost:3001/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Failed to get admin token"
    exit 1
fi

echo "✅ Got admin token"

# Test 1: List target groups (should be empty initially)
echo -e "\n1. Testing list target groups..."
GROUPS_RESPONSE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:3005/target-groups)
echo "Response: $GROUPS_RESPONSE"

# Test 2: Create a simple target group
echo -e "\n2. Testing create target group..."
CREATE_RESPONSE=$(curl -s -X POST http://localhost:3005/target-groups \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Group",
    "description": "A test target group",
    "targets": [],
    "tags": ["test"]
  }')
echo "Create response: $CREATE_RESPONSE"

# Extract group ID
GROUP_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
if [ "$GROUP_ID" = "null" ] || [ -z "$GROUP_ID" ]; then
    echo "❌ Failed to create target group"
    exit 1
fi

echo "✅ Created target group with ID: $GROUP_ID"

# Test 3: Get the created group
echo -e "\n3. Testing get target group by ID..."
GET_RESPONSE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:3005/target-groups/$GROUP_ID)
echo "Get response: $GET_RESPONSE"

# Test 4: Update the group
echo -e "\n4. Testing update target group..."
UPDATE_RESPONSE=$(curl -s -X PUT http://localhost:3005/target-groups/$GROUP_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Test Group",
    "description": "An updated test target group",
    "targets": [],
    "tags": ["test", "updated"]
  }')
echo "Update response: $UPDATE_RESPONSE"

# Test 5: List groups again (should show our group)
echo -e "\n5. Testing list target groups again..."
GROUPS_RESPONSE2=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:3005/target-groups)
echo "Response: $GROUPS_RESPONSE2"

# Test 6: Delete the group
echo -e "\n6. Testing delete target group..."
DELETE_RESPONSE=$(curl -s -X DELETE http://localhost:3005/target-groups/$GROUP_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN")
echo "Delete response: $DELETE_RESPONSE"

# Test 7: Verify group is deleted
echo -e "\n7. Testing get deleted group (should fail)..."
GET_DELETED_RESPONSE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:3005/target-groups/$GROUP_ID)
echo "Get deleted response: $GET_DELETED_RESPONSE"

echo -e "\n=== Target Groups Test Complete ==="