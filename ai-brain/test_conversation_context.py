#!/usr/bin/env python3
"""
Test Conversation Context Handling in DirectExecutor

This script tests the new conversation context functionality to ensure
that Ollama can properly handle clarification responses and maintain
conversation history.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the ai-brain directory to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

from fulfillment_engine.direct_executor import DirectExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockLLMEngine:
    """Mock LLM engine for testing conversation context"""
    
    def __init__(self):
        self.default_model = "test_model"
    
    async def generate(self, prompt: str) -> dict:
        """Mock generate method that simulates LLM responses"""
        
        # Simulate clarification detection responses
        if "Does this look like a clarification response" in prompt:
            user_message = ""
            if '"' in prompt:
                # Extract user message from prompt
                parts = prompt.split('"')
                if len(parts) >= 2:
                    user_message = parts[1].lower()
            
            # Simple heuristics for testing
            clarification_indicators = [
                "building a", "building b", "every", "minutes", "above", "below", 
                "all cameras", "all servers", "in building", "at", "when", "if"
            ]
            
            is_clarification = any(indicator in user_message for indicator in clarification_indicators)
            
            # Simulate some non-clarification cases
            non_clarification_indicators = [
                "weather", "show me", "what is", "instead", "different"
            ]
            
            if any(indicator in user_message for indicator in non_clarification_indicators):
                is_clarification = False
            
            response = "YES" if is_clarification else "NO"
            return {"generated_text": response}
        
        # Simulate execution planning responses
        elif "create a step-by-step execution plan" in prompt:
            if "firmware version" in prompt.lower():
                return {
                    "generated_text": """ANALYSIS: User wants to check firmware version on Axis cameras with specific location clarification.

EXECUTION PLAN:
Step 1: Asset Service - Get all Axis cameras in Building A
Step 2: VAPIX Service - Check firmware version on each camera using firmwaremanagement.cgi
Step 3: Automation Service - Compile results and format response

EXPECTED OUTCOME: User will see firmware version information for all Axis cameras in Building A."""
                }
            else:
                return {
                    "generated_text": """ANALYSIS: User wants to perform a general IT operation.

EXECUTION PLAN:
Step 1: Asset Service - Identify target systems
Step 2: Automation Service - Execute requested operation

