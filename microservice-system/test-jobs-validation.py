#!/usr/bin/env python3
"""
Test jobs service validation directly
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

def test_winrm_job():
    """Test creating a simple WinRM job first"""
    print("Testing WinRM job creation...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Simple WinRM job that should work
    job_definition = {
        "name": "Simple WinRM Test",
        "version": 1,
        "steps": [
            {
                "type": "winrm.exec",
                "shell": "powershell",
                "target": "test-target",
                "command": "Get-Date"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}:3006/jobs",
        headers=headers,
        json={
            "name": job_definition["name"],
            "version": job_definition["version"],
            "definition": job_definition,
            "is_active": True
        }
    )
    
    print(f"WinRM job response status: {response.status_code}")
    if response.status_code != 201:
        print(f"WinRM job response body: {response.text}")
        return False
    else:
        print("✅ WinRM job created successfully")
        return True

def test_notification_job():
    """Test creating a notification job"""
    print("Testing notification job creation...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Simple notification job
    job_definition = {
        "name": "Simple Notification Test",
        "version": 1,
        "steps": [
            {
                "type": "notify.email",
                "recipients": ["test@example.com"],
                "subject_template": "Test from OpsConductor",
                "body_template": "This is a test notification."
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}:3006/jobs",
        headers=headers,
        json={
            "name": job_definition["name"],
            "version": job_definition["version"],
            "definition": job_definition,
            "is_active": True
        }
    )
    
    print(f"Notification job response status: {response.status_code}")
    print(f"Notification job response body: {response.text}")
    
    if response.status_code == 201:
        print("✅ Notification job created successfully")
        return True
    else:
        print("❌ Notification job creation failed")
        return False

if __name__ == "__main__":
    print("Testing job creation...")
    
    # Test WinRM job first to make sure basic functionality works
    winrm_success = test_winrm_job()
    
    # Test notification job
    notification_success = test_notification_job()
    
    if winrm_success and notification_success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)