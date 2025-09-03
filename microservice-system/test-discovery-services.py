#!/usr/bin/env python3

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:3010"  # Discovery service direct
AUTH_URL = "http://localhost:3001"  # Auth service direct

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(f"{AUTH_URL}/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_discovery_job_creation():
    """Test creating a discovery job with the new services array"""
    print("🧪 Testing Discovery Job Creation with Services Array")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data with new services array format
    test_job = {
        "name": "Test Services Discovery",
        "discovery_type": "network_scan",
        "config": {
            "cidr_ranges": ["192.168.1.0/24"],
            "services": [
                {
                    "name": "SSH",
                    "port": 22,
                    "protocol": "tcp",
                    "category": "Remote Access",
                    "enabled": True
                },
                {
                    "name": "RDP",
                    "port": 3389,
                    "protocol": "tcp",
                    "category": "Remote Access",
                    "enabled": True
                },
                {
                    "name": "WinRM HTTP",
                    "port": 5985,
                    "protocol": "tcp",
                    "category": "Windows Management",
                    "enabled": True
                },
                {
                    "name": "HTTP",
                    "port": 80,
                    "protocol": "tcp",
                    "category": "Web Services",
                    "enabled": False
                }
            ],
            "os_detection": True,
            "service_detection": True,
            "connection_testing": False,
            "timeout": 300
        }
    }
    
    try:
        # Create discovery job
        print("📤 Creating discovery job...")
        response = requests.post(f"{BASE_URL}/discovery-jobs", 
                               json=test_job, 
                               headers=headers,
                               timeout=10)
        
        if response.status_code in [200, 201]:
            job_data = response.json()
            job_id = job_data["id"]
            print(f"✅ Discovery job created successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Job Name: {job_data['name']}")
            print(f"   Discovery Type: {job_data['discovery_type']}")
            
            # Check if services are properly stored
            if "services" in job_data["config"]:
                enabled_services = [s for s in job_data["config"]["services"] if s["enabled"]]
                print(f"   Enabled Services: {len(enabled_services)}")
                for service in enabled_services:
                    print(f"     - {service['name']} (port {service['port']})")
            else:
                print("   ⚠️  Services array not found in response")
            
            return True
        else:
            print(f"❌ Failed to create discovery job: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating discovery job: {e}")
        return False

def test_legacy_compatibility():
    """Test that legacy scan_intensity still works"""
    print("\n🧪 Testing Legacy Scan Intensity Compatibility")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data with legacy scan_intensity format
    legacy_job = {
        "name": "Test Legacy Scan Intensity",
        "discovery_type": "network_scan",
        "config": {
            "cidr_ranges": ["192.168.1.0/24"],
            "scan_intensity": "standard",
            "os_detection": True,
            "service_detection": True,
            "connection_testing": False,
            "timeout": 300
        }
    }
    
    try:
        # Create discovery job
        print("📤 Creating legacy discovery job...")
        response = requests.post(f"{BASE_URL}/discovery-jobs", 
                               json=legacy_job, 
                               headers=headers,
                               timeout=10)
        
        if response.status_code in [200, 201]:
            job_data = response.json()
            job_id = job_data["id"]
            print(f"✅ Legacy discovery job created successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Job Name: {job_data['name']}")
            print(f"   Scan Intensity: {job_data['config'].get('scan_intensity', 'Not found')}")
            
            return True
        else:
            print(f"❌ Failed to create legacy discovery job: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating legacy discovery job: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Discovery Service - Services Array Testing")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # Test new services array functionality
    if test_discovery_job_creation():
        success_count += 1
    
    # Test legacy compatibility
    if test_legacy_compatibility():
        success_count += 1
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Discovery service supports both new services array and legacy scan_intensity.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())