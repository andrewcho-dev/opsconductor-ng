#!/usr/bin/env python3
"""
Test script for the new Confidence-Driven Clarification System
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from pipeline.orchestrator import get_pipeline_orchestrator
from pipeline.schemas.response_v1 import ResponseType

async def test_clarification_system():
    """Test the clarification system with various confidence scenarios."""
    
    print("🧠 Testing Confidence-Driven Clarification System")
    print("=" * 60)
    
    # Get orchestrator
    orchestrator = await get_pipeline_orchestrator()
    
    # Test cases with different confidence levels
    test_cases = [
        {
            "name": "High Confidence Request",
            "request": "restart the nginx service on web-server-01",
            "expected": "Should proceed normally"
        },
        {
            "name": "Low Confidence Request - Vague",
            "request": "fix the database problem",
            "expected": "Should ask for clarification"
        },
        {
            "name": "Low Confidence Request - Ambiguous",
            "request": "check the thing",
            "expected": "Should ask for clarification"
        },
        {
            "name": "Medium Confidence Request",
            "request": "show me the database status",
            "expected": "Might proceed or ask for clarification"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Request: '{test_case['request']}'")
        print(f"Expected: {test_case['expected']}")
        print("-" * 40)
        
        try:
            # Process the request
            result = await orchestrator.process_request(test_case['request'])
            
            # Analyze the result
            print(f"✅ Success: {result.success}")
            print(f"📊 Response Type: {result.response.response_type}")
            print(f"🎯 Confidence: {result.response.confidence}")
            print(f"❓ Needs Clarification: {result.needs_clarification}")
            
            if result.needs_clarification:
                print(f"🔄 Clarification Message: {result.response.message[:200]}...")
                if hasattr(result.response, 'metadata') and result.response.metadata:
                    print(f"📈 Attempt: {result.response.metadata.get('clarification_attempt', 'N/A')}")
                    print(f"🎯 Threshold: {result.response.metadata.get('confidence_threshold', 'N/A')}")
            
            # Show Stage A confidence details
            if "stage_a" in result.intermediate_results:
                stage_a = result.intermediate_results["stage_a"]
                print(f"🧠 Stage A Confidence: {stage_a.overall_confidence:.3f}")
                print(f"📋 Intent: {stage_a.intent.category}/{stage_a.intent.action}")
                print(f"🏷️  Entities Found: {len(stage_a.entities)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
    
    print("🎉 Clarification System Test Complete!")

async def test_clarification_loop():
    """Test the clarification loop with multiple attempts."""
    
    print("\n🔄 Testing Clarification Loop (Multiple Attempts)")
    print("=" * 60)
    
    orchestrator = await get_pipeline_orchestrator()
    
    # Start with a very vague request
    request = "do something"
    context = {}
    
    for attempt in range(1, 5):  # Test up to 4 attempts
        print(f"\n🔄 Attempt {attempt}")
        print(f"Request: '{request}'")
        print("-" * 30)
        
        try:
            result = await orchestrator.process_request(request, context=context)
            
            print(f"Response Type: {result.response.response_type}")
            print(f"Needs Clarification: {result.needs_clarification}")
            
            if result.needs_clarification:
                print(f"Clarification Message: {result.response.message[:150]}...")
                # Update context for next attempt
                context = result.response.metadata or {}
            else:
                print("✅ System proceeded with the request!")
                break
                
            if result.response.response_type == ResponseType.ERROR:
                print("🛑 System refused to proceed after max attempts")
                break
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            break

if __name__ == "__main__":
    asyncio.run(test_clarification_system())
    asyncio.run(test_clarification_loop())