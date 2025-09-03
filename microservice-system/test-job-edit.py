#!/usr/bin/env python3
"""
Test script to verify job editing functionality
"""

import requests
import json
import random

# Configuration
BASE_URL = "http://localhost:3006"
AUTH_URL = "http://localhost:3001"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{AUTH_URL}/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to authenticate: {response.status_code}")

def test_job_edit():
    """Test job creation and editing"""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Create a test notification job
    job_name = f"Edit Test Job {random.randint(1000000, 9999999)}"
    create_data = {
        "name": job_name,
        "version": 1,
        "definition": {
            "name": job_name,
            "version": 1,
            "steps": [{
                "type": "notify.email",
                "recipients": ["original@example.com"],
                "subject_template": "Original Subject",
                "body_template": "Original body content"
            }]
        },
        "is_active": True
    }
    
    print("Creating test job...")
    create_response = requests.post(f"{BASE_URL}/jobs", json=create_data, headers=headers)
    if create_response.status_code != 201:
        print(f"Failed to create job: {create_response.status_code} - {create_response.text}")
        return False
    
    job = create_response.json()
    job_id = job["id"]
    print(f"✅ Created job with ID: {job_id}")
    
    # Retrieve the job to verify data
    print("Retrieving job data...")
    get_response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    if get_response.status_code != 200:
        print(f"Failed to retrieve job: {get_response.status_code}")
        return False
    
    retrieved_job = get_response.json()
    print(f"✅ Retrieved job data:")
    print(f"   Name: {retrieved_job['name']}")
    print(f"   Steps: {len(retrieved_job['definition']['steps'])}")
    print(f"   First step type: {retrieved_job['definition']['steps'][0]['type']}")
    print(f"   Recipients: {retrieved_job['definition']['steps'][0]['recipients']}")
    print(f"   Subject: {retrieved_job['definition']['steps'][0]['subject_template']}")
    
    # Update the job
    print("Updating job...")
    update_data = {
        "name": job_name + " (Updated)",
        "version": 2,
        "definition": {
            "name": job_name + " (Updated)",
            "version": 2,
            "steps": [{
                "type": "notify.email",
                "recipients": ["updated@example.com", "second@example.com"],
                "subject_template": "Updated Subject",
                "body_template": "Updated body content with more details"
            }]
        },
        "is_active": True
    }
    
    update_response = requests.put(f"{BASE_URL}/jobs/{job_id}", json=update_data, headers=headers)
    if update_response.status_code != 200:
        print(f"Failed to update job: {update_response.status_code} - {update_response.text}")
        return False
    
    updated_job = update_response.json()
    print(f"✅ Updated job:")
    print(f"   Name: {updated_job['name']}")
    print(f"   Version: {updated_job['version']}")
    print(f"   Recipients: {updated_job['definition']['steps'][0]['recipients']}")
    print(f"   Subject: {updated_job['definition']['steps'][0]['subject_template']}")
    
    # Verify the update by retrieving again
    print("Verifying update...")
    verify_response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    if verify_response.status_code != 200:
        print(f"Failed to verify job: {verify_response.status_code}")
        return False
    
    verified_job = verify_response.json()
    print(f"✅ Verified updated job data:")
    print(f"   Name: {verified_job['name']}")
    print(f"   Version: {verified_job['version']}")
    print(f"   Recipients: {verified_job['definition']['steps'][0]['recipients']}")
    print(f"   Subject: {verified_job['definition']['steps'][0]['subject_template']}")
    
    return True

if __name__ == "__main__":
    print("Testing job editing functionality...")
    try:
        if test_job_edit():
            print("\n✅ Job editing test completed successfully!")
        else:
            print("\n❌ Job editing test failed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")