#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng')

from ai_brain.main import chat_with_ai_brain
from ai_brain.models import ChatRequest

async def test_clarification_followup():
    """Test the clarification follow-up system with the user's response"""
    
    print("🧪 Testing Clarification Follow-up System")
    print("=" * 60)
    
    # Test the user's follow-up message
    followup_message = "run every day at midnight and trigger if there is less than 10GB left"
    
    print(f"📝 Testing follow-up message: '{followup_message}'")
    print("-" * 60)
    
    request = ChatRequest(
        message=followup_message,
        conversation_id="test-clarification-followup",
        user_id="test-user"
    )
    
    try:
        result = await chat_with_ai_brain(request)
        
        print("✅ Follow-up Response:")
        print(f"Intent: {result.get('intent', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 'N/A')}")
        print(f"Clarification Needed: {result.get('clarification_needed', False)}")
        
        if result.get('clarification_needed'):
            print("❌ STILL ASKING FOR CLARIFICATION!")
            print(f"Missing Info: {result.get('missing_information', [])}")
            print(f"Questions: {result.get('clarifying_questions', [])}")
        else:
            print("✅ CLARIFICATION RESOLVED!")
            print(f"Intent Type: {result.get('intent_classification', {}).get('intent_type', 'N/A')}")
        
        print(f"\nResponse: {result.get('response', 'No response')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_clarification_followup())