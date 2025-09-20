#!/usr/bin/env python3
"""
Test script for Job Engine functionality
"""
import requests
import json
import sys

def test_job_engine():
    """Test the Job Engine by creating a job from natural language"""
    
    # AI Brain service URL
    base_url = "http://localhost:3005"
    
    # Test health endpoint first
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
        print("✅ AI Brain service is healthy")
    except Exception as e:
        print(f"❌ Failed to connect to AI Brain service: {e}")
        return False
    
    # Test job creation endpoint
    test_request = {
        "natural_language": "Deploy the web application to production servers and restart nginx",
        "context": {
            "user_id": "test_user",
            "environment": "production"
        }
    }
    
    try:
        print("\n🚀 Testing Job Engine with natural language request...")
        print(f"Request: {test_request['natural_language']}")
        
        response = requests.post(
            f"{base_url}/ai/create-job",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Job creation successful!")
            print(f"📋 Job ID: {result.get('job_id', 'N/A')}")
            print(f"🎯 Intent: {result.get('intent', {}).get('type', 'N/A')}")
            print(f"🎯 Confidence: {result.get('intent', {}).get('confidence', 'N/A')}")
            print(f"🎯 Targets: {len(result.get('targets', []))} target(s) resolved")
            print(f"📝 Workflow: {len(result.get('workflow', {}).get('steps', []))} step(s)")
            print(f"⚡ Optimizations: {len(result.get('optimizations', []))} optimization(s)")
            print(f"📅 Execution Plan: {result.get('execution_plan', {}).get('strategy', 'N/A')}")
            return True
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing job creation: {e}")
        return False

if __name__ == "__main__":
    print("🧠 Testing OpsConductor AI Brain - Job Engine")
    print("=" * 50)
    
    success = test_job_engine()
    
    if success:
        print("\n🎉 Job Engine test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Job Engine test failed!")
        sys.exit(1)