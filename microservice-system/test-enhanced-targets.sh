#!/bin/bash

# Enhanced Targets Service Test Script
# Tests the new multi-service architecture endpoints

set -e

BASE_URL="http://localhost"
AUTH_TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to make authenticated API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
             -H "Content-Type: application/json" \
             -H "Authorization: Bearer $AUTH_TOKEN" \
             -d "$data" \
             "$BASE_URL$endpoint"
    else
        curl -s -X "$method" \
             -H "Authorization: Bearer $AUTH_TOKEN" \
             "$BASE_URL$endpoint"
    fi
}

# Function to authenticate and get token
authenticate() {
    print_status "Authenticating..."
    
    # Try to get token from existing login
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}' \
        "$BASE_URL/api/v1/auth/login" 2>/dev/null || echo "")
    
    if [ -n "$response" ] && echo "$response" | grep -q "access_token"; then
        AUTH_TOKEN=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
        if [ -n "$AUTH_TOKEN" ]; then
            print_status "Authentication successful"
            return 0
        fi
    fi
    
    print_warning "Authentication failed or admin user not found"
    print_warning "Please ensure the system is running and admin user exists"
    return 1
}

# Test service definitions endpoint
test_service_definitions() {
    print_status "Testing service definitions endpoint..."
    
    local response=$(api_call "GET" "/api/v1/targets/service-definitions")
    
    if echo "$response" | grep -q "services"; then
        local count=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('services', [])))" 2>/dev/null || echo "0")
        print_status "✓ Service definitions endpoint working - found $count services"
        
        # Test with category filter
        local filtered_response=$(api_call "GET" "/api/v1/targets/service-definitions?category=remote")
        if echo "$filtered_response" | grep -q "services"; then
            print_status "✓ Service definitions category filter working"
        else
            print_warning "Service definitions category filter may not be working"
        fi
    else
        print_error "✗ Service definitions endpoint failed"
        echo "Response: $response"
    fi
}

# Test enhanced targets endpoint
test_enhanced_targets() {
    print_status "Testing enhanced targets endpoint..."
    
    local response=$(api_call "GET" "/api/v1/targets")
    
    if echo "$response" | grep -q "targets"; then
        local count=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('targets', [])))" 2>/dev/null || echo "0")
        print_status "✓ Enhanced targets endpoint working - found $count targets"
    else
        print_error "✗ Enhanced targets endpoint failed"
        echo "Response: $response"
    fi
}

# Test creating an enhanced target
test_create_enhanced_target() {
    print_status "Testing enhanced target creation..."
    
    local target_data='{
        "name": "test-enhanced-target",
        "hostname": "test.example.com",
        "ip_address": "192.168.1.100",
        "os_type": "windows",
        "os_version": "Windows Server 2022",
        "description": "Test target for enhanced API",
        "tags": ["test", "enhanced"],
        "services": [
            {
                "service_type": "winrm",
                "port": 5985,
                "is_secure": false,
                "is_enabled": true,
                "notes": "Default WinRM configuration"
            }
        ],
        "credentials": []
    }'
    
    local response=$(api_call "POST" "/api/v1/targets" "$target_data")
    
    if echo "$response" | grep -q "test-enhanced-target"; then
        local target_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
        print_status "✓ Enhanced target creation successful - ID: $target_id"
        
        # Store target ID for cleanup
        echo "$target_id" > /tmp/test_target_id
        
        # Test getting the specific target
        local get_response=$(api_call "GET" "/api/v1/targets/$target_id")
        if echo "$get_response" | grep -q "test-enhanced-target"; then
            print_status "✓ Enhanced target retrieval successful"
        else
            print_warning "Enhanced target retrieval may have issues"
        fi
        
    else
        print_error "✗ Enhanced target creation failed"
        echo "Response: $response"
    fi
}

# Test adding a service to target
test_add_service() {
    if [ ! -f /tmp/test_target_id ]; then
        print_warning "Skipping service addition test - no target ID available"
        return
    fi
    
    local target_id=$(cat /tmp/test_target_id)
    print_status "Testing service addition to target $target_id..."
    
    local service_data='{
        "service_type": "rdp",
        "port": 3389,
        "is_secure": true,
        "is_enabled": true,
        "notes": "RDP service for remote desktop"
    }'
    
    local response=$(api_call "POST" "/api/v1/targets/$target_id/services" "$service_data")
    
    if echo "$response" | grep -q "rdp"; then
        print_status "✓ Service addition successful"
    else
        print_error "✗ Service addition failed"
        echo "Response: $response"
    fi
}

# Test health endpoint
test_health() {
    print_status "Testing health endpoint..."
    
    local response=$(api_call "GET" "/api/v1/targets/health")
    
    if echo "$response" | grep -q "status"; then
        print_status "✓ Health endpoint working"
    else
        print_error "✗ Health endpoint failed"
        echo "Response: $response"
    fi
}

# Cleanup test data
cleanup() {
    if [ -f /tmp/test_target_id ]; then
        local target_id=$(cat /tmp/test_target_id)
        print_status "Cleaning up test target $target_id..."
        
        local response=$(api_call "DELETE" "/api/v1/targets/$target_id")
        print_status "✓ Test target cleanup completed"
        
        rm -f /tmp/test_target_id
    fi
}

# Main test execution
main() {
    echo "=========================================="
    echo "Enhanced Targets Service Test Suite"
    echo "=========================================="
    
    # Check if services are running
    if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        print_error "Services are not accessible at $BASE_URL"
        print_error "Please ensure the system is running with: ./start-python-system.sh"
        exit 1
    fi
    
    # Authenticate
    if ! authenticate; then
        exit 1
    fi
    
    # Run tests
    test_health
    test_service_definitions
    test_enhanced_targets
    test_create_enhanced_target
    test_add_service
    
    # Cleanup
    cleanup
    
    echo "=========================================="
    print_status "Enhanced Targets Service tests completed!"
    echo "=========================================="
}

# Run main function
main "$@"