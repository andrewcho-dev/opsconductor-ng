#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain')

from main import pure_llm_chat_endpoint, ChatRequest

async def test_natural_intent():
    """Test how the LLM naturally interprets different types of requests"""
    
    test_cases = [
        "run echo hello on localhost",
        "execute ls -la on server1", 
        "how does nginx work?",
        "what is the status of server1?",
        "restart the web server",
        "tell me about docker containers",
        "deploy the application to production",
        "can you help me understand kubernetes?"
    ]
    
    print("🧪 Testing Natural Intent Analysis")
    print("=" * 50)
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{message}'")
        print("-" * 40)
        
        try:
            request = ChatRequest(
                message=message,
                conversation_id=f"test-{i}",
                user_id=123
            )
            
            # We need to pass the intent_brain_instance, but for testing we can pass None
            response = await pure_llm_chat_endpoint(request, None)
            
            # Extract key information
            intent_type = "JOB" if response.get("automation_job_id") is not None or response.get("job_id") is not None else "CONVERSATION"
            confidence = response.get("confidence", "unknown")
            
            print(f"   Intent: {intent_type}")
            print(f"   Confidence: {confidence}")
            print(f"   Response preview: {response.get('response', '')[:100]}...")
            
            if response.get("intent_classification"):
                classification = response["intent_classification"]
                print(f"   LLM Classification: {classification.get('intent_type', 'unknown')}")
                print(f"   LLM Reasoning: {classification.get('reasoning', 'none')}")
            
        except Exception as e:
            print(f"   ERROR: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Natural Intent Analysis Test Complete")

if __name__ == "__main__":
    asyncio.run(test_natural_intent())