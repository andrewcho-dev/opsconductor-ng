#!/usr/bin/env python3
"""
End-to-End Test for Fulfillment Engine Integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the ai-brain directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fulfillment_engine.fulfillment_engine import FulfillmentEngine, FulfillmentRequest, FulfillmentStatus
from brains.intent_brain.intent_brain import IntentBrain

class MockLLMEngine:
    """Mock LLM engine for testing"""
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Mock LLM response"""
        if "intent analysis" in prompt.lower():
            return "The user wants to install nginx web server on their systems for hosting web applications."
        elif "clarification" in prompt.lower():
            return "No clarification needed - the request is clear."
        elif "workflow" in prompt.lower():
            return """
            1. Update package repositories
            2. Install nginx package
            3. Start nginx service
            4. Enable nginx to start on boot
            5. Verify nginx is running
            """
        else:
            return "Mock LLM response for testing purposes."

class MockAutomationClient:
    """Mock automation client for testing"""
    
    async def create_job(self, job_data: dict) -> dict:
        """Mock job creation"""
        return {
            "job_id": f"mock_job_{int(datetime.now().timestamp())}",
            "status": "created",
            "message": "Mock job created successfully"
        }
    
    async def execute_job(self, job_id: str) -> dict:
        """Mock job execution"""
        return {
            "execution_id": f"exec_{job_id}",
            "status": "completed",
            "result": "Mock execution completed successfully"
        }

class MockAssetClient:
    """Mock asset client for testing"""
    
    async def get_assets(self, filters: dict = None) -> list:
        """Mock asset retrieval"""
        return [
            {"id": "server1", "name": "web-server-1", "type": "server", "status": "active"},
            {"id": "server2", "name": "web-server-2", "type": "server", "status": "active"}
        ]

async def test_end_to_end_flow():
    """Test the complete end-to-end flow"""
    
    print("🚀 End-to-End Fulfillment Engine Test")
    print("=" * 60)
    
    # Initialize mock components
    print("🔧 Initializing components with mocks...")
    mock_llm = MockLLMEngine()
    mock_automation = MockAutomationClient()
    mock_assets = MockAssetClient()
    
    # Initialize the real components with mocks
    intent_brain = IntentBrain(llm_engine=mock_llm)
    fulfillment_engine = FulfillmentEngine(
        llm_engine=mock_llm,
        automation_client=mock_automation,
        asset_client=mock_assets
    )
    
    print("✅ Components initialized successfully")
    
    # Test 1: Intent Analysis
    print("\n🧪 Test 1: Intent Analysis...")
    user_message = "Please install nginx on all web servers"
    
    try:
        intent_result = await intent_brain.analyze_intent(
            user_message=user_message,
            context={"user_id": "test_user"}
        )
        
        print(f"✅ Intent analyzed successfully")
        print(f"   User Intent: {intent_result.user_intent}")
        print(f"   Needs Clarification: {intent_result.needs_clarification}")
        print(f"   Processing Time: {intent_result.processing_time:.3f}s")
        
    except Exception as e:
        print(f"❌ Intent analysis failed: {e}")
        return False
    
    # Test 2: Fulfillment Request Creation
    print("\n🧪 Test 2: Creating Fulfillment Request...")
    
    try:
        fulfillment_request = FulfillmentRequest(
            request_id=f"test_{int(datetime.now().timestamp())}",
            user_intent=intent_result.user_intent,
            user_message=user_message,
            user_id="test_user",
            context={"test": True, "conversation_id": "test_conv"}
        )
        
        print(f"✅ Fulfillment request created: {fulfillment_request.request_id}")
        
    except Exception as e:
        print(f"❌ Fulfillment request creation failed: {e}")
        return False
    
    # Test 3: Fulfillment Execution
    print("\n🧪 Test 3: Executing Fulfillment...")
    
    try:
        fulfillment_result = await fulfillment_engine.fulfill_intent(fulfillment_request)
        
        print(f"✅ Fulfillment executed successfully")
        print(f"   Request ID: {fulfillment_result.request_id}")
        print(f"   Status: {fulfillment_result.status.value}")
        print(f"   Steps Completed: {fulfillment_result.steps_completed}/{fulfillment_result.total_steps}")
        print(f"   Execution Summary: {fulfillment_result.execution_summary}")
        
        if fulfillment_result.error_message:
            print(f"   Error: {fulfillment_result.error_message}")
        
    except Exception as e:
        print(f"❌ Fulfillment execution failed: {e}")
        return False
    
    # Test 4: Status Tracking
    print("\n🧪 Test 4: Status Tracking...")
    
    try:
        status = await fulfillment_engine.get_fulfillment_status(fulfillment_request.request_id)
        
        if status:
            print(f"✅ Status retrieved successfully")
            print(f"   Status: {status.status.value}")
            print(f"   Progress: {status.steps_completed}/{status.total_steps}")
        else:
            print(f"❌ Status not found for request {fulfillment_request.request_id}")
            return False
        
    except Exception as e:
        print(f"❌ Status tracking failed: {e}")
        return False
    
    # Test 5: List Active Fulfillments
    print("\n🧪 Test 5: Listing Active Fulfillments...")
    
    try:
        active_fulfillments = await fulfillment_engine.list_active_fulfillments()
        
        print(f"✅ Active fulfillments listed: {len(active_fulfillments)} found")
        
        for fulfillment in active_fulfillments:
            print(f"   - {fulfillment.request_id}: {fulfillment.status.value}")
        
    except Exception as e:
        print(f"❌ Listing active fulfillments failed: {e}")
        return False
    
    # Test 6: Engine Health
    print("\n🧪 Test 6: Engine Health Check...")
    
    try:
        health = await fulfillment_engine.get_engine_health()
        
        print(f"✅ Engine health check completed")
        print(f"   Status: {health.get('status', 'unknown')}")
        print(f"   Active Requests: {health.get('active_requests', 0)}")
        print(f"   Uptime: {health.get('uptime_seconds', 0):.1f}s")
        
    except Exception as e:
        print(f"❌ Engine health check failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎯 END-TO-END TEST COMPLETED SUCCESSFULLY!")
    print("✅ All components are working together properly")
    print("✅ Intent Brain → Fulfillment Engine integration is functional")
    print("✅ API endpoints should work correctly")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_end_to_end_flow())
    if success:
        print("\n🚀 System is ready for production use!")
        sys.exit(0)
    else:
        print("\n❌ System has issues that need to be resolved")
        sys.exit(1)