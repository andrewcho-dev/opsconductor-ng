#!/usr/bin/env python3

import asyncio
import httpx
import json

async def debug_workflow_simple():
    """Debug what workflow is being generated"""
    
    test_request = {
        "message": "execute echo hello on server",
        "user_id": 1,
        "conversation_id": "debug_simple"
    }
    
    print("🔍 Debugging simple workflow generation...")
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
                
                print("✅ Response received:")
                print(f"📝 Response Text: {result.get('response', 'No response text')}")
                
                # Print the full result for debugging
                print(f"\n🔍 Full Result Keys: {list(result.keys())}")
                
                # Check fulfillment result details
                fulfillment_result = result.get('fulfillment_result', {})
                if fulfillment_result:
                    print("\n🎯 Fulfillment Result Details:")
                    print(f"  Status: {fulfillment_result.get('status', 'Unknown')}")
                    print(f"  Error Message: {fulfillment_result.get('error_message', 'None')}")
                    print(f"  Request ID: {fulfillment_result.get('request_id', 'None')}")
                    print(f"  Workflow ID: {fulfillment_result.get('workflow_id', 'None')}")
                    print(f"  Steps Completed: {fulfillment_result.get('steps_completed', 0)}")
                    print(f"  Total Steps: {fulfillment_result.get('total_steps', 0)}")
                    
                    # Check execution logs
                    execution_logs = fulfillment_result.get('execution_logs', [])
                    if execution_logs:
                        print("\n📋 Execution Logs:")
                        for i, log in enumerate(execution_logs):
                            print(f"  {i+1}. {log}")
                    
                    # Check job details
                    job_details = fulfillment_result.get('job_details', [])
                    if job_details:
                        print("\n📋 Job Details:")
                        for i, job in enumerate(job_details):
                            print(f"  {i+1}. Job ID: {job.get('job_id', 'N/A')}")
                            print(f"      Execution ID: {job.get('execution_id', 'N/A')}")
                            print(f"      Job Name: {job.get('job_name', 'N/A')}")
                            print(f"      Step Name: {job.get('step_name', 'N/A')}")
                    else:
                        print("\n📋 Job Details: None (no jobs created)")
                
                # Check top-level job details
                top_level_job_details = result.get('job_details', [])
                if top_level_job_details:
                    print("\n📋 Top-Level Job Details:")
                    for i, job in enumerate(top_level_job_details):
                        print(f"  {i+1}. {job}")
                else:
                    print("\n📋 Top-Level Job Details: None")
                
                # Check automation job ID
                automation_job_id = result.get('automation_job_id')
                print(f"\n🤖 Automation Job ID: {automation_job_id}")
                
                # Check execution ID
                execution_id = result.get('execution_id')
                print(f"🔄 Execution ID: {execution_id}")
                
                # Check job ID
                job_id = result.get('job_id')
                print(f"📋 Job ID: {job_id}")
                
                return True
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Debug failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_workflow_simple())
    if success:
        print("\n🎉 Debug completed!")
    else:
        print("\n💥 Debug failed!")