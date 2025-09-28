#!/usr/bin/env python3

import asyncio
import httpx
import json

async def test_ping_job():
    """Test creating a ping job and verify job details are returned"""
    
    # Test data
    test_request = {
        "message": "create a job that pings 192.168.50.210 every 10 seconds",
        "user_id": 1,
        "conversation_id": "test_conversation_123"
    }
    
    print("🧪 Testing ping job creation with job details...")
    print(f"📤 Request: {test_request['message']}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://ai-brain:3005/ai/chat",
                json=test_request
            )
            
            print(f"📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ SUCCESS! Response received:")
                print(f"📝 Response Text: {result.get('response', 'No response text')}")
                print(f"🆔 Job ID: {result.get('job_id', 'No job ID')}")
                print(f"🔄 Execution ID: {result.get('execution_id', 'No execution ID')}")
                print(f"🤖 Automation Job ID: {result.get('automation_job_id', 'No automation job ID')}")
                
                # Check for job details
                job_details = result.get('job_details', [])
                if job_details:
                    print("📋 Job Details Found:")
                    for i, job_detail in enumerate(job_details):
                        print(f"  Job {i+1}:")
                        print(f"    Step: {job_detail.get('step_name', 'Unknown')}")
                        print(f"    Job Name: {job_detail.get('job_name', 'Unknown')}")
                        print(f"    Job ID: {job_detail.get('job_id', 'N/A')}")
                        print(f"    Execution ID: {job_detail.get('execution_id', 'N/A')}")
                else:
                    print("❌ No job details found in response")
                
                # Check fulfillment result
                fulfillment_result = result.get('fulfillment_result', {})
                if fulfillment_result:
                    print(f"🎯 Fulfillment Status: {fulfillment_result.get('status', 'Unknown')}")
                    print(f"📊 Steps Completed: {fulfillment_result.get('steps_completed', 0)}/{fulfillment_result.get('total_steps', 0)}")
                
                return True
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ping_job())
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")