#!/usr/bin/env python3
"""
Test Discovery Job Delete and Cancel Functionality
"""

import requests
import time
import json

BASE_URL = "http://localhost"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    return response.json()["access_token"]

def test_discovery_delete_cancel():
    print("🧪 Testing Discovery Job Delete and Cancel Functionality")
    print("=" * 60)
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Create a discovery job
    print("\n📤 Creating a test discovery job...")
    job_data = {
        "name": "Delete/Cancel Test Job",
        "discovery_type": "network_scan",
        "config": {
            "cidr_ranges": ["192.168.1.1/32"],  # Single IP to make it quick
            "services": [
                {"name": "SSH", "port": 22, "enabled": True},
                {"name": "RDP", "port": 3389, "enabled": True}
            ],
            "os_detection": True,
            "timeout": 30
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/discovery/discovery-jobs", json=job_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create job: {response.text}")
        return
    
    job = response.json()
    job_id = job["id"]
    print(f"✅ Created discovery job with ID: {job_id}")
    
    # Test 2: Wait a moment for job to start running
    print("\n⏳ Waiting for job to start running...")
    time.sleep(2)
    
    # Check job status
    response = requests.get(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}", headers=headers)
    job_status = response.json()["status"]
    print(f"📊 Job status: {job_status}")
    
    # Test 3: Try to cancel if running
    if job_status == "running":
        print(f"\n🛑 Testing cancel functionality for running job {job_id}...")
        response = requests.post(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}/cancel", headers=headers)
        if response.status_code == 200:
            print("✅ Successfully cancelled running job")
            print(f"📝 Response: {response.json()['message']}")
        else:
            print(f"❌ Failed to cancel job: {response.text}")
    else:
        print(f"ℹ️  Job is not running (status: {job_status}), skipping cancel test")
    
    # Test 4: Test delete functionality
    print(f"\n🗑️  Testing delete functionality for job {job_id}...")
    response = requests.delete(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}", headers=headers)
    if response.status_code == 200:
        print("✅ Successfully deleted job")
        result = response.json()
        print(f"📝 Response: {result['message']}")
        if 'targets_deleted' in result:
            print(f"🎯 Targets deleted: {result['targets_deleted']}")
        if 'was_running' in result:
            print(f"🏃 Was running: {result['was_running']}")
    else:
        print(f"❌ Failed to delete job: {response.text}")
    
    # Test 5: Verify job is deleted
    print(f"\n🔍 Verifying job {job_id} is deleted...")
    response = requests.get(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}", headers=headers)
    if response.status_code == 404:
        print("✅ Job successfully deleted (404 Not Found)")
    else:
        print(f"❌ Job still exists: {response.status_code}")
    
    print("\n🎉 Discovery delete/cancel functionality test completed!")

if __name__ == "__main__":
    test_discovery_delete_cancel()