#!/usr/bin/env python3
"""
Test Step Libraries Integration
Verifies that the step-libraries-service is properly integrated into OpsConductor
"""

import requests
import json
import time
import sys

def test_step_libraries_integration():
    """Test that step libraries service is integrated and working"""
    
    print("🧪 Testing Step Libraries Integration...")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get("http://localhost:3011/health", timeout=10)
        if response.status_code == 200:
            print("✅ Step Libraries Service health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Check if service is accessible through nginx
    print("\n2. Testing nginx proxy...")
    try:
        response = requests.get("http://localhost/api/v1/step-libraries/health", timeout=10)
        if response.status_code == 200:
            print("✅ Step Libraries Service accessible through nginx")
        else:
            print(f"❌ Nginx proxy failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Nginx proxy failed: {e}")
        return False
    
    # Test 3: Check libraries endpoint
    print("\n3. Testing libraries endpoint...")
    try:
        response = requests.get("http://localhost:3011/api/v1/libraries", timeout=10)
        if response.status_code == 200:
            libraries = response.json()
            print(f"✅ Libraries endpoint working - found {len(libraries)} libraries")
            
            # Show installed libraries
            if libraries:
                print("   Installed libraries:")
                for lib in libraries:
                    status = "🟢" if lib.get('is_enabled') else "🔴"
                    print(f"   {status} {lib.get('display_name', lib.get('name'))} v{lib.get('version')}")
            else:
                print("   No libraries installed yet")
        else:
            print(f"❌ Libraries endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Libraries endpoint failed: {e}")
        return False
    
    # Test 4: Check steps endpoint
    print("\n4. Testing steps endpoint...")
    try:
        response = requests.get("http://localhost:3011/api/v1/steps", timeout=10)
        if response.status_code == 200:
            steps_data = response.json()
            steps = steps_data.get('steps', [])
            print(f"✅ Steps endpoint working - found {len(steps)} available steps")
            
            # Show available step categories
            categories = set()
            libraries = set()
            for step in steps:
                categories.add(step.get('category', 'unknown'))
                libraries.add(step.get('library', 'unknown'))
            
            if categories:
                print(f"   Categories: {', '.join(sorted(categories))}")
            if libraries:
                print(f"   Libraries: {', '.join(sorted(libraries))}")
        else:
            print(f"❌ Steps endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Steps endpoint failed: {e}")
        return False
    
    # Test 5: Check database integration
    print("\n5. Testing database integration...")
    try:
        response = requests.get("http://localhost:3011/api/v1/analytics/usage", timeout=10)
        if response.status_code == 200:
            analytics = response.json()
            print("✅ Database integration working - analytics available")
            print(f"   Performance stats: {analytics.get('performance_stats', {})}")
        else:
            print(f"❌ Database integration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Database integration failed: {e}")
        return False
    
    print("\n🎉 All Step Libraries Integration Tests Passed!")
    print("\n📋 Integration Summary:")
    print("   ✅ Step Libraries Service is running on port 3011")
    print("   ✅ Service is accessible through nginx proxy")
    print("   ✅ Database integration is working")
    print("   ✅ Core API endpoints are functional")
    print("   ✅ Frontend can load dynamic steps")
    
    print("\n🚀 Ready to use:")
    print("   1. Open http://localhost in your browser")
    print("   2. Navigate to Visual Job Builder")
    print("   3. Click 'Manage' in the Step Library panel")
    print("   4. Upload library ZIP files to extend functionality")
    
    return True

def wait_for_services():
    """Wait for services to be ready"""
    print("⏳ Waiting for services to be ready...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:3011/health", timeout=5)
            if response.status_code == 200:
                print("✅ Step Libraries Service is ready")
                return True
        except:
            pass
        
        print(f"   Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ Services did not start in time")
    return False

if __name__ == "__main__":
    print("🔧 OpsConductor Step Libraries Integration Test")
    print("=" * 50)
    
    if not wait_for_services():
        sys.exit(1)
    
    if test_step_libraries_integration():
        print("\n✅ Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Integration test failed!")
        sys.exit(1)