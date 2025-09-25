#!/usr/bin/env python3
"""
Test the specific ping job creation flow that was broken
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the ai-brain directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brains.intent_brain.intent_brain import IntentBrain
from brains.intent_brain.intent_analyzer import IntentAnalyzer

# Mock LLM Engine that behaves like the real one
class MockLLMEngine:
    """Mock LLM engine that simulates real responses"""
    
    async def generate(self, prompt: str, **kwargs) -> dict:
        """Mock LLM response based on prompt content"""
        
        # Uncomment for debugging:
        # print(f"🤖 Mock LLM received prompt (first 200 chars): {prompt[:200]}...")
        
        # For clarification analysis - this is the key fix
        if "automation request" in prompt and "CLEAR" in prompt:
            # Extract the actual user request from the prompt
            if 'User request: "' in prompt:
                # Find the user request line
                user_request_start = prompt.find('User request: "') + len('User request: "')
                user_request_end = prompt.find('"', user_request_start)
                user_request = prompt[user_request_start:user_request_end]
                print(f"🤖 Extracted user request: '{user_request}'")
                
                # Now check the actual user request
                if user_request == "do something":
                    print("🤖 Mock LLM responding: UNCLEAR (vague request)")
                    return {"generated_text": "UNCLEAR\nWhat specific action would you like to perform?"}
                elif "ping 192.168.50.210 every 10 seconds" in user_request:
                    print("🤖 Mock LLM responding: CLEAR (ping request)")
                    return {"generated_text": "CLEAR"}
                elif "monitor disk space on server1" in user_request:
                    print("🤖 Mock LLM responding: CLEAR (disk monitoring)")
                    return {"generated_text": "CLEAR"}
                else:
                    print("🤖 Mock LLM responding: CLEAR (default)")
                    return {"generated_text": "CLEAR"}
            else:
                print("🤖 Mock LLM responding: CLEAR (no user request found)")
                return {"generated_text": "CLEAR"}
        
        # For intent understanding
        elif "What does this user want" in prompt:
            if "ping 192.168.50.210 every 10 seconds" in prompt:
                print("🤖 Mock LLM responding: Intent understanding (ping)")
                return {"generated_text": "The user wants to create a monitoring job that pings the IP address 192.168.50.210 every 10 seconds to check network connectivity and server availability."}
            else:
                print("🤖 Mock LLM responding: Intent understanding (generic)")
                return {"generated_text": "The user wants to perform some automation task."}
        
        # Default response
        print("🤖 Mock LLM responding: Default response")
        return {"generated_text": "Mock LLM response for testing purposes."}

async def test_ping_job_clarification_flow():
    """Test the specific ping job flow that was broken"""
    
    print("🧪 Testing Ping Job Creation Flow")
    print("=" * 60)
    
    # Initialize components
    print("🔧 Initializing Intent Brain with mock LLM...")
    mock_llm = MockLLMEngine()
    intent_brain = IntentBrain(llm_engine=mock_llm)
    
    print("✅ Components initialized successfully")
    
    # Test the exact message that was failing
    test_message = "create a job that pings 192.168.50.210 every 10 seconds"
    user_context = {
        "user_id": "test_user",
        "conversation_id": "test_conv_123"
    }
    
    print(f"\n📝 Testing message: '{test_message}'")
    print("🔍 This should NOT ask for clarification...")
    
    try:
        # This is the exact call that was failing before our fix
        intent_result = await intent_brain.analyze_intent(test_message, user_context)
        
        print(f"\n✅ Intent analysis completed successfully!")
        print(f"   User Intent: {intent_result.user_intent}")
        print(f"   Needs Clarification: {intent_result.needs_clarification}")
        print(f"   Processing Time: {intent_result.processing_time:.3f}s")
        
        if intent_result.needs_clarification:
            print(f"   ❌ ISSUE: Still asking for clarification!")
            print(f"   Questions: {intent_result.clarifying_questions}")
            return False
        else:
            print(f"   ✅ SUCCESS: No clarification needed - ready for fulfillment!")
            
        # Test the clarifying questions list is empty
        if intent_result.clarifying_questions:
            print(f"   ❌ ISSUE: Clarifying questions list should be empty but contains: {intent_result.clarifying_questions}")
            return False
        else:
            print(f"   ✅ SUCCESS: Clarifying questions list is empty as expected")
            
    except Exception as e:
        print(f"❌ Intent analysis failed: {e}")
        return False
    
    # Test a vague request to make sure clarification still works when needed
    print(f"\n🧪 Testing vague request (should ask for clarification)...")
    vague_message = "do something"
    
    try:
        vague_result = await intent_brain.analyze_intent(vague_message, user_context)
        
        if vague_result.needs_clarification:
            print(f"   ✅ SUCCESS: Vague request correctly asks for clarification")
            print(f"   Questions: {vague_result.clarifying_questions}")
        else:
            print(f"   ❌ ISSUE: Vague request should ask for clarification but doesn't")
            return False
            
    except Exception as e:
        print(f"❌ Vague request test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎯 PING JOB FLOW TEST COMPLETED!")
    print("✅ Clear requests proceed to fulfillment")
    print("✅ Vague requests still ask for clarification")
    print("✅ The fulfillment engine should now be reachable!")
    
    return True

async def test_intent_analyzer_directly():
    """Test the IntentAnalyzer component directly"""
    
    print("\n🧪 Testing IntentAnalyzer Component Directly")
    print("=" * 60)
    
    mock_llm = MockLLMEngine()
    analyzer = IntentAnalyzer(llm_engine=mock_llm)
    
    test_cases = [
        {
            "message": "create a job that pings 192.168.50.210 every 10 seconds",
            "should_be_clear": True,
            "description": "Ping job request"
        },
        {
            "message": "monitor disk space on server1",
            "should_be_clear": True,
            "description": "Disk monitoring request"
        },
        {
            "message": "do something",
            "should_be_clear": False,
            "description": "Vague request"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"📝 Message: '{test_case['message']}'")
        
        try:
            needs_clarification, questions = await analyzer.needs_clarification(test_case['message'])
            
            if test_case['should_be_clear']:
                if not needs_clarification:
                    print("   ✅ PASS: Clear request correctly identified")
                else:
                    print(f"   ❌ FAIL: Clear request incorrectly needs clarification: {questions}")
                    return False
            else:
                if needs_clarification:
                    print(f"   ✅ PASS: Vague request correctly needs clarification: {questions}")
                else:
                    print("   ❌ FAIL: Vague request incorrectly identified as clear")
                    return False
                    
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False
    
    print("\n✅ All IntentAnalyzer tests passed!")
    return True

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 TESTING THE FULFILLMENT ENGINE FIX")
    print("=" * 80)
    
    success1 = asyncio.run(test_ping_job_clarification_flow())
    success2 = asyncio.run(test_intent_analyzer_directly())
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 The fulfillment engine should now work correctly!")
        print("✅ Users can create jobs without unnecessary clarification requests")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🔧 The fix may need additional work")
        sys.exit(1)