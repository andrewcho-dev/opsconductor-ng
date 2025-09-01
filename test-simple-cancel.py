#!/usr/bin/env python3
"""
Simple test to cancel a running discovery job
"""

import requests
import time

BASE_URL = "http://localhost"

def get_auth_token():
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    return response.json()["access_token"]

def main():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current jobs
    response = requests.get(f"{BASE_URL}/api/v1/discovery/jobs", headers=headers)
    jobs = response.json()["jobs"]
    
    print(f"Found {len(jobs)} discovery jobs:")
    for job in jobs:
        print(f"  Job {job['id']}: {job['name']} - Status: {job['status']}")
        
        if job['status'] == 'running':
            print(f"\n🛑 Attempting to cancel running job {job['id']}...")
            cancel_response = requests.post(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job['id']}/cancel", headers=headers)
            print(f"Cancel response: {cancel_response.status_code}")
            if cancel_response.status_code == 200:
                print(f"✅ Successfully cancelled job {job['id']}")
                print(f"Response: {cancel_response.json()}")
            else:
                print(f"❌ Failed to cancel: {cancel_response.text}")
            
            # Check status after cancel
            time.sleep(1)
            status_response = requests.get(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job['id']}", headers=headers)
            if status_response.status_code == 200:
                new_status = status_response.json()["status"]
                print(f"📊 Job status after cancel: {new_status}")

if __name__ == "__main__":
    main()