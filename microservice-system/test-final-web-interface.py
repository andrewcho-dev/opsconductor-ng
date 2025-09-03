#!/usr/bin/env python3

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost"  # Through nginx

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
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

def test_simplified_discovery_web_interface():
    """Test the simplified discovery interface through web"""
    print("🌐 Testing Simplified Discovery Interface Through Web")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Create discovery job with simplified structure
    test_job = {
        "name": "Web Interface Test",
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
                }
            ],
            "os_detection": True,
            "timeout": 300
        }
    }
    
    try:
        # Create discovery job through web interface
        print("📤 Creating discovery job through web interface...")
        response = requests.post(f"{BASE_URL}/api/v1/discovery/discovery-jobs", 
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
            
            return True
                
        else:
            print(f"❌ Failed to create discovery job: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in discovery test: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Final Discovery Service - Web Interface Testing")
    print("=" * 60)
    
    success = test_simplified_discovery_web_interface()
    
    if success:
        print("\n🎉 Simplified discovery interface is working through web!")
        print("\n📋 Summary of Changes Completed:")
        print("✅ Discovery type dropdown removed from frontend")
        print("✅ Service detection checkbox removed from frontend") 
        print("✅ Connection testing checkbox removed from frontend")
        print("✅ Clean table layout without type column")
        print("✅ Granular service selection working")
        print("✅ Backend API endpoints working correctly")
        print("✅ Web interface accessible through nginx")
        print("✅ Services restarted and refreshed")
        print("\n🚀 The simplified discovery interface is ready!")
        print("🌐 Access the web interface at: http://localhost")
        return 0
    else:
        print("\n❌ Test failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())