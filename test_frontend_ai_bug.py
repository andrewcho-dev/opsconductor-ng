#!/usr/bin/env python3
"""
Test script to reproduce the AI confirmation loop bug from the frontend perspective.
This simulates exactly what the frontend does when a user interacts with the AI chat.
"""

import requests
import json
import time
import sys

# Configuration
API_BASE_URL = "http://localhost:3000"  # API Gateway
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/ai/chat"

def make_chat_request(message, conversation_id=None, user_id=1):
    """Make a chat request exactly like the frontend does"""
    payload = {
        "message": message,
        "user_id": user_id
    }
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"\n🔄 Sending request to {CHAT_ENDPOINT}")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload, headers=headers, timeout=30)
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📥 Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_confirmation_loop_bug():
    """Test the specific confirmation loop bug scenario"""
    print("🧪 Testing AI Confirmation Loop Bug")
    print("=" * 60)
    
    # Step 1: Initial automation request
    print("\n1️⃣ STEP 1: Initial automation request")
    response1 = make_chat_request("create and execute a job to connect to 192.168.50.210 and get a directory listing of drive c:\\")
    
    if not response1:
        print("❌ Failed to get initial response")
        return False
    
    conversation_id = response1.get("conversation_id")
    if not conversation_id:
        print("❌ No conversation_id in response")
        return False
    
    print(f"✅ Got conversation_id: {conversation_id}")
    
    # Check if this is asking for confirmation
    if "Should I proceed" not in response1.get("response", ""):
        print("❌ Expected confirmation prompt, but didn't get one")
        print(f"Got response: {response1.get('response')}")
        return False
    
    print("✅ Got confirmation prompt as expected")
    
    # Step 2: First "yes" response
    print("\n2️⃣ STEP 2: First 'yes' response")
    time.sleep(1)  # Small delay to simulate user thinking
    response2 = make_chat_request("yes", conversation_id=conversation_id)
    
    if not response2:
        print("❌ Failed to get response to first 'yes'")
        return False
    
    # This should execute the job
    if "already being processed" in response2.get("response", "").lower():
        print("❌ BUG DETECTED: Got 'already being processed' on first 'yes'")
        return False
    
    print("✅ First 'yes' processed correctly")
    
    # Step 3: Second "yes" response (this should NOT create another confirmation loop)
    print("\n3️⃣ STEP 3: Second 'yes' response (testing for bug)")
    time.sleep(1)
    response3 = make_chat_request("yes", conversation_id=conversation_id)
    
    if not response3:
        print("❌ Failed to get response to second 'yes'")
        return False
    
    # This should NOT ask for confirmation again
    if "Should I proceed" in response3.get("response", ""):
        print("🐛 BUG CONFIRMED: Got confirmation prompt again on second 'yes'")
        print(f"Response: {response3.get('response')}")
        return False
    
    # This SHOULD say already completed or similar
    response_text = response3.get("response", "").lower()
    if "already been completed" in response_text or "already completed" in response_text:
        print("✅ FIXED: Got 'already completed' message as expected")
        return True
    
    print(f"⚠️  Unexpected response to second 'yes': {response3.get('response')}")
    return False

def test_multiple_yes_responses():
    """Test multiple 'yes' responses to ensure no infinite loop"""
    print("\n🧪 Testing Multiple 'yes' Responses")
    print("=" * 60)
    
    # Initial request
    response1 = make_chat_request("create and execute a job to connect to 192.168.50.210 and get a directory listing of drive c:\\")
    if not response1:
        return False
    
    conversation_id = response1.get("conversation_id")
    if not conversation_id:
        return False
    
    # First yes
    response2 = make_chat_request("yes", conversation_id=conversation_id)
    if not response2:
        return False
    
    # Test multiple additional "yes" responses
    for i in range(3, 8):  # Test 5 more "yes" responses
        print(f"\n{i}️⃣ STEP {i}: Additional 'yes' response #{i-2}")
        time.sleep(0.5)
        response = make_chat_request("yes", conversation_id=conversation_id)
        
        if not response:
            print(f"❌ Failed to get response to 'yes' #{i-2}")
            return False
        
        # Should get "already being processed" message
        if "Should I proceed" in response.get("response", ""):
            print(f"🐛 BUG: Got confirmation prompt on 'yes' #{i-2}")
            return False
        
        if "already being processed" not in response.get("response", "").lower():
            print(f"⚠️  Unexpected response to 'yes' #{i-2}: {response.get('response')}")
    
    print("✅ All additional 'yes' responses handled correctly")
    return True

def main():
    print("🚀 Frontend AI Bug Test Suite")
    print("Testing the AI confirmation loop bug from frontend perspective")
    print("=" * 80)
    
    # Test basic confirmation loop bug
    bug_test_passed = test_confirmation_loop_bug()
    
    if not bug_test_passed:
        print("\n❌ CONFIRMATION LOOP BUG TEST FAILED")
        print("The bug is still present in the system!")
        sys.exit(1)
    
    # Test multiple yes responses
    multiple_test_passed = test_multiple_yes_responses()
    
    if not multiple_test_passed:
        print("\n❌ MULTIPLE YES RESPONSES TEST FAILED")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("🎉 The AI confirmation loop bug appears to be FIXED!")
    print("=" * 80)

if __name__ == "__main__":
    main()