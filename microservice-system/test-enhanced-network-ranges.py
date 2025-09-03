#!/usr/bin/env python3
"""
Test script for enhanced network range parsing functionality
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost"
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """Login and get access token"""
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_network_range_validation(token):
    """Test the network range validation endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test cases for different network range formats
    test_cases = [
        # CIDR ranges
        "192.168.1.0/24",
        "10.0.0.0/16",
        
        # IP ranges (short form)
        "192.168.1.100-120",
        "10.0.0.1-5",
        
        # IP ranges (full form)
        "192.168.1.100-192.168.1.120",
        "10.0.0.1-10.0.0.5",
        
        # Individual IPs
        "192.168.1.20, 192.168.1.22, 192.168.1.25",
        "10.0.0.1,10.0.0.3,10.0.0.5",
        
        # Mixed formats
        "192.168.1.23, 192.168.1.26-32, 10.0.0.0/28",
        "172.16.1.1, 172.16.1.10-20, 172.16.2.0/24",
        
        # Invalid cases
        "invalid-range",
        "192.168.1.300",
        "192.168.1.1-300",
        ""
    ]
    
    print("Testing Network Range Validation:")
    print("=" * 50)
    
    for i, test_range in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test_range}'")
        
        validation_data = {"ranges": [test_range]}
        response = requests.post(
            f"{BASE_URL}/api/v1/discovery/validate-network-ranges",
            json=validation_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["results"]:
                validation_result = result["results"][0]
                if validation_result["valid"]:
                    print(f"  ✓ Valid - {validation_result['parsed_count']} target(s)")
                    print(f"    Sample targets: {validation_result['sample_targets'][:5]}")
                    print(f"    Optimized ranges: {validation_result['optimized_ranges']}")
                else:
                    print(f"  ✗ Invalid - {validation_result['error']}")
            else:
                print("  ✗ No results returned")
        else:
            print(f"  ✗ Request failed: {response.status_code} - {response.text}")

def test_discovery_job_creation(token):
    """Test creating a discovery job with enhanced network ranges"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test job with mixed network range formats
    job_data = {
        "name": "Enhanced Network Range Test",
        "discovery_type": "network_scan",
        "config": {
            "cidr_ranges": [
                "192.168.1.100-110",  # IP range
                "10.0.0.1, 10.0.0.5, 10.0.0.10",  # Individual IPs
                "172.16.1.1, 172.16.1.20-25"  # Mixed format
            ],
            "services": [
                {"name": "SSH", "port": 22, "protocol": "tcp", "category": "Remote Access", "enabled": True},
                {"name": "RDP", "port": 3389, "protocol": "tcp", "category": "Remote Access", "enabled": True},
                {"name": "WinRM HTTP", "port": 5985, "protocol": "tcp", "category": "Windows Management", "enabled": True}
            ],
            "os_detection": True,
            "timeout": 300
        }
    }
    
    print("\n\nTesting Discovery Job Creation with Enhanced Ranges:")
    print("=" * 55)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/discovery/jobs",
        json=job_data,
        headers=headers
    )
    
    if response.status_code == 200:
        job = response.json()
        print(f"✓ Discovery job created successfully!")
        print(f"  Job ID: {job['id']}")
        print(f"  Job Name: {job['name']}")
        print(f"  Status: {job['status']}")
        print(f"  Network Ranges: {job['config']['cidr_ranges']}")
        return job['id']
    else:
        print(f"✗ Job creation failed: {response.status_code} - {response.text}")
        return None

def main():
    print("Enhanced Network Range Testing")
    print("=" * 40)
    
    # Login
    token = login()
    if not token:
        print("Failed to login. Exiting.")
        sys.exit(1)
    
    print("✓ Login successful")
    
    # Test validation endpoint
    test_network_range_validation(token)
    
    # Test job creation
    job_id = test_discovery_job_creation(token)
    
    if job_id:
        print(f"\n✓ All tests completed successfully!")
        print(f"  Created discovery job with ID: {job_id}")
        print(f"  You can monitor the job progress in the web interface.")
    else:
        print(f"\n✗ Some tests failed.")

if __name__ == "__main__":
    main()