#!/usr/bin/env python3
import requests
import json

def test_windows11_query():
    """Test the Windows 11 machine count query to verify AI hallucination fix"""
    
    print("Testing Windows 11 machine count query...")
    print("=" * 60)
    
    response = requests.post(
        "http://localhost:3005/ai/chat",
        json={
            "message": "how many Windows 11 machines do we have?",
            "user_id": 1,
            "conversation_id": "test_windows11"
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print("AI Response:")
        print("=" * 50)
        print(result.get('response', 'No response'))
        print("=" * 50)
        print(f"Intent: {result.get('intent', 'unknown')}")
        print(f"Status: {response.status_code}")
        
        # Check if the response mentions the correct count
        response_text = result.get('response', '').lower()
        
        # Look for clear indicators of the count
        has_one_machine = ('1' in response_text and 'windows 11' in response_text and 'machine' in response_text) or 'exactly 1' in response_text
        
        # Look for problematic indicators (multiple machines, not just multiple sources)
        has_multiple_machines = ('2 windows 11' in response_text or 
                               'multiple windows 11' in response_text or 
                               'several windows 11' in response_text or
                               'windows 11 machines' in response_text and ('2' in response_text or 'multiple' in response_text))
        
        # Look for the key phrase that indicates correct answer
        correct_answer = ('there is **1** windows 11 machine' in response_text or 
                         'there is 1 windows 11 machine' in response_text or
                         'single windows 11 machine' in response_text)
        
        if correct_answer or (has_one_machine and not has_multiple_machines):
            print("\n✅ SUCCESS: AI correctly identified 1 Windows 11 machine")
        elif has_multiple_machines:
            print("\n❌ FAILURE: AI still hallucinating multiple Windows 11 machines")
        else:
            print(f"\n⚠️  UNCLEAR: Response doesn't clearly indicate count - manual review needed")
            print(f"Response text: {response_text[:200]}...")
            
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_windows11_query()