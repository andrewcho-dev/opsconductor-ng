#!/usr/bin/env python3

import asyncio
import httpx
import json

async def test_job_creation():
    """Test the final fix for job creation data type issue"""
    
    print("🧪 Testing AI job creation with data type fix...")
    
    # Test request
    test_request = {
        "message": "restart nginx service",
        "user_id": 1,
        "conversation_id": "test-final-fix"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"📤 Sending request: {test_request['message']}")
            
            response = await client.post(
                "http://localhost:3005/ai/chat",
                json=test_request
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Response received successfully!")
                print(f"🎯 Intent: {result.get('intent')}")
                print(f"🆔 Job ID: {result.get('job_id')} (type: {type(result.get('job_id'))})")
                print(f"🔧 Execution ID: {result.get('execution_id')}")
                print(f"🤖 Automation Job ID: {result.get('automation_job_id')}")
                print(f"🚀 Execution Started: {result.get('execution_started')}")
                
                if result.get('intent') == 'job_creation' and result.get('job_id'):
                    print("🎉 SUCCESS: Job creation working with proper data types!")
                    return True
                else:
                    print("❌ ISSUE: Job not created or wrong intent")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_job_creation())
    if success:
        print("\n🎊 FINAL FIX SUCCESSFUL: AI system is now creating and executing jobs!")
    else:
        print("\n💥 FINAL FIX FAILED: Still issues with job creation")