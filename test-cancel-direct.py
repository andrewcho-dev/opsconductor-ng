#!/usr/bin/env python3
"""
Test cancel functionality directly via API
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
    
    # Try to cancel job 15 (the most recent one)
    job_id = 15
    
    print(f"🛑 Attempting to cancel job {job_id}...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/discovery/discovery-jobs/{job_id}/cancel", 
                               headers=headers, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - service might be busy")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    main()