#!/usr/bin/env python3
"""
Test script for OpsConductor AI Service
Tests basic functionality and AI capabilities
"""

import requests
import json
import time

def test_ai_service():
    """Test the AI service endpoints"""
    base_url = "http://localhost:3005"
    
    print("🤖 Testing OpsConductor AI Service")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Text analysis
    print("\n2. Testing text analysis...")
    try:
        test_text = "The web server on production-server-01 is experiencing high CPU usage and needs immediate attention."
        
        response = requests.post(
            f"{base_url}/analyze-text",
            json={"text": test_text},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Text analysis passed")
            print(f"   Entities found: {len(result.get('entities', []))}")
            print(f"   Intent: {result.get('intent', 'Unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
        else:
            print(f"❌ Text analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Text analysis failed: {e}")
    
    # Test 3: Script generation
    print("\n3. Testing script generation...")
    try:
        request_data = {
            "task_description": "Stop the Apache web server on Windows servers",
            "target_os": "windows",
            "operation_type": "service_management"
        }
        
        response = requests.post(
            f"{base_url}/generate-script",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Script generation passed")
            print(f"   Script type: {result.get('script_type', 'Unknown')}")
            print(f"   Script length: {len(result.get('script', ''))} characters")
            print(f"   Has validation: {bool(result.get('validation_script'))}")
        else:
            print(f"❌ Script generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Script generation failed: {e}")
    
    # Test 4: Task recommendation
    print("\n4. Testing task recommendations...")
    try:
        request_data = {
            "description": "Our website is slow and users are complaining",
            "context": {
                "environment": "production",
                "services": ["web", "database", "cache"]
            }
        }
        
        response = requests.post(
            f"{base_url}/recommend-tasks",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Task recommendations passed")
            print(f"   Recommendations: {len(result.get('recommendations', []))}")
            for i, rec in enumerate(result.get('recommendations', [])[:3]):
                print(f"   {i+1}. {rec.get('title', 'Unknown task')}")
        else:
            print(f"❌ Task recommendations failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Task recommendations failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 AI Service testing completed!")
    return True

if __name__ == "__main__":
    # Wait a bit for service to be ready
    print("Waiting for AI service to be ready...")
    time.sleep(5)
    
    test_ai_service()