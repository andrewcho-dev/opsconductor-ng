#!/usr/bin/env python3
"""
Tool Catalog API Integration Test
Tests all REST API endpoints for the Tool Catalog system.
"""

import sys
import requests
import json
import yaml
from typing import Dict, Any

# API base URL
API_BASE = "http://localhost:3005/api/v1/tools"

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print('=' * 70)

def print_test(test_name: str):
    """Print a test name"""
    print(f"\n{test_name}...")

def print_success(message: str):
    """Print success message"""
    print(f"   ✓ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"   ✗ {message}")

def test_health_check():
    """Test health check endpoint"""
    print_test("1. Testing health check")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Health check passed: {data['status']}")
        print_success(f"Tool count: {data['tool_count']}")
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_list_tools():
    """Test listing all tools"""
    print_test("2. Testing list tools")
    
    try:
        response = requests.get(API_BASE)
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Retrieved {data['total']} tools")
        
        for tool in data['tools']:
            print(f"     - {tool['tool_name']} ({tool['platform']}/{tool['category']})")
        
        return True, data['tools']
    except Exception as e:
        print_error(f"List tools failed: {e}")
        return False, []

def test_get_tool(tool_name: str):
    """Test getting a specific tool"""
    print_test(f"3. Testing get tool: {tool_name}")
    
    try:
        response = requests.get(f"{API_BASE}/{tool_name}")
        response.raise_for_status()
        
        tool = response.json()
        print_success(f"Retrieved tool: {tool['tool_name']}")
        print_success(f"  Version: {tool['version']}")
        print_success(f"  Platform: {tool['platform']}")
        print_success(f"  Category: {tool['category']}")
        print_success(f"  Status: {tool['status']}")
        print_success(f"  Enabled: {tool['enabled']}")
        
        return True
    except Exception as e:
        print_error(f"Get tool failed: {e}")
        return False

def test_get_tool_versions(tool_name: str):
    """Test getting tool versions"""
    print_test(f"4. Testing get tool versions: {tool_name}")
    
    try:
        response = requests.get(f"{API_BASE}/{tool_name}/versions")
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Found {data['total_versions']} version(s)")
        
        for version in data['versions']:
            print(f"     - Version {version['version']} (created: {version['created_at']})")
        
        return True
    except Exception as e:
        print_error(f"Get tool versions failed: {e}")
        return False

def test_search_tools(query: str):
    """Test searching tools"""
    print_test(f"5. Testing search tools: '{query}'")
    
    try:
        response = requests.get(f"{API_BASE}/search/query", params={"q": query})
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Found {data['total']} matching tools")
        
        for tool in data['results']:
            print(f"     - {tool['tool_name']}: {tool['description'][:60]}...")
        
        return True
    except Exception as e:
        print_error(f"Search tools failed: {e}")
        return False

def test_filter_by_platform(platform: str):
    """Test filtering tools by platform"""
    print_test(f"6. Testing filter by platform: {platform}")
    
    try:
        response = requests.get(f"{API_BASE}/platform/{platform}")
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Found {data['total']} {platform} tools")
        
        for tool in data['tools']:
            print(f"     - {tool['tool_name']}")
        
        return True
    except Exception as e:
        print_error(f"Filter by platform failed: {e}")
        return False

def test_filter_by_category(category: str):
    """Test filtering tools by category"""
    print_test(f"7. Testing filter by category: {category}")
    
    try:
        response = requests.get(f"{API_BASE}/category/{category}")
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Found {data['total']} {category} tools")
        
        for tool in data['tools']:
            print(f"     - {tool['tool_name']}")
        
        return True
    except Exception as e:
        print_error(f"Filter by category failed: {e}")
        return False

def test_list_capabilities():
    """Test listing all capabilities"""
    print_test("8. Testing list capabilities")
    
    try:
        response = requests.get(f"{API_BASE}/capabilities/list")
        response.raise_for_status()
        
        capabilities = response.json()
        print_success(f"Found {len(capabilities)} capabilities")
        
        for cap in capabilities:
            print(f"     - {cap['capability_name']}: {cap['tool_count']} tool(s)")
            for tool in cap['tools']:
                print(f"       • {tool}")
        
        return True, capabilities
    except Exception as e:
        print_error(f"List capabilities failed: {e}")
        return False, []

def test_get_tools_by_capability(capability_name: str):
    """Test getting tools by capability"""
    print_test(f"9. Testing get tools by capability: {capability_name}")
    
    try:
        response = requests.get(f"{API_BASE}/capabilities/{capability_name}/tools")
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Found {data['total']} tools with {capability_name} capability")
        
        for tool in data['tools']:
            print(f"     - {tool['tool_name']}")
        
        return True
    except Exception as e:
        print_error(f"Get tools by capability failed: {e}")
        return False

def test_validate_tool(tool_name: str):
    """Test tool validation"""
    print_test(f"10. Testing validate tool: {tool_name}")
    
    try:
        response = requests.post(f"{API_BASE}/{tool_name}/validate")
        response.raise_for_status()
        
        result = response.json()
        
        if result['valid']:
            print_success("Tool validation passed")
        else:
            print_error("Tool validation failed")
            for error in result['errors']:
                print(f"       Error: {error}")
        
        if result['warnings']:
            for warning in result['warnings']:
                print(f"       Warning: {warning}")
        
        return result['valid']
    except Exception as e:
        print_error(f"Validate tool failed: {e}")
        return False

def test_enable_disable_tool(tool_name: str):
    """Test enabling and disabling a tool"""
    print_test(f"11. Testing enable/disable tool: {tool_name}")
    
    try:
        # Disable tool
        response = requests.patch(f"{API_BASE}/{tool_name}/disable")
        response.raise_for_status()
        tool = response.json()
        
        if not tool['enabled']:
            print_success("Tool disabled successfully")
        else:
            print_error("Tool disable failed")
            return False
        
        # Enable tool
        response = requests.patch(f"{API_BASE}/{tool_name}/enable")
        response.raise_for_status()
        tool = response.json()
        
        if tool['enabled']:
            print_success("Tool enabled successfully")
        else:
            print_error("Tool enable failed")
            return False
        
        return True
    except Exception as e:
        print_error(f"Enable/disable tool failed: {e}")
        return False

def test_create_tool():
    """Test creating a new tool"""
    print_test("12. Testing create tool")
    
    tool_data = {
        "tool_name": "test_tool",
        "version": "1.0",
        "description": "Test tool for API testing",
        "platform": "linux",
        "category": "system",
        "status": "testing",
        "enabled": True,
        "defaults": {
            "accuracy_level": "real-time",
            "freshness": "live",
            "data_source": "direct"
        },
        "dependencies": [],
        "metadata": {
            "author": "API Test",
            "tags": ["test", "api"]
        },
        "capabilities": [
            {
                "capability_name": "test_capability",
                "description": "Test capability",
                "patterns": [
                    {
                        "pattern_name": "test_pattern",
                        "description": "Test pattern",
                        "typical_use_cases": ["testing"],
                        "time_estimate_ms": "1000",
                        "cost_estimate": "1",
                        "complexity_score": 0.5,
                        "scope": "local",
                        "completeness": "full",
                        "limitations": [],
                        "policy": {
                            "max_cost": 10,
                            "requires_approval": False,
                            "production_safe": False
                        },
                        "preference_match": {
                            "speed": 0.5,
                            "accuracy": 0.5,
                            "cost": 0.5,
                            "complexity": 0.5,
                            "completeness": 0.5
                        },
                        "required_inputs": [
                            {
                                "name": "test_input",
                                "type": "string",
                                "required": True,
                                "description": "Test input"
                            }
                        ],
                        "expected_outputs": [
                            {
                                "name": "test_output",
                                "type": "string",
                                "description": "Test output"
                            }
                        ],
                        "examples": []
                    }
                ]
            }
        ],
        "created_by": "api_test"
    }
    
    try:
        response = requests.post(API_BASE, json=tool_data)
        response.raise_for_status()
        
        tool = response.json()
        print_success(f"Tool created: {tool['tool_name']}")
        print_success(f"  ID: {tool['id']}")
        print_success(f"  Version: {tool['version']}")
        
        return True, tool['tool_name']
    except Exception as e:
        print_error(f"Create tool failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"  Response: {e.response.text}")
        return False, None

def test_update_tool(tool_name: str):
    """Test updating a tool"""
    print_test(f"13. Testing update tool: {tool_name}")
    
    update_data = {
        "description": "Updated test tool description",
        "status": "active",
        "updated_by": "api_test"
    }
    
    try:
        response = requests.put(f"{API_BASE}/{tool_name}", json=update_data)
        response.raise_for_status()
        
        tool = response.json()
        print_success(f"Tool updated: {tool['tool_name']}")
        print_success(f"  New description: {tool['description']}")
        print_success(f"  New status: {tool['status']}")
        
        return True
    except Exception as e:
        print_error(f"Update tool failed: {e}")
        return False

def test_export_tools(tool_names: list):
    """Test exporting tools"""
    print_test(f"14. Testing export tools: {', '.join(tool_names)}")
    
    try:
        response = requests.post(f"{API_BASE}/export", json=tool_names)
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Exported {data['tool_count']} tool(s)")
        print_success(f"  YAML length: {len(data['yaml_content'])} characters")
        
        return True
    except Exception as e:
        print_error(f"Export tools failed: {e}")
        return False

def test_delete_tool(tool_name: str):
    """Test deleting a tool"""
    print_test(f"15. Testing delete tool: {tool_name}")
    
    try:
        response = requests.delete(f"{API_BASE}/{tool_name}")
        response.raise_for_status()
        
        print_success(f"Tool deleted: {tool_name}")
        
        # Verify deletion
        response = requests.get(f"{API_BASE}/{tool_name}")
        if response.status_code == 404:
            print_success("Deletion verified (tool not found)")
            return True
        else:
            print_error("Deletion verification failed (tool still exists)")
            return False
    except Exception as e:
        print_error(f"Delete tool failed: {e}")
        return False

def run_all_tests():
    """Run all API tests"""
    print_section("TOOL CATALOG API INTEGRATION TEST")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: List tools
    success, tools = test_list_tools()
    results.append(("List Tools", success))
    
    if not tools:
        print_error("No tools found - cannot continue with remaining tests")
        return False
    
    # Use first tool for subsequent tests
    test_tool_name = tools[0]['tool_name']
    
    # Test 3: Get tool
    results.append(("Get Tool", test_get_tool(test_tool_name)))
    
    # Test 4: Get tool versions
    results.append(("Get Tool Versions", test_get_tool_versions(test_tool_name)))
    
    # Test 5: Search tools
    results.append(("Search Tools", test_search_tools("search")))
    
    # Test 6: Filter by platform
    results.append(("Filter by Platform", test_filter_by_platform("linux")))
    
    # Test 7: Filter by category
    results.append(("Filter by Category", test_filter_by_category("system")))
    
    # Test 8: List capabilities
    success, capabilities = test_list_capabilities()
    results.append(("List Capabilities", success))
    
    # Test 9: Get tools by capability
    if capabilities:
        cap_name = capabilities[0]['capability_name']
        results.append(("Get Tools by Capability", test_get_tools_by_capability(cap_name)))
    
    # Test 10: Validate tool
    results.append(("Validate Tool", test_validate_tool(test_tool_name)))
    
    # Test 11: Enable/disable tool
    results.append(("Enable/Disable Tool", test_enable_disable_tool(test_tool_name)))
    
    # Test 12: Create tool
    success, new_tool_name = test_create_tool()
    results.append(("Create Tool", success))
    
    if new_tool_name:
        # Test 13: Update tool
        results.append(("Update Tool", test_update_tool(new_tool_name)))
        
        # Test 14: Export tools
        results.append(("Export Tools", test_export_tools([new_tool_name])))
        
        # Test 15: Delete tool
        results.append(("Delete Tool", test_delete_tool(new_tool_name)))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print(f"❌ {total - passed} TEST(S) FAILED")
        print("=" * 70)
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)