#!/usr/bin/env python3
"""
Test Discovery Job Cancel Functionality with a Long-Running Job
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

def test_cancel_running_job():
    print("🧪 Testing Cancel Functionality with Long-Running Job")
    print("=" * 60)
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a job that will take a while to complete (large network range)
    print("\n📤 Creating a long-running discovery job...")
    job_data = {
        "name": "Long-Running Cancel Test",
        "discovery_type": "network_scan",
        "config": {
            "cidr_ranges": ["10.0.0.0/24"],  # Large range that will take time
            "services": [
                {"name": "SSH", "port": 22, "category": "remote_access", "enabled": True},
                {"name": "RDP", "port": 3389, "category": "remote_access", "enabled": True},
                {"name": "WinRM", "port": 5985, "category": "management", "enabled": True}
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
    
    # Wait for job to start running
    print("\n⏳ Waiting for job to start running...")
    for i in range(10):  # Wait up to 10 seconds
        time.sleep(1)
        response = requests.get(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}", headers=headers)
        job_status = response.json()["status"]
        print(f"📊 Job status (attempt {i+1}): {job_status}")
        
        if job_status == "running":
            print("✅ Job is now running!")
            break
        elif job_status in ["completed", "failed", "cancelled"]:
            print(f"⚠️  Job finished too quickly with status: {job_status}")
            break
    else:
        print("⚠️  Job didn't start running within 10 seconds")
    
    # If job is running, test cancel
    if job_status == "running":
        print(f"\n🛑 Testing cancel functionality for running job {job_id}...")
        response = requests.post(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}/cancel", headers=headers)
        if response.status_code == 200:
            print("✅ Successfully cancelled running job")
            print(f"📝 Response: {response.json()['message']}")
            
            # Verify job is cancelled
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}", headers=headers)
            new_status = response.json()["status"]
            print(f"📊 Job status after cancel: {new_status}")
            
            if new_status == "cancelled":
                print("✅ Job successfully cancelled!")
            else:
                print(f"⚠️  Job status is {new_status}, expected 'cancelled'")
        else:
            print(f"❌ Failed to cancel job: {response.text}")
    
    # Clean up - delete the job
    print(f"\n🧹 Cleaning up - deleting job {job_id}...")
    response = requests.delete(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}", headers=headers)
    if response.status_code == 200:
        print("✅ Job deleted successfully")
    else:
        print(f"⚠️  Failed to delete job: {response.text}")
    
    print("\n🎉 Cancel functionality test completed!")

if __name__ == "__main__":
    test_cancel_running_job()