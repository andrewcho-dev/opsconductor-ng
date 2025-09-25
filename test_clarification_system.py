#!/usr/bin/env python3
"""
Test script for the enhanced clarification system in the 4W Framework
"""

import asyncio
import json
import aiohttp
import sys

async def test_clarification_system():
    """Test the clarification system with the SFP monitoring request"""
    
    # Test the original request that should trigger clarification
    original_request = {
        "message": "i would like you to create a recurring job that runs every hour and checks the sfp rx and tx strength values from the ciena switch located at 10.127.0.130. you will use ssh to connect to the switch.",
        "conversation_id": "test-clarification-001",
        "user_id": 1
    }
    
    print("🧪 Testing Clarification System")
    print("=" * 50)
    print(f"Original Request: {original_request['message']}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Send the original request
            print("📤 Sending original request...")
            async with session.post(
                "http://localhost:3005/ai/chat",
                json=original_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Response Status: {response.status}")
                    print(f"📋 Response Intent: {result.get('intent', 'unknown')}")
                    print(f"🎯 Confidence: {result.get('confidence', 0):.2%}")
                    print()
                    
                    # Check if clarification was requested
                    if result.get('clarification_needed', False):
                        print("🤔 CLARIFICATION REQUESTED!")
                        print(f"📝 Response: {result.get('response', 'No response')}")
                        print()
                        print("🔍 Clarifying Questions:")
                        for i, question in enumerate(result.get('clarifying_questions', []), 1):
                            print(f"   {i}. {question}")
                        print()
                        print("📊 Missing Information:")
                        for i, info in enumerate(result.get('missing_information', []), 1):
                            print(f"   {i}. {info}")
                        print()
                        
                        # Test follow-up with clarification
                        follow_up_request = {
                            "message": "Alert me when RX power is below -15 dBm or TX power is above 5 dBm. Also notify if either value changes by more than 3 dBm from baseline.",
                            "conversation_id": original_request["conversation_id"],
                            "user_id": original_request["user_id"]
                        }
                        
                        print("📤 Sending follow-up with clarification...")
                        print(f"Follow-up: {follow_up_request['message']}")
                        print()
                        
                        async with session.post(
                            "http://localhost:3005/ai/chat",
                            json=follow_up_request,
                            headers={"Content-Type": "application/json"}
                        ) as follow_response:
                            if follow_response.status == 200:
                                follow_result = await follow_response.json()
                                print(f"✅ Follow-up Status: {follow_response.status}")
                                print(f"📋 Follow-up Intent: {follow_result.get('intent', 'unknown')}")
                                print(f"🎯 Follow-up Confidence: {follow_result.get('confidence', 0):.2%}")
                                print(f"📝 Follow-up Response: {follow_result.get('response', 'No response')}")
                                
                                # Check if still needs clarification
                                if follow_result.get('clarification_needed', False):
                                    print("🤔 Still needs clarification:")
                                    for question in follow_result.get('clarifying_questions', []):
                                        print(f"   • {question}")
                                else:
                                    print("✅ Clarification complete - ready to proceed!")
                            else:
                                print(f"❌ Follow-up failed with status: {follow_response.status}")
                                error_text = await follow_response.text()
                                print(f"Error: {error_text}")
                    else:
                        print("ℹ️  No clarification requested - proceeding directly")
                        print(f"📝 Response: {result.get('response', 'No response')}")
                        
                else:
                    print(f"❌ Request failed with status: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Starting Clarification System Test")
    print("Waiting for AI Brain service to be ready...")
    
    # Wait a moment for the service to be fully ready
    import time
    time.sleep(3)
    
    asyncio.run(test_clarification_system())