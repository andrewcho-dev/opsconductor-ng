#!/usr/bin/env python3

import asyncio
import httpx
import json

async def debug_job_creation():
    """Debug job creation process step by step"""
    
    test_request = {
        "message": "create a job that pings 192.168.50.210 every 10 seconds",
        "user_id": 1,
        "conversation_id": "debug_test"
    }
    
    print("🔍 Debugging job creation process...")
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
                
                # Check fulfillment result details
                fulfillment_result = result.get('fulfillment_result', {})
                if fulfillment_result:
                    print("\n🎯 Fulfillment Result Details:")
                    print(f"  Status: {fulfillment_result.get('status', 'Unknown')}")
                    print(f"  Steps Completed: {fulfillment_result.get('steps_completed', 0)}")
                    print(f"  Total Steps: {fulfillment_result.get('total_steps', 0)}")
                    print(f"  Error Message: {fulfillment_result.get('error_message', 'None')}")
                    print(f"  Execution Summary: {fulfillment_result.get('execution_summary', 'None')}")
                    
                    # Check execution logs
                    execution_logs = fulfillment_result.get('execution_logs', [])
                    if execution_logs:
                        print("\n📋 Execution Logs:")
                        for i, log in enumerate(execution_logs):
                            print(f"  {i+1}. {log}")
                    
                    # Check job details
                    job_details = fulfillment_result.get('job_details', [])
                    if job_details:
                        print("\n📋 Job Details in Fulfillment Result:")
                        for i, job_detail in enumerate(job_details):
                            print(f"  Job {i+1}:")
                            print(f"    Step: {job_detail.get('step_name', 'Unknown')}")
                            print(f"    Job Name: {job_detail.get('job_name', 'Unknown')}")
                            print(f"    Job ID: {job_detail.get('job_id', 'N/A')}")
                            print(f"    Execution ID: {job_detail.get('execution_id', 'N/A')}")
                    else:
                        print("\n❌ No job details found in fulfillment result")
                
                # Check top-level job details
                top_level_job_details = result.get('job_details', [])
                if top_level_job_details:
                    print("\n📋 Top-Level Job Details:")
                    for i, job_detail in enumerate(top_level_job_details):
                        print(f"  Job {i+1}:")
                        print(f"    Step: {job_detail.get('step_name', 'Unknown')}")
                        print(f"    Job Name: {job_detail.get('job_name', 'Unknown')}")
                        print(f"    Job ID: {job_detail.get('job_id', 'N/A')}")
                        print(f"    Execution ID: {job_detail.get('execution_id', 'N/A')}")
                else:
                    print("\n❌ No top-level job details found")
                
                # Check other fields
                print(f"\n🆔 Top-level Job ID: {result.get('job_id', 'None')}")
                print(f"🔄 Top-level Execution ID: {result.get('execution_id', 'None')}")
                print(f"🤖 Automation Job ID: {result.get('automation_job_id', 'None')}")
                
                return True
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Debug failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_job_creation())
    if success:
        print("\n🎉 Debug completed!")
    else:
        print("\n💥 Debug failed!")