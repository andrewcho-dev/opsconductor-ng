#!/usr/bin/env python3
"""
Frontend API Testing Script
Tests the ACTUAL running system through HTTP API calls
This matches what the frontend does - no mocks, no local imports
"""

import requests
import json
import sys
from typing import Literal

API_URL = "http://localhost:3005"
TIMEOUT = 120

# Color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

# Test counters
total_tests = 0
passed_tests = 0
failed_tests = 0


def test_query(query: str, expected_tool_type: Literal["asset", "prometheus"], test_name: str) -> bool:
    """Test a single query through the actual API"""
    global total_tests, passed_tests, failed_tests
    
    total_tests += 1
    
    print("----------------------------------------")
    print(f"Test #{total_tests}: {test_name}")
    print(f'Query: "{query}"')
    print(f"Expected: {expected_tool_type} tool")
    print()
    
    try:
        # Make the actual API call
        response = requests.post(
            f"{API_URL}/pipeline",
            json={"request": query},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"{RED}❌ FAILED: API request failed: {e}{NC}")
        failed_tests += 1
        return False
    except Exception as e:
        print(f"{RED}❌ FAILED: Unexpected error: {e}{NC}")
        failed_tests += 1
        return False
    
    if not data:
        print(f"{RED}❌ FAILED: Empty response from API{NC}")
        failed_tests += 1
        return False
    
    # Debug: print response structure
    print(f"DEBUG: Response keys: {list(data.keys())}")
    
    # Extract key information from the new pipeline response structure
    intermediate_results = data.get("result", {}).get("intermediate_results", {}) if data.get("result") else {}
    stage_a_result = intermediate_results.get("stage_a", {})
    stage_b_result = intermediate_results.get("stage_b", {})
    
    stage_a_category = stage_a_result.get("intent", {}).get("category", "null")
    stage_a_action = stage_a_result.get("intent", {}).get("action", "null")
    stage_b_tools = stage_b_result.get("selected_tools", [])
    stage_b_tool = stage_b_tools[0].get("tool_name", "null") if stage_b_tools else "null"
    error = data.get("error", None)
    
    print(f"Stage A Category: {stage_a_category}")
    print(f"Stage A Action: {stage_a_action}")
    print(f"Stage B Tool: {stage_b_tool}")
    
    if error:
        print(f"{RED}❌ FAILED: Pipeline error: {error}{NC}")
        failed_tests += 1
        return False
    
    # Validate based on expected tool type
    if expected_tool_type == "asset":
        # Should NOT be prometheus
        if "prometheus" in stage_b_tool.lower():
            print(f"{RED}❌ FAILED: Selected prometheus instead of asset tool!{NC}")
            failed_tests += 1
            return False
        
        # Should be asset-related
        if any(keyword in stage_b_tool.lower() for keyword in ["asset", "inventory", "cmdb"]):
            print(f"{GREEN}✅ PASSED: Correctly selected asset tool{NC}")
            passed_tests += 1
            return True
        else:
            print(f"{RED}❌ FAILED: Did not select asset tool (got: {stage_b_tool}){NC}")
            failed_tests += 1
            return False
            
    elif expected_tool_type == "prometheus":
        # Should be prometheus
        if "prometheus" in stage_b_tool.lower():
            print(f"{GREEN}✅ PASSED: Correctly selected prometheus tool{NC}")
            passed_tests += 1
            return True
        else:
            print(f"{RED}❌ FAILED: Did not select prometheus tool (got: {stage_b_tool}){NC}")
            failed_tests += 1
            return False
    
    print(f"{RED}❌ FAILED: Unknown validation result{NC}")
    failed_tests += 1
    return False


def main():
    print("==========================================")
    print("🧪 FRONTEND API TESTING")
    print("Testing actual Docker containers via HTTP")
    print("==========================================")
    print()
    
    # Check if API is reachable
    print("Checking API health...")
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        health_data = health_response.json()
        if health_data.get("status") == "healthy":
            print(f"{GREEN}✅ API is healthy{NC}")
            print()
        else:
            print(f"{RED}❌ API is not healthy{NC}")
            sys.exit(1)
    except Exception as e:
        print(f"{RED}❌ API is not reachable at {API_URL}: {e}{NC}")
        sys.exit(1)
    
    # Run tests - Asset queries (should select asset tools)
    print("==========================================")
    print("📦 ASSET QUERY TESTS")
    print("==========================================")
    print()
    
    test_query("Show me all assets", "asset", "Basic asset listing")
    test_query("Show me all Linux servers", "asset", "Filtered asset listing")
    test_query("How many assets do we have?", "asset", "Asset count query")
    test_query("Find all Windows servers", "asset", "Asset search query")
    test_query("List all database servers", "asset", "Asset listing with filter")
    test_query("Get asset info for server web-01", "asset", "Specific asset query")
    test_query("Search for assets with IP 10.0.1.5", "asset", "Asset search by IP")
    test_query("Show me all production assets", "asset", "Asset filter by environment")
    test_query("How many Linux servers are there?", "asset", "Asset count with filter")
    test_query("What servers do we have?", "asset", "Natural language asset query")
    
    # Run tests - Monitoring queries (should select prometheus)
    print()
    print("==========================================")
    print("📊 MONITORING QUERY TESTS")
    print("==========================================")
    print()
    
    test_query("Show me CPU usage", "prometheus", "Basic monitoring query")
    
    # Summary
    print()
    print("==========================================")
    print("📊 TEST SUMMARY")
    print("==========================================")
    print(f"Total Tests: {total_tests}")
    print(f"{GREEN}Passed: {passed_tests}{NC}")
    print(f"{RED}Failed: {failed_tests}{NC}")
    print()
    
    if failed_tests == 0:
        print(f"{GREEN}🎉 ALL TESTS PASSED!{NC}")
        sys.exit(0)
    else:
        print(f"{RED}❌ SOME TESTS FAILED{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()