#!/usr/bin/env python3
"""
Test script for Pipeline V2 (Combined Stage AB)

This script tests the new simplified pipeline architecture and compares it with V1.
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.orchestrator_v2 import PipelineOrchestratorV2
from llm.factory import get_default_llm_client


# Test cases covering different scenarios
TEST_CASES = [
    {
        "name": "Asset Count Query",
        "request": "How many assets do we have?",
        "expected_tools": ["asset-query"],
        "expected_type": "data_query",
        "description": "Tests if V2 correctly selects asset-query tool for inventory questions"
    },
    {
        "name": "Asset Filter Query",
        "request": "Show me all Windows servers",
        "expected_tools": ["asset-query"],
        "expected_type": "data_query",
        "description": "Tests filtered asset queries"
    },
    {
        "name": "Service Management",
        "request": "Restart nginx service",
        "expected_tools": ["systemctl"],
        "expected_type": "action",
        "description": "Tests service management tool selection"
    },
    {
        "name": "Information Request",
        "request": "What is Kubernetes?",
        "expected_tools": [],
        "expected_type": "information",
        "description": "Tests information-only requests (no tools needed)"
    },
    {
        "name": "Status Check",
        "request": "What is the status of the web server?",
        "expected_tools": ["systemctl", "service-status"],
        "expected_type": "monitoring",
        "description": "Tests monitoring tool selection"
    },
    {
        "name": "Credential Query",
        "request": "What credentials do we use for production?",
        "expected_tools": [],
        "expected_type": "information",
        "description": "Tests that credential queries don't trigger tool execution (security)"
    }
]


async def test_single_request(orchestrator, test_case):
    """Test a single request and return results"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_case['name']}")
    print(f"{'='*80}")
    print(f"Request: {test_case['request']}")
    print(f"Expected: {test_case['description']}")
    print(f"-" * 80)
    
    start_time = time.time()
    
    try:
        # Process request
        result = await orchestrator.process_request(
            user_request=test_case['request'],
            context={"test_mode": True}
        )
        
        duration = (time.time() - start_time) * 1000
        
        # Extract results
        selection = result.intermediate_results.get("stage_ab")
        selected_tools = [tool.tool_name for tool in selection.selected_tools] if selection else []
        
        # Check if test passed
        passed = True
        issues = []
        
        # Check tool selection
        if test_case['expected_tools']:
            # At least one expected tool should be selected
            if not any(expected in selected_tools for expected in test_case['expected_tools']):
                passed = False
                issues.append(f"Expected tools {test_case['expected_tools']}, got {selected_tools}")
        else:
            # No tools should be selected
            if selected_tools:
                passed = False
                issues.append(f"Expected no tools, but got {selected_tools}")
        
        # Print results
        print(f"✅ SUCCESS" if passed else f"❌ FAILED")
        print(f"Duration: {duration:.0f}ms")
        print(f"Tools Selected: {selected_tools if selected_tools else 'None (information-only)'}")
        print(f"Response: {result.response.message[:200]}...")
        print(f"Confidence: {selection.selection_confidence:.2f}" if selection else "N/A")
        print(f"Next Stage: {selection.next_stage}" if selection else "N/A")
        
        if not passed:
            print(f"\n⚠️  Issues:")
            for issue in issues:
                print(f"   - {issue}")
        
        return {
            "name": test_case['name'],
            "passed": passed,
            "duration_ms": duration,
            "tools_selected": selected_tools,
            "response": result.response.message,
            "issues": issues
        }
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        print(f"❌ ERROR: {str(e)}")
        print(f"Duration: {duration:.0f}ms")
        
        return {
            "name": test_case['name'],
            "passed": False,
            "duration_ms": duration,
            "tools_selected": [],
            "response": None,
            "issues": [f"Exception: {str(e)}"]
        }


async def run_all_tests():
    """Run all test cases"""
    print("="*80)
    print("PIPELINE V2 TEST SUITE")
    print("="*80)
    print(f"Testing {len(TEST_CASES)} scenarios...")
    
    # Initialize orchestrator
    print("\n🔧 Initializing Pipeline V2...")
    llm_client = get_default_llm_client()
    await llm_client.connect()
    
    orchestrator = PipelineOrchestratorV2(llm_client)
    await orchestrator.initialize()
    
    # Check health
    print("🏥 Running health check...")
    health = await orchestrator.health_check()
    print(f"   Orchestrator: {health['orchestrator']}")
    print(f"   LLM: {health.get('llm', 'unknown')}")
    
    if health['orchestrator'] != 'healthy':
        print("❌ Health check failed! Aborting tests.")
        return
    
    print("✅ Health check passed\n")
    
    # Run tests
    results = []
    for test_case in TEST_CASES:
        result = await test_single_request(orchestrator, test_case)
        results.append(result)
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    success_rate = (passed_count / total_count) * 100
    
    print(f"Total Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Average duration
    avg_duration = sum(r['duration_ms'] for r in results) / len(results)
    print(f"Average Duration: {avg_duration:.0f}ms")
    
    # Failed tests
    failed_tests = [r for r in results if not r['passed']]
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test['name']}")
            for issue in test['issues']:
                print(f"     • {issue}")
    else:
        print(f"\n✅ All tests passed!")
    
    # Get orchestrator metrics
    print(f"\n{'='*80}")
    print("ORCHESTRATOR METRICS")
    print(f"{'='*80}")
    metrics = orchestrator.get_metrics()
    print(json.dumps(metrics, indent=2))
    
    return success_rate == 100.0


async def main():
    """Main entry point"""
    try:
        success = await run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())