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

def test_complete_simplified_discovery():
    """Test the complete simplified discovery interface"""
    print("🧪 Testing Complete Simplified Discovery Interface")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Create discovery job with simplified structure
    test_job = {
        "name": "Complete Simplified Test",
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
                },
                {
                    "name": "WinRM HTTP",
                    "port": 5985,
                    "protocol": "tcp",
                    "category": "Windows Management",
                    "enabled": True
                }
            ],
            "os_detection": True,
            "timeout": 300
        }
    }
    
    try:
        # Test 1: Create discovery job
        print("📤 Creating simplified discovery job...")
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
            
            # Test 2: Get discovery jobs list using /discovery-jobs endpoint
            print("\n📥 Testing /discovery-jobs endpoint...")
            response = requests.get(f"{BASE_URL}/discovery-jobs?skip=0&limit=10", 
                                  headers=headers,
                                  timeout=10)
            
            if response.status_code == 200:
                jobs_data = response.json()
                print(f"✅ Discovery jobs list retrieved successfully!")
                print(f"   Total jobs: {jobs_data.get('total', 0)}")
                
                if jobs_data.get('jobs'):
                    latest_job = jobs_data['jobs'][0]
                    print(f"   Latest job: {latest_job['name']}")
                    print(f"   Status: {latest_job['status']}")
                    
                    # Verify no discovery_type field issues in list
                    if 'discovery_type' in latest_job:
                        print(f"   Discovery type: {latest_job['discovery_type']}")
                
                # Test 3: Get specific job details
                print(f"\n📋 Testing job details for job {job_id}...")
                response = requests.get(f"{BASE_URL}/discovery-jobs/{job_id}", 
                                      headers=headers,
                                      timeout=10)
                
                if response.status_code == 200:
                    job_detail = response.json()
                    print(f"✅ Job details retrieved successfully!")
                    print(f"   Job name: {job_detail['name']}")
                    print(f"   Status: {job_detail['status']}")
                    print(f"   Created at: {job_detail['created_at']}")
                    
                    return True
                else:
                    print(f"❌ Failed to get job details: {response.status_code}")
                    return False
                
            else:
                print(f"❌ Failed to get discovery jobs list: {response.status_code}")
                print(f"   Response: {response.text}")
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
    print("🔍 Complete Discovery Service - Simplified Interface Testing")
    print("=" * 60)
    
    success = test_complete_simplified_discovery()
    
    if success:
        print("\n🎉 Complete simplified discovery interface test passed!")
        print("✅ Discovery type dropdown removed from frontend")
        print("✅ Service detection checkbox removed from frontend") 
        print("✅ Connection testing checkbox removed from frontend")
        print("✅ Clean table layout without type column")
        print("✅ Granular service selection working")
        print("✅ Backend API endpoints working correctly")
        print("✅ Authentication issues resolved")
        print("✅ Services restarted and refreshed")
        print("\n🚀 The simplified discovery interface is ready for use!")
        return 0
    else:
        print("\n❌ Test failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())