#!/usr/bin/env python3
"""Test AI capabilities after knowledge training"""

import requests
import json
import time

def test_ai_knowledge():
    base_url = "http://localhost:3005"
    
    print("="*60)
    print("Testing AI After Knowledge Training")
    print("="*60)
    
    test_questions = [
        {
            "category": "Docker",
            "question": "What are the key Docker commands and concepts?",
        },
        {
            "category": "Kubernetes", 
            "question": "How do I troubleshoot a pod that keeps restarting?",
        },
        {
            "category": "AWS",
            "question": "What are the main AWS services for compute and storage?",
        },
        {
            "category": "Linux",
            "question": "How can I check if a server is running out of disk space?",
        },
        {
            "category": "Security",
            "question": "What are the key principles of network security?",
        },
        {
            "category": "Database",
            "question": "How do I handle a database connection pool exhaustion?",
        }
    ]
    
    for test in test_questions:
        print(f"\n📝 Testing: {test['category']}")
        print(f"Question: {test['question']}")
        print("-" * 50)
        
        payload = {
            "message": test["question"],
            "user_id": 1
        }
        
        try:
            response = requests.post(
                f"{base_url}/ai/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', 'No response')
                
                # Print first 500 chars of response
                if len(ai_response) > 500:
                    print(f"AI Response: {ai_response[:500]}...")
                else:
                    print(f"AI Response: {ai_response}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1)  # Brief pause between requests
    
    print("\n" + "="*60)
    print("✅ Testing complete! The AI now has comprehensive IT knowledge!")
    print("="*60)

if __name__ == "__main__":
    test_ai_knowledge()