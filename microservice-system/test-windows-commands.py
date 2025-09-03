#!/usr/bin/env python3
"""
Test script for Windows Commands functionality
"""

import requests
import json
import random

# Configuration
BASE_URL = "http://localhost:3006"  # Jobs service
AUTH_URL = "http://localhost:3001"  # Auth service

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to authenticate: {response.status_code} - {response.text}")
        return None

def create_windows_command_job(token, command_type="system_info", parameters=None):
    """Create a job with Windows command step"""
    if parameters is None:
        parameters = {}
    
    job_name = f"Windows Command Test - {command_type} {random.randint(100000, 999999)}"
    
    job_data = {
        "name": job_name,
        "version": 1,
        "definition": {
            "name": job_name,
            "version": 1,
            "parameters": {},
            "steps": [
                {
                    "type": "windows.command",
                    "target": "test-target",  # This would need to be a real target
                    "command_type": command_type,
                    "parameters": parameters,
                    "timeoutSec": 120
                }
            ]
        },
        "is_active": True
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/jobs", json=job_data, headers=headers)
    
    if response.status_code == 201:
        job = response.json()
        print(f"✅ Created Windows command job with ID: {job['id']}")
        print(f"   Name: {job['name']}")
        print(f"   Command Type: {command_type}")
        print(f"   Parameters: {parameters}")
        return job
    else:
        print(f"❌ Failed to create job: {response.status_code} - {response.text}")
        return None

def test_different_command_types(token):
    """Test different Windows command types"""
    
    # Test system info (no parameters)
    print("\n=== Testing System Information ===")
    create_windows_command_job(token, "system_info")
    
    # Test disk space with specific drive
    print("\n=== Testing Disk Space (C: drive) ===")
    create_windows_command_job(token, "disk_space", {"drive": "C:"})
    
    # Test disk space for all drives
    print("\n=== Testing Disk Space (all drives) ===")
    create_windows_command_job(token, "disk_space")
    
    # Test running services with filter
    print("\n=== Testing Running Services (Windows services) ===")
    create_windows_command_job(token, "running_services", {"service_filter": "Windows"})
    
    # Test event logs
    print("\n=== Testing Event Logs (System, Error level) ===")
    create_windows_command_job(token, "event_logs", {
        "log_name": "System",
        "max_events": 10,
        "level": "Error"
    })
    
    # Test registry query
    print("\n=== Testing Registry Query ===")
    create_windows_command_job(token, "registry_query", {
        "registry_path": "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion",
        "value_name": "ProductName"
    })
    
    # Test file operations
    print("\n=== Testing File Operations (list Windows directory) ===")
    create_windows_command_job(token, "file_operations", {
        "operation": "list",
        "path": "C:\\Windows",
        "filter": "*.exe"
    })
    
    # Test process list
    print("\n=== Testing Process List ===")
    create_windows_command_job(token, "process_list")

def main():
    print("Testing Windows Commands functionality...")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return
    
    print("✅ Successfully authenticated")
    
    # Test different command types
    test_different_command_types(token)
    
    print("\n✅ Windows Commands test completed!")
    print("\nNote: These jobs have been created but won't execute without valid Windows targets.")
    print("You can view them in the frontend at https://localhost")

if __name__ == "__main__":
    main()