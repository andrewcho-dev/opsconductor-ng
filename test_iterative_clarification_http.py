#!/usr/bin/env python3
"""
Test the iterative clarification system via HTTP requests to the running AI brain service.
This tests that the system properly combines original requests with clarification responses
and re-analyzes iteratively.
"""

import requests
import json
import time

def test_iterative_clarification():
    """Test the iterative clarification system via HTTP"""
    
    print("🧪 TESTING ITERATIVE CLARIFICATION SYSTEM (HTTP)")
    print("=" * 60)
    
    base_url = "http://localhost:3005"
    conversation_id = f"test-iterative-clarification-{int(time.time())}"
    
    # Test 1: Original request that should need clarification
    print("\n1️⃣ STEP 1: Original request (should need clarification)")
    original_request = {
        "message": "create a job that runs every day to check the remaining disk space on each windows machine and warns if it is critical",
        "conversation_id": conversation_id,
        "user_id": 123
    }
    
    try:
        response1 = requests.post(f"{base_url}/ai/chat", json=original_request)
        response1.raise_for_status()
        data1 = response1.json()
        
        print(f"✅ Response 1: {data1.get('response', 'No response')[:200]}...")
        print(f"🔍 Clarification needed: {data1.get('clarification_needed', False)}")
        print(f"🔍 Missing info: {data1.get('missing_information', [])}")
        print(f"🔍 Intent: {data1.get('intent', 'Unknown')}")
        print(f"🔍 Confidence: {data1.get('confidence', 0)}")
        
        if data1.get('clarification_needed', False):
            print(f"✅ System correctly identified need for clarification")
            print(f"🔍 Clarifying questions: {data1.get('clarifying_questions', [])}")
        else:
            print(f"⚠️ System did not identify need for clarification - this might be expected if the request is complete")
            
    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        return
    
    print("\n" + "="*60)
    
    # Test 2: Clarification response (should combine with original)
    print("\n2️⃣ STEP 2: Clarification response (should combine with original)")
    clarification_request = {
        "message": "run every day at midnight and trigger if there is less than 10GB left",
        "conversation_id": conversation_id,
        "user_id": 123
    }
    
    try:
        response2 = requests.post(f"{base_url}/ai/chat", json=clarification_request)
        response2.raise_for_status()
        data2 = response2.json()
        
        print(f"✅ Response 2: {data2.get('response', 'No response')[:200]}...")
        print(f"🔍 Clarification needed: {data2.get('clarification_needed', False)}")
        print(f"🔍 Missing info: {data2.get('missing_information', [])}")
        print(f"🔍 Intent: {data2.get('intent', 'Unknown')}")
        print(f"🔍 Confidence: {data2.get('confidence', 0)}")
        
        # Check if the system properly combined the contexts
        if "midnight" in data2.get('response', '') or "10GB" in data2.get('response', ''):
            print(f"✅ System appears to have combined original request with clarification")
        else:
            print(f"⚠️ System may not have combined contexts properly")
            
    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        return
    
    print("\n" + "="*60)
    
    # Test 3: If still needs clarification, test another round
    if data2.get('clarification_needed', False):
        print("\n3️⃣ STEP 3: Additional clarification needed - testing iterative flow")
        additional_clarification = {
            "message": "send email alerts to admin@company.com",
            "conversation_id": conversation_id,
            "user_id": 123
        }
        
        try:
            response3 = requests.post(f"{base_url}/ai/chat", json=additional_clarification)
            response3.raise_for_status()
            data3 = response3.json()
            
            print(f"✅ Response 3: {data3.get('response', 'No response')[:200]}...")
            print(f"🔍 Clarification needed: {data3.get('clarification_needed', False)}")
            print(f"🔍 Missing info: {data3.get('missing_information', [])}")
            print(f"🔍 Intent: {data3.get('intent', 'Unknown')}")
            print(f"🔍 Confidence: {data3.get('confidence', 0)}")
            
        except Exception as e:
            print(f"❌ Step 3 failed: {e}")
    else:
        print("\n3️⃣ STEP 3: No additional clarification needed - system completed analysis")
    
    print("\n" + "="*60)
    print("🎯 ITERATIVE CLARIFICATION TEST COMPLETE")
    
    # Test 4: Test with a completely new conversation to ensure isolation
    print("\n4️⃣ STEP 4: Testing conversation isolation")
    new_conversation_id = f"test-new-conversation-{int(time.time())}"
    new_request = {
        "message": "hello",
        "conversation_id": new_conversation_id,
        "user_id": 123
    }
    
    try:
        response4 = requests.post(f"{base_url}/ai/chat", json=new_request)
        response4.raise_for_status()
        data4 = response4.json()
        
        print(f"✅ New conversation response: {data4.get('response', 'No response')[:100]}...")
        print(f"🔍 Should not reference previous conversation context")
        
        # Check that it doesn't reference disk space, midnight, etc.
        response_text = data4.get('response', '').lower()
        if any(word in response_text for word in ['disk', 'midnight', '10gb', 'windows']):
            print(f"❌ New conversation appears to have leaked context from previous conversation")
        else:
            print(f"✅ New conversation properly isolated from previous context")
            
    except Exception as e:
        print(f"❌ Step 4 failed: {e}")

if __name__ == "__main__":
    test_iterative_clarification()