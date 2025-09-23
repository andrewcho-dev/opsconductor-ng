#!/usr/bin/env python3
"""
Test AI knowledge about remote probe installation
"""

import requests
import json

def test_ai_knowledge():
    """Test AI knowledge about remote probe installation"""
    
    # AI Brain service endpoint
    ai_url = "http://localhost:3005/ai/chat"
    
    questions = [
        "What do you know about OpsConductor remote probe installation?",
        "How do you install a remote probe on Windows?",
        "What automation jobs are available for remote probe deployment?",
        "Do you know about the install-windows-remote-probe.json job template?",
        "What steps are involved in installing a remote probe on 192.168.50.211?",
        "Can you list the existing automation job templates?",
        "What is the proper way to deploy a remote probe using automation?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"🤖 Question {i}: {question}")
        print('='*60)
        
        payload = {
            "user_id": 1,
            "message": question,
            "conversation_id": f"test-knowledge-{i}"
        }
        
        try:
            response = requests.post(ai_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ AI Response:")
                print(result.get('response', 'No response'))
                
                if 'intent' in result:
                    print(f"\n🎯 Intent: {result['intent']}")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    test_ai_knowledge()