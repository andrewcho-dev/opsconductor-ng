#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost"

def get_auth_token():
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    return response.json()["access_token"]

token = get_auth_token()
headers = {"Authorization": f"Bearer {token}"}

# Get recent jobs
response = requests.get(f"{BASE_URL}/api/v1/discovery/discovery-jobs?skip=0&limit=5", headers=headers)
if response.status_code == 200:
    jobs = response.json()["jobs"]
    print("Recent Discovery Jobs:")
    for job in jobs:
        print(f"  Job {job['id']}: {job['name']} - Status: {job['status']}")
        if job['status'] == 'running':
            print(f"    🏃 RUNNING JOB FOUND! Check the UI for Cancel button!")
else:
    print(f"Error: {response.status_code} - {response.text}")