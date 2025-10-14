#!/bin/bash
# Quick verification script for PR #8
# Tests the three main acceptance criteria

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${BASE_URL:-http://localhost:3000}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PR #8 Quick Verification${NC}"
echo -e "${BLUE}========================================${NC}\n"

# AC1: Tool Discovery
echo -e "${BLUE}[AC1]${NC} Testing tool discovery..."
response=$(curl -s "${BASE_URL}/ai/tools/list")
count=$(echo "$response" | jq -r '.total // 0')

if [ "$count" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} Tool discovery works ($count tools found)"
    echo "  Sample: $(echo "$response" | jq -r '.tools[0].name')"
else
    echo -e "${RED}✗ FAIL${NC} No tools found"
    exit 1
fi

# AC2: Port Check
echo -e "\n${BLUE}[AC2]${NC} Testing port check execution..."
response=$(curl -s -X POST "${BASE_URL}/ai/tools/execute" \
    -H "Content-Type: application/json" \
    -d '{"name":"tcp_port_check","params":{"host":"127.0.0.1","port":80}}')

success=$(echo "$response" | jq -r '.success')
tool=$(echo "$response" | jq -r '.tool')

if [ "$tool" = "tcp_port_check" ]; then
    echo -e "${GREEN}✓ PASS${NC} Port check executed (success=$success)"
else
    echo -e "${RED}✗ FAIL${NC} Port check failed"
    exit 1
fi

# AC3: Windows Tool
echo -e "\n${BLUE}[AC3]${NC} Testing Windows tool accessibility..."
response=$(curl -s -X POST "${BASE_URL}/ai/tools/execute" \
    -H "Content-Type: application/json" \
    -d '{"name":"windows_list_directory","params":{"host":"192.168.50.211","path":"C:\\","username":"test","password":"test"}}')

tool=$(echo "$response" | jq -r '.tool')

if [ "$tool" = "windows_list_directory" ]; then
    echo -e "${GREEN}✓ PASS${NC} Windows tool accessible (may have auth error, but not 404)"
else
    echo -e "${RED}✗ FAIL${NC} Windows tool not accessible"
    exit 1
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All acceptance criteria passed!${NC}"
echo -e "${GREEN}========================================${NC}\n"