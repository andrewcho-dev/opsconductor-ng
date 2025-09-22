#!/usr/bin/env python3
"""
Test real job creation with the fixed automation service connection
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_real_job_creation():
    """Test actual job creation through the AI brain API"""
    
    # Test data
    test_request = {
        "message": "restart nginx service on server1",
        "user_id": "test_user",
        "conversation_id": "test_conversation_123"
    }
    
    print(f"🧪 Testing real job creation at {datetime.now()}")
    print(f"📝 Request: {test_request['message']}")
    
    try:
        # Make request to AI brain service
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("🔗 Connecting to AI brain service at http://localhost:3005...")
            
            response = await client.post(
                "http://localhost:3005/chat",
                json=test_request
            )
            
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Response received:")
                print(f"   Response: {result.get('response', 'No response')}")
                print(f"   Intent: {result.get('intent', 'Unknown')}")
                print(f"   Confidence: {result.get('confidence', 'Unknown')}")
                print(f"   Job ID: {result.get('job_id', 'None')}")
                print(f"   Execution ID: {result.get('execution_id', 'None')}")
                print(f"   Automation Job ID: {result.get('automation_job_id', 'None')}")
                print(f"   Execution Started: {result.get('execution_started', False)}")
                
                # Check if it's a real job creation
                if result.get('job_id') and result.get('execution_id'):
                    print("🎉 REAL JOB CREATED AND STARTED!")
                    print(f"   Real Job ID: {result.get('job_id')}")
                    print(f"   Real Execution ID: {result.get('execution_id')}")
                    
                    # Check workflow details
                    workflow = result.get('workflow')
                    if workflow:
                        print(f"   Workflow Type: {workflow.get('workflow_type', 'Unknown')}")
                        print(f"   Steps Count: {len(workflow.get('steps', []))}")
                        print(f"   Risk Level: {workflow.get('risk_level', 'Unknown')}")
                else:
                    print("⚠️  Job creation response received but no real job IDs found")
                    print("   This might be a conversation response instead of job creation")
                
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_job_creation())