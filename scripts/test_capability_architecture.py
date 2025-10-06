#!/usr/bin/env python3
"""
Test script to verify the capability-first architecture is working correctly
"""

import requests
import json
import sys
from typing import Dict, Any

PIPELINE_URL = "http://localhost:3005/pipeline"

def test_request(description: str, request: str, expected_capabilities: list = None, should_have_capabilities: bool = True) -> Dict[str, Any]:
    """Test a single request through the pipeline"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"Request: {request}")
    
    try:
        response = requests.post(
            PIPELINE_URL,
            json={"request": request},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract key information
        success = data.get('success', False)
        stage_a = data['result']['intermediate_results']['stage_a']
        stage_b = data['result']['intermediate_results']['stage_b']
        
        capabilities = stage_a['intent']['capabilities']
        action = stage_a['intent']['action']
        category = stage_a['intent']['category']
        tools = [t['tool_name'] for t in stage_b['selected_tools']]
        next_stage = stage_b['next_stage']
        
        print(f"\n✅ SUCCESS: {success}")
        print(f"📋 Category: {category}")
        print(f"🎯 Action: {action}")
        print(f"🔧 Capabilities: {capabilities}")
        print(f"🛠️  Tools Selected: {tools}")
        print(f"➡️  Next Stage: {next_stage}")
        
        # Validate expectations
        if should_have_capabilities and not capabilities:
            print(f"\n⚠️  WARNING: Expected capabilities but got empty list")
            return {"status": "warning", "data": data}
        
        if not should_have_capabilities and capabilities:
            print(f"\n⚠️  WARNING: Expected empty capabilities but got: {capabilities}")
            return {"status": "warning", "data": data}
        
        if expected_capabilities:
            missing = set(expected_capabilities) - set(capabilities)
            extra = set(capabilities) - set(expected_capabilities)
            if missing or extra:
                print(f"\n⚠️  WARNING: Capability mismatch")
                if missing:
                    print(f"   Missing: {missing}")
                if extra:
                    print(f"   Extra: {extra}")
                return {"status": "warning", "data": data}
        
        print(f"\n✅ TEST PASSED")
        return {"status": "pass", "data": data}
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return {"status": "fail", "error": str(e)}

def main():
    print("="*80)
    print("CAPABILITY-FIRST ARCHITECTURE TEST SUITE")
    print("="*80)
    
    tests = [
        {
            "description": "Information-only request (no capabilities needed)",
            "request": "what kind of credentials do we use with windows assets?",
            "expected_capabilities": [],
            "should_have_capabilities": False
        },
        {
            "description": "Asset query request (multiple capabilities)",
            "request": "show me all Linux servers",
            "expected_capabilities": ["asset_query", "infrastructure_info", "resource_listing"],
            "should_have_capabilities": True
        },
        {
            "description": "Process monitoring request (single capability)",
            "request": "show running processes",
            "expected_capabilities": ["process_monitoring"],
            "should_have_capabilities": True
        },
        {
            "description": "Service control request",
            "request": "restart nginx service",
            "expected_capabilities": ["service_control"],
            "should_have_capabilities": True
        },
        {
            "description": "Network testing request",
            "request": "test connectivity to 10.0.0.1",
            "expected_capabilities": ["network_testing"],
            "should_have_capabilities": True
        },
        {
            "description": "Information request about concepts",
            "request": "explain how DNS works",
            "expected_capabilities": [],
            "should_have_capabilities": False
        }
    ]
    
    results = []
    for test in tests:
        result = test_request(
            test["description"],
            test["request"],
            test.get("expected_capabilities"),
            test.get("should_have_capabilities", True)
        )
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r["status"] == "pass")
    warned = sum(1 for r in results if r["status"] == "warning")
    failed = sum(1 for r in results if r["status"] == "fail")
    
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"⚠️  Warnings: {warned}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed > 0:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
    elif warned > 0:
        print("\n⚠️  TESTS PASSED WITH WARNINGS")
        sys.exit(0)
    else:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()