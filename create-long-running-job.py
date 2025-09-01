#!/usr/bin/env python3
"""
Create a long-running discovery job to test the Cancel button
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
    
    # Create a job that will take a long time (scan multiple large ranges)
    job_data = {
        "name": "Long Running Test - Check UI for Cancel Button",
        "discovery_type": "network_scan",
        "config": {
            "cidr_ranges": [
                "192.168.1.0/24",   # 254 IPs
                "10.0.0.0/24",      # 254 IPs  
                "172.16.0.0/24"     # 254 IPs
            ],
            "services": [
                {"name": "SSH", "port": 22, "category": "remote_access", "enabled": True},
                {"name": "RDP", "port": 3389, "category": "remote_access", "enabled": True},
                {"name": "WinRM", "port": 5985, "category": "management", "enabled": True},
                {"name": "HTTPS", "port": 443, "category": "web", "enabled": True},
                {"name": "HTTP", "port": 80, "category": "web", "enabled": True}
            ],
            "os_detection": True,
            "timeout": 60  # Longer timeout per host
        }
    }
    
    print("🚀 Creating long-running discovery job...")
    response = requests.post(f"{BASE_URL}/api/v1/discovery/discovery-jobs", json=job_data, headers=headers)
    
    if response.status_code == 200:
        job = response.json()
        print(f"✅ Created job ID: {job['id']}")
        print(f"📝 Job name: {job['name']}")
        print(f"📊 Status: {job['status']}")
        print("\n🎯 Now go to the Discovery page in the UI to see the Cancel button!")
        print("   The job should show 'running' status with a yellow 'Cancel' button")
        print(f"   URL: http://localhost:3000/discovery")
        
        # Monitor job status for a few seconds
        for i in range(10):
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job['id']}", headers=headers)
            if status_response.status_code == 200:
                current_status = status_response.json()["status"]
                print(f"📊 Job status (after {(i+1)*2}s): {current_status}")
                if current_status == "running":
                    print("🎉 Job is running! Check the UI now for the Cancel button!")
                    break
                elif current_status in ["completed", "failed", "cancelled"]:
                    print(f"⚠️  Job finished with status: {current_status}")
                    break
        
    else:
        print(f"❌ Failed to create job: {response.text}")

if __name__ == "__main__":
    main()