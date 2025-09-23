#!/usr/bin/env python3
"""
Test AI probe installation request
"""

import requests
import json

def test_ai_probe_install():
    """Test AI probe installation"""
    
    # AI Brain service endpoint
    ai_url = "http://localhost:3005/ai/chat"
    
    # Test request
    payload = {
        "user_id": 1,
        "message": "Install the OpsConductor remote probe on 192.168.50.211",
        "conversation_id": "test-probe-install"
    }
    
    print("🤖 Testing AI probe installation request...")
    print(f"Request: {payload['message']}")
    
    try:
        response = requests.post(ai_url, json=payload, timeout=60)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AI Response: {result.get('response', 'No response')}")
            print(f"🎯 Intent: {result.get('intent', 'No intent detected')}")
            
            if 'metadata' in result:
                metadata = result['metadata']
                print(f"📋 Processing Time: {metadata.get('processing_time_seconds', 'N/A')}s")
                if 'job_creation' in metadata:
                    print(f"🔧 Job Creation: {metadata['job_creation']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    test_ai_probe_install()