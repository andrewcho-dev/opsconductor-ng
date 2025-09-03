#!/bin/bash

# Simple HTTP Test
set -e

echo "🚀 Simple HTTP Test"
echo "==================="

# Test credentials
USERNAME="admin"
PASSWORD="admin123"

echo "Step 1: Login"
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:3001/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
AUTH_HEADER="Authorization: Bearer $TOKEN"

echo "Step 2: Create simple HTTP job"
HTTP_JOB_RESPONSE=$(curl -s -X POST "http://localhost:3006/jobs" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Simple HTTP Test",
    "version": 1,
    "definition": {
      "name": "Simple HTTP Test",
      "version": 1,
      "steps": [
        {
          "type": "http.get",
          "url": "https://httpbin.org/status/200"
        }
      ]
    }
  }')

echo "Response: $HTTP_JOB_RESPONSE"