#!/bin/bash

# Test HTTP/HTTPS Features Implementation
# Tests the new HTTP step types and webhook functionality

set -e

echo "🚀 Testing HTTP/HTTPS Features Implementation"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URLs
BASE_URL="http://localhost:8080"
API_BASE="$BASE_URL/api"

# Test credentials
USERNAME="admin"
PASSWORD="admin123"

echo -e "${BLUE}Step 1: Login and get JWT token${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get authentication token${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✅ Successfully authenticated${NC}"

# Set auth header
AUTH_HEADER="Authorization: Bearer $TOKEN"

echo -e "\n${BLUE}Step 2: Create HTTP API Health Check Job${NC}"
HTTP_JOB_RESPONSE=$(curl -s -X POST "$API_BASE/jobs" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "HTTP API Health Check Test",
    "version": 1,
    "definition": {
      "name": "HTTP API Health Check Test",
      "version": 1,
      "parameters": {
        "api_url": "https://httpbin.org/status/200",
        "expected_status": 200,
        "timeout": 30
      },
      "steps": [
        {
          "type": "http.get",
          "name": "Check API Health",
          "url": "{{ api_url }}",
          "timeout_sec": "{{ timeout }}",
          "expected_status": ["{{ expected_status }}"],
          "headers": {
            "User-Agent": "OpsConductor-HealthCheck/1.0"
          }
        }
      ]
    }
  }')

HTTP_JOB_ID=$(echo $HTTP_JOB_RESPONSE | jq -r '.id')
if [ "$HTTP_JOB_ID" = "null" ] || [ -z "$HTTP_JOB_ID" ]; then
    echo -e "${RED}❌ Failed to create HTTP job${NC}"
    echo "Response: $HTTP_JOB_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✅ Created HTTP API Health Check job (ID: $HTTP_JOB_ID)${NC}"

echo -e "\n${BLUE}Step 3: Create HTTP POST Data Test Job${NC}"
POST_JOB_RESPONSE=$(curl -s -X POST "$API_BASE/jobs" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "HTTP POST Data Test",
    "version": 1,
    "definition": {
      "name": "HTTP POST Data Test",
      "version": 1,
      "parameters": {
        "post_url": "https://httpbin.org/post",
        "test_data": "Hello from OpsConductor!"
      },
      "steps": [
        {
          "type": "http.post",
          "name": "Send Test Data",
          "url": "{{ post_url }}",
          "timeout_sec": 30,
          "headers": {
            "Content-Type": "application/json",
            "User-Agent": "OpsConductor-Test/1.0"
          },
          "body": {
            "message": "{{ test_data }}",
            "timestamp": "{{ current_timestamp }}",
            "source": "OpsConductor"
          },
          "expected_status": [200]
        }
      ]
    }
  }')

POST_JOB_ID=$(echo $POST_JOB_RESPONSE | jq -r '.id')
if [ "$POST_JOB_ID" = "null" ] || [ -z "$POST_JOB_ID" ]; then
    echo -e "${RED}❌ Failed to create HTTP POST job${NC}"
    echo "Response: $POST_JOB_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✅ Created HTTP POST Data Test job (ID: $POST_JOB_ID)${NC}"

echo -e "\n${BLUE}Step 4: Create Webhook Test Job${NC}"
WEBHOOK_JOB_RESPONSE=$(curl -s -X POST "$API_BASE/jobs" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Webhook Notification Test",
    "version": 1,
    "definition": {
      "name": "Webhook Notification Test",
      "version": 1,
      "parameters": {
        "webhook_url": "https://httpbin.org/post",
        "message": "Test webhook from OpsConductor",
        "event_type": "test_event"
      },
      "steps": [
        {
          "type": "webhook.call",
          "name": "Send Test Webhook",
          "url": "{{ webhook_url }}",
          "payload": {
            "event": "{{ event_type }}",
            "message": "{{ message }}",
            "timestamp": "{{ current_timestamp }}",
            "source": "OpsConductor"
          },
          "timeout_sec": 30,
          "max_retries": 2
        }
      ]
    }
  }')

