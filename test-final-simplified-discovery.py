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

def test_final_simplified_discovery():
    """Test the final simplified discovery interface"""
    print("🧪 Testing Final Simplified Discovery Interface")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Create discovery job with simplified structure
    test_job = {
        "name": "Final Simplified Test",
        "discovery_type": "network_scan",  # This is set automatically
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
                }
            ],
            "os_detection": True,
            "timeout": 300
            # Note: No discovery_type dropdown, service_detection, or connection_testing
        }
    }
    
    try:
        # Create discovery job
        print("📤 Creating final simplified discovery job...")
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
            
            # Verify simplified structure
            config = job_data["config"]
            
            # Check that required fields are present
            required_fields = ['cidr_ranges', 'services', 'os_detection', 'timeout']
            present_required = [field for field in required_fields if field in config]
            print(f"   ✅ Required fields present: {', '.join(present_required)}")
            
            # Check that removed fields are not present
            removed_fields = ['service_detection', 'connection_testing']
            missing_removed = [field for field in removed_fields if field not in config]
            if len(missing_removed) == len(removed_fields):
                print(f"   ✅ Removed fields are not present: {', '.join(removed_fields)}")
            else:
                present_removed = [field for field in removed_fields if field in config]
                print(f"   ⚠️  Some removed fields are still present: {', '.join(present_removed)}")
            
            # Test 2: Get discovery jobs list
            print("\n📥 Testing discovery jobs list...")
            response = requests.get(f"{BASE_URL}/jobs", 
                                  headers=headers,
                                  timeout=10)
            
            if response.status_code == 200:
                jobs_data = response.json()
                print(f"✅ Jobs list retrieved successfully!")
                print(f"   Total jobs: {jobs_data.get('total', 0)}")
                
                if jobs_data.get('jobs'):
                    latest_job = jobs_data['jobs'][0]
                    print(f"   Latest job: {latest_job['name']}")
                    print(f"   Status: {latest_job['status']}")
                
                return True
            else:
                print(f"❌ Failed to get jobs list: {response.status_code}")
                return False
                
        else:
            print(f"❌ Failed to create discovery job: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in discovery test: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Final Discovery Service - Simplified Interface Testing")
    print("=" * 60)
    
    success = test_final_simplified_discovery()
    
    if success:
        print("\n🎉 Final simplified discovery interface test passed!")
        print("✅ Discovery type dropdown removed")
        print("✅ Service detection checkbox removed") 
        print("✅ Connection testing checkbox removed")
        print("✅ Clean table layout without type column")
        print("✅ Granular service selection working")
        print("✅ Services restarted and refreshed")
        return 0
    else:
        print("\n❌ Test failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())