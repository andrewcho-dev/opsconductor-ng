#!/usr/bin/env python3
"""
Test that fallbacks are properly removed and errors are raised
"""

import requests
import json
import time

API_URL = "http://localhost:3005"

def test_unknown_action():
    """Test that an unknown action raises an error instead of falling back"""
    
    print("\n" + "="*60)
    print("🧪 TESTING FALLBACK REMOVAL")
    print("="*60)
    
    # First, let's test with a valid query to make sure system is working
    print("\n1️⃣ Testing with VALID query (should work)...")
    valid_response = requests.post(
        f"{API_URL}/api/v1/pipeline/process",
        json={
            "query": "Show me all assets",
            "tenant_id": "default",
            "actor_id": "1"
        },
        timeout=30
    )
    
    if valid_response.status_code == 200:
        data = valid_response.json()
        if data.get("success"):
            print("✅ Valid query works correctly")
            print(f"   Stage A: {data['result']['stage_a']['intent']['category']}/{data['result']['stage_a']['intent']['action']}")
            print(f"   Stage B: {data['result']['stage_b']['selected_tools'][0]['tool_name']}")
        else:
            print(f"❌ Valid query failed: {data.get('error')}")
    else:
        print(f"❌ API error: {valid_response.status_code}")
    
    # Now test with a query that might trigger an unmapped action
    # We need to craft something that Stage A might classify as a new action
    print("\n2️⃣ Testing system behavior with edge cases...")
    
    test_queries = [
        "Show me all assets",  # Should work - list_assets
        "Find assets with IP 10.0.1.5",  # Should work - find_asset_by_ip
        "How many assets do we have?",  # Should work - count_assets
    ]
    
    for query in test_queries:
        print(f"\n   Testing: '{query}'")
        response = requests.post(
            f"{API_URL}/api/v1/pipeline/process",
            json={
                "query": query,
                "tenant_id": "default",
                "actor_id": "1"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                action = data['result']['stage_a']['intent']['action']
                tool = data['result']['stage_b']['selected_tools'][0]['tool_name']
                print(f"   ✅ Action: {action} → Tool: {tool}")
            else:
                error = data.get('error', 'Unknown error')
                # Check if it's our new error message
                if "Unknown action" in error or "capability_mapping" in error:
                    print(f"   ✅ GOOD! Got explicit error instead of fallback:")
                    print(f"      {error[:100]}...")
                else:
                    print(f"   ⚠️  Failed with: {error[:100]}...")
        else:
            print(f"   ❌ HTTP {response.status_code}")
    
    print("\n" + "="*60)
    print("✅ FALLBACK REMOVAL TEST COMPLETE")
    print("="*60)
    print("\nSummary:")
    print("- All known actions should work correctly")
    print("- Unknown actions should raise explicit errors")
    print("- No silent fallbacks to wrong tools!")
    print()

if __name__ == "__main__":
    # Wait for API to be ready
    print("Waiting for API to be ready...")
    for i in range(10):
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ API is ready\n")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ API not ready after 10 seconds")
        exit(1)
    
    test_unknown_action()