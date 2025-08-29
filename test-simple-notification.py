#!/usr/bin/env python3
"""
Simple test for notification steps
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

def test_simple_email_notification():
    """Test creating a simple email notification job"""
    print("Testing simple email notification job creation...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Simple job with just email notification
    job_definition = {
        "name": "Simple Email Test",
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
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 201:
        job = response.json()
        print(f"✅ Created job: {job['name']} (ID: {job['id']})")
        return job['id']
    else:
        print(f"❌ Failed to create job")
        return None

if __name__ == "__main__":
    test_simple_email_notification()