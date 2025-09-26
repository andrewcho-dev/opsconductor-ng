#!/usr/bin/env python3
"""
Test Realistic Clarification Flow

This script tests the conversation context with a more realistic scenario
where the AI actually asks for clarification and then processes the response.
"""

import asyncio
import logging
import sys
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

class RealisticMockLLMEngine:
    """Mock LLM engine that simulates realistic clarification flow"""
    
    def __init__(self):
        self.default_model = "test_model"
        self.step_counter = 0
    
    async def generate(self, prompt: str) -> dict:
        """Mock generate method that simulates realistic LLM responses"""
        
        # Simulate clarification detection responses
        if "Does this look like a clarification response" in prompt:
            user_message = ""
            if '"' in prompt:
                parts = prompt.split('"')
                if len(parts) >= 2:
                    user_message = parts[1].lower()
            
            # Realistic clarification detection
            clarification_indicators = [
                "building a", "building b", "every", "minutes", "above", "below", 
                "all cameras", "all servers", "in building", "at", "when", "if"
            ]
            
            is_clarification = any(indicator in user_message for indicator in clarification_indicators)
            response = "YES" if is_clarification else "NO"
            return {"generated_text": response}
        
        # Simulate execution planning responses
        elif "create a step-by-step execution plan" in prompt:
            if "firmware version" in prompt.lower() and "building a" not in prompt.lower():
                # First request - ask for clarification
                return {
                    "generated_text": """ANALYSIS: User wants to check firmware version on Axis cameras but didn't specify which cameras or location.

EXECUTION PLAN:
Step 1: Ask for clarification - Which specific cameras or location?

EXPECTED OUTCOME: User will provide more specific information about which cameras to check."""
                }
            elif "firmware version" in prompt.lower() and "building a" in prompt.lower():
                # Combined request with clarification
                return {
                    "generated_text": """ANALYSIS: User wants to check firmware version on Axis cameras in Building A (clarification provided).

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
        
        # Simulate step-by-step execution responses
        elif "What should I do next" in prompt:
            self.step_counter += 1
            
            if "ask for clarification" in prompt.lower():
                return {
                    "generated_text": """ACTION: ASK_CLARIFICATION
QUESTION: Which specific cameras would you like me to check? Please specify:
- All cameras in a specific building (e.g., "Building A")  
- Cameras in a specific area (e.g., "lobby cameras")
- All cameras in the entire network

This will help me target the right devices for firmware checking."""
                }
            elif self.step_counter == 1:
                return {
                    "generated_text": """ACTION: CALL_SERVICE
SERVICE: asset
METHOD: get_all_assets
PARAMETERS: {"filter": {"type": "axis_camera", "location": "Building A"}}
REASON: Getting list of Axis cameras in Building A to check firmware versions"""
                }
            elif self.step_counter == 2:
                return {
                    "generated_text": """ACTION: CALL_SERVICE
SERVICE: automation
METHOD: submit_ai_workflow
PARAMETERS: {"workflow": {"steps": [{"action": "vapix_firmware_check", "targets": ["192.168.1.101", "192.168.1.102"]}]}}
REASON: Executing firmware version check on identified cameras"""
                }
            else:
                return {
                    "generated_text": """ACTION: COMPLETE
RESULT: Successfully checked firmware versions on 2 Axis cameras in Building A
SUMMARY: All cameras are running firmware version 10.12.196"""
                }
        
        # Default response
        return {"generated_text": "Mock LLM response for testing"}

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
            }
        ]

async def test_realistic_clarification_flow():
    """Test the complete clarification flow"""
    
    print("🧪 Testing Realistic Clarification Flow")
    print("=" * 60)
    
    try:
        # Initialize components
        llm_engine = RealisticMockLLMEngine()
        automation_client = MockAutomationClient()
        asset_client = MockAssetClient()
        
        direct_executor = DirectExecutor(
            llm_engine=llm_engine,
            automation_client=automation_client,
            asset_client=asset_client
        )
        
        conversation_id = f"test_clarification_{int(datetime.now().timestamp())}"
        user_context = {
            "user_id": "test_user",
            "conversation_id": conversation_id
        }
        
        print(f"📝 Using conversation ID: {conversation_id}")
        print()
        
        # Step 1: Initial ambiguous request
        print("🔍 STEP 1: Initial ambiguous request")
        print("-" * 40)
        
        initial_request = "check firmware version on all axis cameras"
        print(f"User: {initial_request}")
        
        result1 = await direct_executor.execute_user_request(initial_request, user_context)
        
        print(f"AI Response: {result1.get('message', 'No message')}")
        print(f"Status: {result1.get('status', 'Unknown')}")
        
        # Check if awaiting clarification was set
        if conversation_id in direct_executor.conversation_contexts:
            context = direct_executor.conversation_contexts[conversation_id]
            awaiting = context.get("awaiting_clarification", False)
            print(f"Awaiting clarification: {awaiting}")
            if awaiting:
                print(f"Original request stored: {context.get('original_request', 'None')}")
        
        print()
        
        # Step 2: Provide clarification
        print("🔍 STEP 2: Provide clarification")
        print("-" * 40)
        
        clarification = "all cameras in building A"
        print(f"User: {clarification}")
        
        result2 = await direct_executor.execute_user_request(clarification, user_context)
        
        print(f"AI Response: {result2.get('message', 'No message')}")
        print(f"Status: {result2.get('status', 'Unknown')}")
        print()
        
        # Step 3: Verify conversation context
        print("🔍 STEP 3: Conversation context verification")
        print("-" * 40)
        
        if conversation_id in direct_executor.conversation_contexts:
            context = direct_executor.conversation_contexts[conversation_id]
            print(f"✅ Conversation context found:")
            print(f"   History entries: {len(context.get('history', []))}")
            print(f"   Awaiting clarification: {context.get('awaiting_clarification', False)}")
            
            # Show the conversation history
            for i, interaction in enumerate(context.get('history', []), 1):
                print(f"   Interaction {i}:")
                print(f"     User: {interaction['user_message'][:80]}...")
                print(f"     Status: {interaction['execution_result'].get('status', 'Unknown')}")
        else:
            print("❌ No conversation context found")
        
        print()
        print("✅ Realistic clarification flow testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")

async def main():
    """Run the realistic clarification flow test"""
    await test_realistic_clarification_flow()

if __name__ == "__main__":
    asyncio.run(main())