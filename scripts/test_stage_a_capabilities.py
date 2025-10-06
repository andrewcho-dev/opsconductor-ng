#!/usr/bin/env python3
"""
Test Stage A Capability Detection with Database-Backed Capabilities

This test verifies that Stage A correctly identifies capabilities from the database
(not from an in-memory tool registry).
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.stages.stage_a.classifier import StageAClassifier
from llm.ollama_client import OllamaClient


TEST_CASES = [
    {
        "name": "Information-only request",
        "request": "What is a service mesh?",
        "expected_capabilities": [],
        "description": "Information requests should not require any capabilities"
    },
    {
        "name": "Asset query",
        "request": "Show me all production servers",
        "expected_capabilities": ["asset_query", "infrastructure_info", "resource_listing"],
        "description": "Asset queries should identify asset_query capability"
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


async def test_stage_a_capabilities():
    """Test that Stage A correctly identifies capabilities from database"""
    
    print("=" * 80)
    print("TESTING STAGE A CAPABILITY DETECTION (DATABASE-BACKED)")
    print("=" * 80)
    print()
    
    # Initialize LLM client
    ollama_config = {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
        "timeout": 120
    }
    
    try:
        llm_client = OllamaClient(ollama_config)
        await llm_client.connect()
        print("✅ Connected to Ollama LLM")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return False
    
    # Initialize Stage A Classifier
    try:
        classifier = StageAClassifier(llm_client)
        print("✅ Stage A Classifier initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize Stage A Classifier: {e}")
        return False
    
    # Run test cases
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"Test {i}/{len(TEST_CASES)}: {test_case['name']}")
        print(f"  Request: {test_case['request']}")
        print(f"  Expected: {test_case['expected_capabilities']}")
        
        try:
            # Classify the request
            decision = await classifier.classify(test_case['request'])
            
            # Extract capabilities
            capabilities = decision.intent.capabilities if decision.intent else []
            
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
            import traceback
            traceback.print_exc()
            failed += 1
        
        print()
    
    # Cleanup
    await llm_client.disconnect()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total: {len(TEST_CASES)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print()
    
    if failed > 0:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False
    else:
        print("🎉 All tests passed!")
        return True


if __name__ == "__main__":
    success = asyncio.run(test_stage_a_capabilities())
    sys.exit(0 if success else 1)