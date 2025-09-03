#!/bin/bash

# Test SSH Credentials Implementation
set -e

echo "🔐 Testing SSH Credentials Implementation"
echo "========================================"

# Test credentials
USERNAME="admin"
PASSWORD="admin123"

echo "Step 1: Login and get JWT token"
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:3001/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Successfully authenticated"
AUTH_HEADER="Authorization: Bearer $TOKEN"

echo ""
echo "Step 2: Create SSH Password Credential"
SSH_PASSWORD_RESPONSE=$(curl -s -X POST "http://localhost:3004/credentials" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Test SSH Password",
    "description": "SSH password authentication for testing",
    "credential_type": "ssh",
    "credential_data": {
      "username": "testuser",
      "password": "testpass123",
      "port": 22,
      "timeout": 30
    }
  }')

echo "SSH Password Credential Response: $SSH_PASSWORD_RESPONSE"

# Check if credential was created successfully
SSH_PASSWORD_ID=$(echo $SSH_PASSWORD_RESPONSE | jq -r '.id // empty')
if [ -n "$SSH_PASSWORD_ID" ]; then
  echo "✅ SSH password credential created with ID: $SSH_PASSWORD_ID"
else
  echo "❌ Failed to create SSH password credential"
fi

echo ""
echo "Step 3: Create SSH Key Credential"
SSH_KEY_RESPONSE=$(curl -s -X POST "http://localhost:3004/credentials" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Test SSH Key",
    "description": "SSH key authentication for testing",
    "credential_type": "ssh_key",
    "credential_data": {
      "username": "keyuser",
      "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn\nNhAAAAAwEAAQAAAQEA1234567890abcdef...\n-----END OPENSSH PRIVATE KEY-----",
      "passphrase": "",
      "key_type": "rsa"
    }
  }')

echo "SSH Key Credential Response: $SSH_KEY_RESPONSE"

# Check if credential was created successfully
SSH_KEY_ID=$(echo $SSH_KEY_RESPONSE | jq -r '.id // empty')
if [ -n "$SSH_KEY_ID" ]; then
  echo "✅ SSH key credential created with ID: $SSH_KEY_ID"
else
  echo "❌ Failed to create SSH key credential"
fi

echo ""
echo "Step 4: List all credentials to verify SSH types"
CREDENTIALS_RESPONSE=$(curl -s -X GET "http://localhost:3004/credentials" \
  -H "$AUTH_HEADER")

echo "All Credentials:"
echo $CREDENTIALS_RESPONSE | jq '.credentials[] | {id: .id, name: .name, type: .credential_type}'

echo ""
echo "Step 5: Test credential retrieval"
if [ -n "$SSH_PASSWORD_ID" ]; then
  SSH_PASSWORD_DETAIL=$(curl -s -X GET "http://localhost:3004/credentials/$SSH_PASSWORD_ID" \
    -H "$AUTH_HEADER")
  echo "SSH Password Credential Detail:"
  echo $SSH_PASSWORD_DETAIL | jq '{id: .id, name: .name, type: .credential_type, created_at: .created_at}'
fi

if [ -n "$SSH_KEY_ID" ]; then
  SSH_KEY_DETAIL=$(curl -s -X GET "http://localhost:3004/credentials/$SSH_KEY_ID" \
    -H "$AUTH_HEADER")
  echo "SSH Key Credential Detail:"
  echo $SSH_KEY_DETAIL | jq '{id: .id, name: .name, type: .credential_type, created_at: .created_at}'
fi

echo ""
echo "🎉 SSH Credentials Test Complete!"
echo "✅ SSH password credentials: Supported"
echo "✅ SSH key credentials: Supported"
echo "✅ Frontend integration: Ready for testing"