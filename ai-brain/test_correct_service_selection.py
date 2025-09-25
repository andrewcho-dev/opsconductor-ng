#!/usr/bin/env python3
"""
Test LLM Service Selection - Verify LLM chooses correct services
"""

import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain')

from fulfillment_engine.fulfillment_engine import FulfillmentEngine, FulfillmentRequest
from fulfillment_engine.intent_processor import IntentType, RiskLevel
import uuid
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_llm_service_selection():
    """Test that LLM correctly selects network-analytics-probe for ping operations"""
    
    print("🧠 Testing LLM Service Selection for Ping Operations")
    print("=" * 60)
    
    try:
        # Initialize fulfillment engine
        engine = FulfillmentEngine()
        
        # Test ping request - LLM should choose network-analytics-probe
        user_message = "create a job that pings 192.168.50.210 every 10 seconds"
        
        print(f"📝 User Request: {user_message}")
        print()
        
        # Create fulfillment request
        request = FulfillmentRequest(
            request_id=str(uuid.uuid4()),
            user_intent=user_message,
            user_message=user_message,
            timestamp=datetime.now()
        )
        
        # Process the request
        print("🔄 Processing request through fulfillment engine...")
        result = await engine.fulfill_intent(request)
        
        print(f"✅ Processing completed!")
        print(f"📊 Result: {result}")
        print()
        
        # Check if we got a workflow
        if hasattr(result, 'workflow') and result.workflow:
            print("🎯 LLM Generated Workflow:")
            print(f"   Workflow ID: {result.workflow.workflow_id}")
            print(f"   Steps: {len(result.workflow.steps)}")
            
            for i, step in enumerate(result.workflow.steps, 1):
                print(f"   Step {i}: {step.name}")
                print(f"     Command: {step.command}")
                print(f"     Service: {step.service_name}")
                print(f"     Parameters: {step.parameters}")
                print()
                
                # Check if LLM chose the correct service for network operations
                if 'ping' in step.command.lower():
                    if step.service_name == 'network-analytics-probe':
                        print("✅ SUCCESS: LLM correctly chose network-analytics-probe for ping!")
                    elif step.service_name == 'automation-service':
                        print("❌ ISSUE: LLM chose automation-service instead of network-analytics-probe")
                    else:
                        print(f"⚠️  UNEXPECTED: LLM chose {step.service_name} for ping operation")
        else:
            print("❌ No workflow generated")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_service_selection())