EXPECTED OUTCOME: Operation completed successfully."""
                }
        
        # Default response
        return {"generated_text": "Mock LLM response for testing"}
    
    async def chat(self, message: str, system_prompt: str = None) -> dict:
        """Mock chat method"""
        return await self.generate(f"{system_prompt}\n\nUser: {message}" if system_prompt else message)

class MockAutomationClient:
    """Mock automation client for testing"""
    async def submit_ai_workflow(self, workflow, job_name=None, user_context=None):
        return {
            "job_id": "test_job_123",
            "execution_id": "test_exec_456",
            "status": "submitted"
        }

class MockAssetClient:
    """Mock asset client for testing"""
    async def get_all_assets(self):
        return [
            {
                "id": "camera_001",
                "name": "Building A Camera 1",
                "ip_address": "192.168.1.101",
                "type": "axis_camera",
                "location": "Building A - Lobby"
            },
            {
                "id": "camera_002", 
                "name": "Building A Camera 2",
                "ip_address": "192.168.1.102",
                "type": "axis_camera",
                "location": "Building A - Hallway"
            },
            {
                "id": "camera_003",
                "name": "Building B Camera 1", 
                "ip_address": "192.168.1.201",
                "type": "axis_camera",
                "location": "Building B - Entrance"
            }
        ]

async def test_conversation_context():
    """Test conversation context handling"""
    
    print("🧪 Testing Conversation Context Handling")
    print("=" * 60)
    
    try:
        # Initialize components
        llm_engine = MockLLMEngine()
        automation_client = MockAutomationClient()
        asset_client = MockAssetClient()
        
        direct_executor = DirectExecutor(
            llm_engine=llm_engine,
            automation_client=automation_client,
            asset_client=asset_client
        )
        
        conversation_id = f"test_conv_{int(datetime.now().timestamp())}"
        
        print(f"📝 Using conversation ID: {conversation_id}")
        print()
        
        # Test 1: Initial request that should trigger clarification
        print("🔍 TEST 1: Initial request (should ask for clarification)")
        print("-" * 40)
        
        initial_request = "check firmware version on all axis cameras"
        user_context = {
            "user_id": "test_user",
            "conversation_id": conversation_id
        }
        
        print(f"User: {initial_request}")
        
        result1 = await direct_executor.execute_user_request(initial_request, user_context)
        
        print(f"AI Response: {result1.get('message', 'No message')}")
        print(f"Status: {result1.get('status', 'Unknown')}")
        print()
        
        # Test 2: Clarification response
        print("🔍 TEST 2: Clarification response (should combine with original)")
        print("-" * 40)
        
        clarification = "all cameras in building A"
        
        print(f"User: {clarification}")
        
        result2 = await direct_executor.execute_user_request(clarification, user_context)
        
        print(f"AI Response: {result2.get('message', 'No message')}")
        print(f"Status: {result2.get('status', 'Unknown')}")
        print()
        
        # Test 3: Check conversation context storage
        print("🔍 TEST 3: Conversation context verification")
        print("-" * 40)
        
        if conversation_id in direct_executor.conversation_contexts:
            context = direct_executor.conversation_contexts[conversation_id]
            print(f"✅ Conversation context found:")
            print(f"   History entries: {len(context.get('history', []))}")
            print(f"   Awaiting clarification: {context.get('awaiting_clarification', False)}")
            print(f"   Original request: {context.get('original_request', 'None')}")
            
            if context.get('history'):
                print(f"   Last interaction:")
                last = context['history'][-1]
                print(f"     User: {last['user_message'][:100]}...")
                print(f"     Result: {last['execution_result'].get('status', 'Unknown')}")
        else:
            print("❌ No conversation context found")
        
        print()
        
        # Test 4: New unrelated request (should reset context)
        print("🔍 TEST 4: New unrelated request (should reset context)")
        print("-" * 40)
        
        new_request = "show me all servers"
        
        print(f"User: {new_request}")
        
        result3 = await direct_executor.execute_user_request(new_request, user_context)
        
        print(f"AI Response: {result3.get('message', 'No message')}")
        print(f"Status: {result3.get('status', 'Unknown')}")
        print()
        
        print("✅ Conversation context testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")

async def test_clarification_detection():
    """Test the clarification detection logic specifically"""
    
    print("🧪 Testing Clarification Detection Logic")
    print("=" * 60)
    
    try:
        llm_engine = MockLLMEngine()
        direct_executor = DirectExecutor(llm_engine=llm_engine)
        
        # Test cases for clarification detection
        test_cases = [
            {
                "original": "check firmware version on all axis cameras",
                "response": "all cameras in building A",
                "expected": True,
                "description": "Location specification"
            },
            {
                "original": "monitor CPU usage",
                "response": "every 5 minutes",
                "expected": True,
                "description": "Timing specification"
            },
            {
                "original": "create backup job",
                "response": "alert when disk usage is above 80%",
                "expected": True,
                "description": "Threshold specification"
            },
            {
                "original": "check server status",
                "response": "show me all network devices instead",
                "expected": False,
                "description": "Completely different request"
            },
            {
                "original": "restart nginx service",
                "response": "what is the weather today?",
                "expected": False,
                "description": "Unrelated question"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i}: {test_case['description']}")
            print(f"  Original: {test_case['original']}")
            print(f"  Response: {test_case['response']}")
            print(f"  Expected: {'Clarification' if test_case['expected'] else 'New Request'}")
            
            # Create mock stored context
            stored_context = {
                "original_request": test_case['original'],
                "missing_information": ["location", "timing", "scope"]
            }
            
            # Test detection
            is_clarification = await direct_executor._detect_clarification_response(
                test_case['response'], 
                stored_context
            )
            
            result = "✅ PASS" if is_clarification == test_case['expected'] else "❌ FAIL"
            detected = "Clarification" if is_clarification else "New Request"
            
            print(f"  Detected: {detected}")
            print(f"  Result: {result}")
            print()
        
        print("✅ Clarification detection testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Clarification detection test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")

async def main():
    """Run all conversation context tests"""
    
    print("🚀 Starting Conversation Context Tests")
    print("=" * 80)
    print()
    
    # Test 1: Basic conversation context handling
    await test_conversation_context()
    print()
    
    # Test 2: Clarification detection logic
    await test_clarification_detection()
    print()
    
    print("🎉 All conversation context tests completed!")

if __name__ == "__main__":
    asyncio.run(main())