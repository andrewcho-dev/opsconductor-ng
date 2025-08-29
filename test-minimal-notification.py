#!/usr/bin/env python3
"""
Minimal notification test - bypass schema validation temporarily
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}:3001/login", json=ADMIN_CREDENTIALS)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to authenticate: {response.text}")
        sys.exit(1)

def test_direct_execution():
    """Test notification execution directly via executor service"""
    print("Testing direct notification execution...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test direct execution of notification step
    step_data = {
        "type": "notify.email",
        "recipients": ["test@example.com"],
        "subject_template": "Test from OpsConductor",
        "body_template": "This is a test notification from {{ job.name }}."
    }
    
    execution_request = {
        "job_id": 999,  # Test job ID
        "run_id": 999,  # Test run ID
        "step_idx": 0,
        "step": step_data,
        "context": {
            "job": {
                "name": "Test Notification Job",
                "status": "running",
                "execution_time_ms": 1500,
                "completed_steps": 0,
                "total_steps": 1
            },
            "user": {
                "username": "admin",
                "email": "admin@opsconductor.local"
            },
            "system": {
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}:3007/execute-step",
            headers=headers,
            json=execution_request,
            timeout=30
        )
        
        print(f"Direct execution response status: {response.status_code}")
        print(f"Direct execution response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Notification step executed successfully")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Output: {result.get('stdout', 'no output')}")
            if result.get('stderr'):
                print(f"   Error: {result.get('stderr')}")
            return True
        else:
            print(f"❌ Notification step execution failed")
            return False
            
    except Exception as e:
        print(f"❌ Error executing notification step: {e}")
        return False

if __name__ == "__main__":
    print("Testing notification step execution directly...")
    success = test_direct_execution()
    
    if success:
        print("\n✅ Direct notification execution test passed!")
    else:
        print("\n❌ Direct notification execution test failed")
        sys.exit(1)