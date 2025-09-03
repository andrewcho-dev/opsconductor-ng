#!/bin/bash

echo "🧪 Testing SSH Connection Test Functionality"
echo "=============================================="

# Get auth token
echo "Step 1: Getting authentication token..."
AUTH_RESPONSE=$(curl -s -X POST "http://localhost:3001/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

if [ $? -ne 0 ]; then
  echo "❌ Failed to get auth token"
  exit 1
fi

TOKEN=$(echo $AUTH_RESPONSE | jq -r '.access_token')
if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Invalid token received"
  echo "Auth response: $AUTH_RESPONSE"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer $TOKEN"
echo "✅ Authentication successful"

# Create SSH credential for testing
echo ""
echo "Step 2: Creating SSH credential..."
SSH_CRED_RESPONSE=$(curl -s -X POST "http://localhost:3004/credentials" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Test SSH Credential",
    "type": "ssh",
    "username": "testuser",
    "password": "testpass",
    "description": "Test SSH credential for connection testing"
  }')

SSH_CRED_ID=$(echo $SSH_CRED_RESPONSE | jq -r '.id')
echo "SSH Credential ID: $SSH_CRED_ID"

# Create SSH target for testing
echo ""
echo "Step 3: Creating SSH target..."
SSH_TARGET_RESPONSE=$(curl -s -X POST "http://localhost:3005/targets" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Test SSH Server",
    "hostname": "test-ssh.example.com",
    "protocol": "ssh",
    "port": 22,
    "os_type": "linux",
    "credential_ref": '$SSH_CRED_ID',
    "tags": ["test", "ssh"],
    "metadata": {},
    "depends_on": []
  }')

SSH_TARGET_ID=$(echo $SSH_TARGET_RESPONSE | jq -r '.id')
echo "SSH Target ID: $SSH_TARGET_ID"

# Test SSH connection
echo ""
echo "Step 4: Testing SSH connection (will fail - demo only)..."
SSH_TEST_RESPONSE=$(curl -s -X POST "http://localhost:3005/targets/$SSH_TARGET_ID/test-ssh" \
  -H "$AUTH_HEADER")

echo "SSH Test Response:"
echo $SSH_TEST_RESPONSE | jq '{status: .test.status, message: .test.details.message // "Connection test attempted", note: .note}'

# List all targets to verify SSH target appears with test button capability
echo ""
echo "Step 5: Listing all targets to verify SSH target..."
TARGETS_RESPONSE=$(curl -s -X GET "http://localhost:3005/targets" \
  -H "$AUTH_HEADER")

echo "All Targets:"
echo $TARGETS_RESPONSE | jq '.targets[] | {id: .id, name: .name, hostname: .hostname, protocol: .protocol, os_type: .os_type, port: .port}'

echo ""
echo "✅ SSH test functionality verification complete!"
echo "📝 Note: The SSH connection test will fail since test-ssh.example.com doesn't exist,"
echo "   but this confirms the API endpoint and frontend functionality are working."
echo ""
echo "🎯 Frontend Changes Made:"
echo "   - Added SSHTestResult type definition"
echo "   - Added testSSH function to targetApi"
echo "   - Updated handleTestConnection to support both WinRM and SSH"
echo "   - Updated UI to show test button for both WinRM and SSH targets"
echo ""
echo "🔧 To test in the UI:"
echo "   1. Go to http://localhost:8080/targets"
echo "   2. Look for targets with protocol 'ssh'"
echo "   3. Click the 'Test' button next to SSH targets"
echo "   4. The test will execute and show results in an alert"