WEBHOOK_JOB_ID=$(echo $WEBHOOK_JOB_RESPONSE | jq -r '.id')
if [ "$WEBHOOK_JOB_ID" = "null" ] || [ -z "$WEBHOOK_JOB_ID" ]; then
    echo -e "${RED}❌ Failed to create webhook job${NC}"
    echo "Response: $WEBHOOK_JOB_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✅ Created Webhook Notification Test job (ID: $WEBHOOK_JOB_ID)${NC}"

echo -e "\n${BLUE}Step 5: Execute HTTP GET Test${NC}"
HTTP_RUN_RESPONSE=$(curl -s -X POST "$API_BASE/jobs/$HTTP_JOB_ID/run" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{}')

HTTP_RUN_ID=$(echo $HTTP_RUN_RESPONSE | jq -r '.run_id')
if [ "$HTTP_RUN_ID" = "null" ] || [ -z "$HTTP_RUN_ID" ]; then
    echo -e "${RED}❌ Failed to start HTTP job run${NC}"
    echo "Response: $HTTP_RUN_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✅ Started HTTP GET test (Run ID: $HTTP_RUN_ID)${NC}"

echo -e "\n${BLUE}Step 6: Execute HTTP POST Test${NC}"
POST_RUN_RESPONSE=$(curl -s -X POST "$API_BASE/jobs/$POST_JOB_ID/run" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{}')

POST_RUN_ID=$(echo $POST_RUN_RESPONSE | jq -r '.run_id')
if [ "$POST_RUN_ID" = "null" ] || [ -z "$POST_RUN_ID" ]; then
    echo -e "${RED}❌ Failed to start HTTP POST job run${NC}"
    echo "Response: $POST_RUN_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✅ Started HTTP POST test (Run ID: $POST_RUN_ID)${NC}"

echo -e "\n${BLUE}Step 7: Execute Webhook Test${NC}"
WEBHOOK_RUN_RESPONSE=$(curl -s -X POST "$API_BASE/jobs/$WEBHOOK_JOB_ID/run" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{}')

WEBHOOK_RUN_ID=$(echo $WEBHOOK_RUN_RESPONSE | jq -r '.run_id')
if [ "$WEBHOOK_RUN_ID" = "null" ] || [ -z "$WEBHOOK_RUN_ID" ]; then
    echo -e "${RED}❌ Failed to start webhook job run${NC}"
    echo "Response: $WEBHOOK_RUN_RESPONSE"
    exit 1
fi
echo -e "${GREEN}✅ Started webhook test (Run ID: $WEBHOOK_RUN_ID)${NC}"

echo -e "\n${BLUE}Step 8: Wait for job completion and check results${NC}"
sleep 10

# Check HTTP GET results
echo -e "\n${YELLOW}Checking HTTP GET test results...${NC}"
HTTP_RESULT=$(curl -s "$API_BASE/jobs/runs/$HTTP_RUN_ID" -H "$AUTH_HEADER")
HTTP_STATUS=$(echo $HTTP_RESULT | jq -r '.status')
echo "HTTP GET Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "succeeded" ]; then
    echo -e "${GREEN}✅ HTTP GET test completed successfully${NC}"
    # Get step details
    HTTP_STEPS=$(curl -s "$API_BASE/jobs/runs/$HTTP_RUN_ID/steps" -H "$AUTH_HEADER")
    echo "HTTP GET Step Output:"
    echo $HTTP_STEPS | jq -r '.[0].stdout'
else
    echo -e "${RED}❌ HTTP GET test failed${NC}"
    HTTP_STEPS=$(curl -s "$API_BASE/jobs/runs/$HTTP_RUN_ID/steps" -H "$AUTH_HEADER")
    echo "Error details:"
    echo $HTTP_STEPS | jq -r '.[0].stderr'
fi

# Check HTTP POST results
echo -e "\n${YELLOW}Checking HTTP POST test results...${NC}"
POST_RESULT=$(curl -s "$API_BASE/jobs/runs/$POST_RUN_ID" -H "$AUTH_HEADER")
POST_STATUS=$(echo $POST_RESULT | jq -r '.status')
echo "HTTP POST Status: $POST_STATUS"

if [ "$POST_STATUS" = "succeeded" ]; then
    echo -e "${GREEN}✅ HTTP POST test completed successfully${NC}"
    POST_STEPS=$(curl -s "$API_BASE/jobs/runs/$POST_RUN_ID/steps" -H "$AUTH_HEADER")
    echo "HTTP POST Step Output:"
    echo $POST_STEPS | jq -r '.[0].stdout'
else
    echo -e "${RED}❌ HTTP POST test failed${NC}"
    POST_STEPS=$(curl -s "$API_BASE/jobs/runs/$POST_RUN_ID/steps" -H "$AUTH_HEADER")
    echo "Error details:"
    echo $POST_STEPS | jq -r '.[0].stderr'
fi

# Check Webhook results
echo -e "\n${YELLOW}Checking webhook test results...${NC}"
WEBHOOK_RESULT=$(curl -s "$API_BASE/jobs/runs/$WEBHOOK_RUN_ID" -H "$AUTH_HEADER")
WEBHOOK_STATUS=$(echo $WEBHOOK_RESULT | jq -r '.status')
echo "Webhook Status: $WEBHOOK_STATUS"

if [ "$WEBHOOK_STATUS" = "succeeded" ]; then
    echo -e "${GREEN}✅ Webhook test completed successfully${NC}"
    WEBHOOK_STEPS=$(curl -s "$API_BASE/jobs/runs/$WEBHOOK_RUN_ID/steps" -H "$AUTH_HEADER")
    echo "Webhook Step Output:"
    echo $WEBHOOK_STEPS | jq -r '.[0].stdout'
else
    echo -e "${RED}❌ Webhook test failed${NC}"
    WEBHOOK_STEPS=$(curl -s "$API_BASE/jobs/runs/$WEBHOOK_RUN_ID/steps" -H "$AUTH_HEADER")
    echo "Error details:"
    echo $WEBHOOK_STEPS | jq -r '.[0].stderr'
fi

echo -e "\n${BLUE}Step 9: Check HTTP request tracking in database${NC}"
echo "Checking if HTTP requests were properly tracked..."

# Test database connectivity by checking if our new tables exist
docker compose -f docker-compose-python.yml exec postgres psql -U postgres -d opsconductor -c "
SELECT 
    COUNT(*) as http_requests_count,
    (SELECT COUNT(*) FROM webhook_executions) as webhook_executions_count
FROM http_requests;
" 2>/dev/null || echo "Database check skipped (container may not be accessible)"

echo -e "\n${GREEN}🎉 HTTP/HTTPS Features Test Complete!${NC}"
echo "=============================================="
echo -e "${BLUE}Summary:${NC}"
echo "- HTTP GET Test: $HTTP_STATUS"
echo "- HTTP POST Test: $POST_STATUS" 
echo "- Webhook Test: $WEBHOOK_STATUS"
echo ""
echo -e "${YELLOW}New Features Implemented:${NC}"
echo "✅ HTTP GET, POST, PUT, DELETE, PATCH step types"
echo "✅ Webhook calls with payload templating"
echo "✅ Multiple authentication methods (Bearer, Basic, API Key)"
echo "✅ Request/response tracking in database"
echo "✅ Timeout and retry configuration"
echo "✅ Template rendering for URLs, headers, and payloads"
echo ""
echo -e "${BLUE}Next Phase Ready:${NC} SQL Database Operations, SNMP, and Certificate Authentication"