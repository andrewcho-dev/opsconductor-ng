#!/usr/bin/env python3

import requests
import json

def test_ai_service():
    base_url = "http://localhost:3005"
    
    print("🧪 Testing AI Service...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    # Test script generation
    print("\n2. Testing script generation...")
    try:
        payload = {
            "request": "Write a simple Python function to calculate factorial",
            "language": "python"
        }
        response = requests.post(f"{base_url}/ai/generate-script", json=payload, timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Generated script preview: {result.get('script', '')[:200]}...")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test chat endpoint
    print("\n3. Testing chat endpoint...")
    try:
        payload = {
            "message": "Hello! Can you help me with system automation?",
            "user_id": 1
        }
        response = requests.post(f"{base_url}/ai/chat", json=payload, timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Chat response preview: {result.get('response', '')[:200]}...")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test job creation
    print("\n4. Testing job creation...")
    try:
        payload = {
            "description": "Restart Apache service on web servers",
            "user_id": 1,
            "priority": "normal"
        }
        response = requests.post(f"{base_url}/ai/create-job", json=payload, timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ AI Service testing completed!")
    return True

if __name__ == "__main__":
    test_ai_service()