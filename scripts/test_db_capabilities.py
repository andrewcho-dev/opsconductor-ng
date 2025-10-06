#!/usr/bin/env python3
"""
Test that the capability-first architecture works with database capabilities.
This validates that Stage A prompt, input mapping, and database are synchronized.
"""

import asyncio
import sys
import json
from typing import List

# Test cases
TEST_CASES = [
    {
        "name": "Information-only request",
        "request": "What is a service mesh?",
        "expected_capabilities": [],
        "description": "Conceptual questions should return empty capabilities"
    },
    {
        "name": "Asset query",
        "request": "Show me all production servers",
        "expected_capabilities": ["asset_query", "infrastructure_info", "resource_listing"],
        "description": "Asset queries should identify multiple asset-related capabilities"
    },
    {
        "name": "Process monitoring",
        "request": "Show me running processes",
        "expected_capabilities": ["process_monitoring"],
        "description": "Process monitoring should identify process_monitoring capability"
    },
    {
        "name": "Network testing",
        "request": "Test connectivity to 10.0.0.1",
        "expected_capabilities": ["network_testing"],
        "description": "Network testing should identify network_testing capability"
    },
    {
        "name": "Service management",
        "request": "Restart nginx service",
        "expected_capabilities": ["service_management"],
        "description": "Service control should identify service_management capability"
    },
    {
        "name": "System info",
        "request": "Show system information",
        "expected_capabilities": ["system_info"],
        "description": "System info requests should identify system_info capability"
    }
]


async def test_capability_detection():
    """Test that Stage A correctly identifies capabilities from database"""
    
    print("=" * 80)
    print("TESTING DATABASE-BACKED CAPABILITY DETECTION")
    print("=" * 80)
    print()
    
    # Import here to avoid issues if modules aren't available
    try:
        import requests
    except ImportError:
        print("❌ requests module not available")
        return False
    
    base_url = "http://localhost:3005"
    
    # Check if service is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ AI Pipeline service not healthy: {response.status_code}")
            return False
        print("✅ AI Pipeline service is running")
        print()
    except Exception as e:
        print(f"❌ Cannot connect to AI Pipeline service: {e}")
        print("   Make sure the service is running on port 3005")
        return False
    
    # Run test cases
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"Test {i}/{len(TEST_CASES)}: {test_case['name']}")
        print(f"  Request: {test_case['request']}")
        print(f"  Expected: {test_case['expected_capabilities']}")
        
        try:
            # Send request to pipeline
            response = requests.post(
                f"{base_url}/pipeline",
                json={"request": test_case['request']},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ❌ FAILED: HTTP {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                failed += 1
                print()
                continue
            
            result = response.json()
            
            # Extract capabilities from Stage A decision
            # The pipeline returns the full result, so we need to extract the decision
            capabilities = []
            
            if 'result' in result:
                pipeline_result = result['result']
                
                # Check if we have stage_a_decision in the result
                if 'stage_a_decision' in pipeline_result:
                    decision = pipeline_result['stage_a_decision']
                    if 'intent' in decision:
                        capabilities = decision['intent'].get('capabilities', [])
                # Or check if decision is at the top level
                elif 'decision' in pipeline_result:
                    decision = pipeline_result['decision']
                    if 'intent' in decision:
                        capabilities = decision['intent'].get('capabilities', [])
            
            # If we still don't have capabilities, check the old format
            if not capabilities and 'decision' in result and 'intent' in result['decision']:
                capabilities = result['decision']['intent'].get('capabilities', [])
            
            # For information-only requests, empty capabilities is expected
            if not capabilities and test_case['expected_capabilities'] == []:
                # This is OK for information-only requests
                pass
            elif not capabilities:
                print(f"  ❌ FAILED: No capabilities found in response")
                print(f"     Response keys: {list(result.keys())}")
                if 'result' in result:
                    print(f"     Result keys: {list(result['result'].keys())}")
                failed += 1
                print()
                continue
            
            print(f"  Actual: {capabilities}")
            
            # Check if capabilities match (order doesn't matter)
            expected_set = set(test_case['expected_capabilities'])
            actual_set = set(capabilities)
            
            if expected_set == actual_set:
                print(f"  ✅ PASSED")
                passed += 1
            else:
                print(f"  ❌ FAILED: Capability mismatch")
                if expected_set - actual_set:
                    print(f"     Missing: {expected_set - actual_set}")
                if actual_set - expected_set:
                    print(f"     Extra: {actual_set - expected_set}")
                failed += 1
            
        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
            failed += 1
        
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total: {len(TEST_CASES)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print()
    
    if failed == 0:
        print("🎉 All tests passed! Database capabilities are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_capability_detection())
    sys.exit(0 if success else 1)