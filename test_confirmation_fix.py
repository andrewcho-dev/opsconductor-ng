#!/usr/bin/env python3
"""
Test script to verify the AI confirmation loop bug is fixed
"""
import requests
import json
import time

def test_confirmation_flow():
    """Test the confirmation flow works correctly"""
    base_url = "http://localhost:3000/api/v1/ai/chat"
    
    print("🧪 Testing AI Confirmation Flow")
    print("=" * 50)
    
    # Step 1: Initial request
    print("\n1️⃣ Initial automation request")
    payload1 = {
        "message": "create and execute a job to connect to 192.168.50.210 and get a directory listing of drive c:\\",
        "user_id": 1
    }
    
    response1 = requests.post(base_url, json=payload1)
    data1 = response1.json()
    
    print(f"Response: {data1['response'][:100]}...")
    
    if "Should I proceed?" in data1['response']:
        print("✅ Got confirmation prompt as expected")
        conversation_id = data1['conversation_id']
    else:
        print("❌ Expected confirmation prompt")
        return False
    
    # Step 2: Respond with "yes"
    print("\n2️⃣ Responding with 'yes'")
    payload2 = {
        "message": "yes",
        "user_id": 1,
        "conversation_id": conversation_id
    }
    
    response2 = requests.post(base_url, json=payload2)
    data2 = response2.json()
    
    print(f"Response: {data2['response'][:100]}...")
    
    if "Should I proceed?" in data2['response']:
        print("❌ BUG STILL EXISTS: Got confirmation prompt again!")
        return False
    elif "Perfect! I've created" in data2['response'] or "Job ID" in data2['response']:
        print("✅ SUCCESS: AI processed the confirmation and created job!")
        return True
    else:
        print(f"⚠️  Unexpected response: {data2['response'][:200]}...")
        return False

if __name__ == "__main__":
    success = test_confirmation_flow()
    if success:
        print("\n🎉 CONFIRMATION LOOP BUG IS FIXED!")
        print("The AI now properly processes 'yes' responses and creates jobs.")
    else:
        print("\n💥 CONFIRMATION LOOP BUG STILL EXISTS!")
        print("The AI is still stuck in confirmation loop.")