#!/usr/bin/env python3
"""
Simple test for clarification system
"""

import asyncio
import json
import aiohttp

async def test_simple_request():
    """Test with a simple request that should definitely need clarification"""
    
    # Test a request that's missing critical information
    request = {
        "message": "create a recurring job to monitor SFP values",
        "conversation_id": "test-simple-001",
        "user_id": 1
    }
    
    print("🧪 Testing Simple Clarification")
    print("=" * 40)
    print(f"Request: {request['message']}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:3005/ai/chat",
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Status: {response.status}")
                    print(f"📋 Intent: {result.get('intent', 'unknown')}")
                    print(f"🎯 Confidence: {result.get('confidence', 0):.2%}")
                    print(f"🤔 Clarification Needed: {result.get('clarification_needed', False)}")
                    print()
                    print(f"📝 Response: {result.get('response', 'No response')}")
                    print()
                    
                    if result.get('clarifying_questions'):
                        print("🔍 Clarifying Questions:")
                        for i, question in enumerate(result.get('clarifying_questions', []), 1):
                            print(f"   {i}. {question}")
                        print()
                    
                    if result.get('missing_information'):
                        print("📊 Missing Information:")
                        for i, info in enumerate(result.get('missing_information', []), 1):
                            print(f"   {i}. {info}")
                        print()
                        
                    # Print the full response for debugging
                    print("🔧 Full Response (for debugging):")
                    print(json.dumps(result, indent=2))
                        
                else:
                    print(f"❌ Request failed with status: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_request())