#!/usr/bin/env python3

import requests
import json

def test_pure_llm_chat():
    """Test the pure LLM conversation system"""
    
    # AI Brain service endpoint
    url = "http://localhost:3005/ai/chat"
    
    # Test message
    test_message = "Hello! Can you help me set up monitoring for my web servers?"
    
    payload = {
        "message": test_message,
        "user_id": 1
    }
    
    print(f"🚀 Testing Pure LLM Chat System")
    print(f"📤 Sending message: {test_message}")
    print(f"🔗 URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"🤖 AI Response: {data.get('response', 'No response')}")
            print(f"🆔 Conversation ID: {data.get('data', {}).get('conversation_id', 'None')}")
            print(f"🎯 Success: {data.get('success', False)}")
            
            # Check if it's using the LLM conversation handler
            if 'llm_conversation_handler' in str(data):
                print(f"🎉 CONFIRMED: Using Pure LLM Conversation Handler!")
            else:
                print(f"⚠️  Response doesn't indicate LLM handler usage")
                
        else:
            print(f"❌ FAILED!")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST FAILED: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_pure_llm_chat()