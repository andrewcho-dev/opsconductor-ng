#!/usr/bin/env python3
"""Quick test of knowledge storage endpoint"""

import requests
import json

def test_knowledge_storage():
    base_url = "http://localhost:3005"
    
    print("Testing AI Knowledge Storage...")
    
    # Check health
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test storing a small piece of knowledge
    test_knowledge = {
        "content": "Docker containers are lightweight, portable units that package applications with their dependencies. Key commands include: docker run, docker ps, docker build, docker push.",
        "category": "containers"
    }
    
    try:
        response = requests.post(
            f"{base_url}/ai/store-knowledge",
            json=test_knowledge,
            timeout=30
        )
        print(f"\n✅ Knowledge storage test: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Knowledge storage failed: {e}")
    
    # Test retrieving/using the knowledge via chat
    chat_test = {
        "message": "What are some key Docker commands?",
        "user_id": 1
    }
    
    try:
        response = requests.post(
            f"{base_url}/ai/chat",
            json=chat_test,
            timeout=30
        )
        print(f"\n✅ Chat test: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   AI Response: {result.get('response', '')[:300]}...")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Chat test failed: {e}")

if __name__ == "__main__":
    test_knowledge_storage()