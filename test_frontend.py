#!/usr/bin/env python3
"""
Test script for OpsConductor Frontend
Tests that the web interface is accessible and functional
"""

import requests
import json

def test_frontend():
    """Test the frontend web interface"""
    print("🌐 Testing OpsConductor Frontend")
    print("=" * 50)
    
    # Test 1: Main page
    print("\n1. Testing main page (http://localhost)...")
    try:
        response = requests.get("http://localhost", timeout=10)
        if response.status_code == 200:
            print("✅ Main page accessible")
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"   Content-Length: {len(response.text)} bytes")
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main page failed: {e}")
        return False
    
    # Test 2: API Gateway
    print("\n2. Testing API Gateway (http://localhost:3000)...")
    try:
        response = requests.get("http://localhost:3000/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ API Gateway accessible")
            print(f"   Service: {result.get('service', 'Unknown')}")
            print(f"   Status: {result.get('status', 'Unknown')}")
            
            # Show service health
            checks = result.get('checks', [])
            healthy_services = [c['name'] for c in checks if c['status'] == 'healthy']
            unhealthy_services = [c['name'] for c in checks if c['status'] == 'unhealthy']
            
            print(f"   Healthy services: {', '.join(healthy_services)}")
            if unhealthy_services:
                print(f"   Unhealthy services: {', '.join(unhealthy_services)}")
        else:
            print(f"❌ API Gateway failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API Gateway failed: {e}")
    
    # Test 3: Individual Services
    services = [
        ("Identity Service", "http://localhost:3001/health"),
        ("Asset Service", "http://localhost:3002/health"),
        ("Automation Service", "http://localhost:3003/health"),
    ]
    
    print("\n3. Testing individual services...")
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {service_name}: {result.get('status', 'Unknown')}")
            else:
                print(f"   ❌ {service_name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {service_name}: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Frontend testing completed!")
    print("\n📋 Access Information:")
    print("   Main Web Interface: http://localhost")
    print("   API Gateway: http://localhost:3000")
    print("   Identity Service: http://localhost:3001")
    print("   Asset Service: http://localhost:3002")
    print("   Automation Service: http://localhost:3003")
    print("\n📚 API Documentation:")
    print("   Identity API: http://localhost:3001/docs")
    print("   Asset API: http://localhost:3002/docs")
    print("   Automation API: http://localhost:3003/docs")
    
    return True

if __name__ == "__main__":
    test_frontend()