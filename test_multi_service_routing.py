#!/usr/bin/env python3
"""
Quick test to verify multi-service routing works correctly
"""

import sys
sys.path.append('/home/opsconductor/opsconductor-ng')

from pipeline.stages.stage_e.executor import StageEExecutor
from execution.models import ExecutionModel, ExecutionMode, SLAClass
from uuid import uuid4
from datetime import datetime

def test_routing():
    """Test that Stage E routes to correct services"""
    
    print("=" * 80)
    print("TESTING MULTI-SERVICE ROUTING")
    print("=" * 80)
    print()
    
    # Create executor (without database for testing)
    executor = StageEExecutor()
    
    # Test cases
    test_cases = [
        {
            "name": "Ping (automation-service)",
            "tool": "ping",
            "expected_service": "automation-service"
        },
        {
            "name": "Sendmail (communication-service)",
            "tool": "sendmail",
            "expected_service": "communication-service"
        },
        {
            "name": "Asset Query (asset-service)",
            "tool": "asset-query",
            "expected_service": "asset-service"
        },
        {
            "name": "Tcpdump (network-service)",
            "tool": "tcpdump",
            "expected_service": "network-analyzer-service"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        print(f"  Tool: {test_case['tool']}")
        print(f"  Expected: {test_case['expected_service']}")
        
        # Create mock execution
        execution = ExecutionModel(
            execution_id=uuid4(),
            tenant_id="test-tenant",
            actor_id=1,
            idempotency_key="test-key",
            plan_snapshot={
                "steps": [
                    {
                        "tool": test_case["tool"],
                        "inputs": {"host": "test-host"}
                    }
                ]
            },
            execution_mode=ExecutionMode.IMMEDIATE,
            sla_class=SLAClass.FAST,
            approval_level=0,
            created_at=datetime.utcnow()
        )
        
        # Get service URL
        try:
            service_url = executor._get_execution_service_url(execution)
            
            # Extract service name from URL
            if "automation-service" in service_url:
                actual_service = "automation-service"
            elif "communication-service" in service_url:
                actual_service = "communication-service"
            elif "asset-service" in service_url:
                actual_service = "asset-service"
            elif "network-analyzer-service" in service_url:
                actual_service = "network-analyzer-service"
            else:
                actual_service = "unknown"
            
            # Check if correct
            is_correct = actual_service == test_case["expected_service"]
            status = "✅ PASS" if is_correct else "❌ FAIL"
            
            print(f"  Actual: {actual_service}")
            print(f"  Status: {status}")
            print()
            
            results.append({
                "test": test_case["name"],
                "expected": test_case["expected_service"],
                "actual": actual_service,
                "passed": is_correct
            })
        
        except Exception as e:
            print(f"  Error: {e}")
            print(f"  Status: ❌ ERROR")
            print()
            
            results.append({
                "test": test_case["name"],
                "expected": test_case["expected_service"],
                "actual": f"ERROR: {e}",
                "passed": False
            })
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    for result in results:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['test']}")
        if not result["passed"]:
            print(f"   Expected: {result['expected']}")
            print(f"   Actual: {result['actual']}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(test_routing())