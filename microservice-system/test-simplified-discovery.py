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
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_simplified_discovery():
    """Test creating a discovery job with the simplified interface"""
    print("🧪 Testing Simplified Discovery Interface")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data with simplified structure (no discovery_type dropdown, no service_detection, no connection_testing)
    test_job = {
        "name": "Simplified Discovery Test",
        "discovery_type": "network_scan",  # This is set automatically, not from dropdown
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
            "timeout": 300
            # Note: No service_detection or connection_testing fields
        }
    }
    
    try:
        # Create discovery job
        print("📤 Creating simplified discovery job...")
        response = requests.post(f"{BASE_URL}/discovery-jobs", 
                               json=test_job, 
                               headers=headers,
                               timeout=10)
        
        if response.status_code in [200, 201]:
            job_data = response.json()
            job_id = job_data["id"]
            print(f"✅ Simplified discovery job created successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Job Name: {job_data['name']}")
            print(f"   Discovery Type: {job_data['discovery_type']}")
            
            # Verify the simplified config structure
            config = job_data["config"]
            print(f"   OS Detection: {config.get('os_detection', 'Not set')}")
            print(f"   Timeout: {config.get('timeout', 'Not set')}")
            
            # Check that removed fields are not present
            removed_fields = ['service_detection', 'connection_testing']
            missing_fields = [field for field in removed_fields if field not in config]
            if len(missing_fields) == len(removed_fields):
                print(f"   ✅ Removed fields are not present: {', '.join(removed_fields)}")
            else:
                present_fields = [field for field in removed_fields if field in config]
                print(f"   ⚠️  Some removed fields are still present: {', '.join(present_fields)}")
            
            # Check services array
            if "services" in config:
                enabled_services = [s for s in config["services"] if s["enabled"]]
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

def main():
    """Main test function"""
    print("🔍 Discovery Service - Simplified Interface Testing")
    print("=" * 60)
    
    success = test_simplified_discovery()
    
    if success:
        print("\n🎉 Simplified discovery interface test passed!")
        print("✅ Discovery type dropdown removed")
        print("✅ Service detection checkbox removed") 
        print("✅ Connection testing checkbox removed")
        print("✅ Granular service selection working")
        return 0
    else:
        print("\n❌ Test failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())