#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng')

# Set up environment
os.environ['PYTHONPATH'] = '/home/opsconductor/opsconductor-ng'

async def test_ai_clarification():
    """Test the AI-powered clarification system"""
    
    print("🧪 Testing AI-Powered Clarification System")
    print("=" * 60)
    
    try:
        from ai_brain.main import chat_with_ai_brain
        from ai_brain.models import ChatRequest
        
        # Test 1: Original request that should trigger clarification
        print("📝 Test 1: Original request (should trigger clarification)")
        print("-" * 60)
        
        original_request = ChatRequest(
            message="Create a recurring job to monitor SFP RX and TX strength values from a Ciena switch",
            conversation_id="test-ai-clarification",
            user_id="test-user"
        )
        
        result1 = await chat_with_ai_brain(original_request)
        print(f"Intent: {result1.get('intent', 'N/A')}")
        print(f"Clarification Needed: {result1.get('clarification_needed', False)}")
        if result1.get('clarification_needed'):
            print("✅ CORRECTLY ASKED FOR CLARIFICATION")
            print(f"Missing Info: {result1.get('missing_information', [])}")
        else:
            print("❌ SHOULD HAVE ASKED FOR CLARIFICATION")
        
        print("\n" + "=" * 60)
        
        # Test 2: Follow-up with clarification (should be detected by AI)
        print("📝 Test 2: Follow-up with clarification (AI should detect)")
        print("-" * 60)
        
        followup_request = ChatRequest(
            message="run every day at midnight and trigger if there is less than 10GB left",
            conversation_id="test-ai-clarification",
            user_id="test-user"
        )
        
        result2 = await chat_with_ai_brain(followup_request)
        print(f"Intent: {result2.get('intent', 'N/A')}")
        print(f"Clarification Needed: {result2.get('clarification_needed', False)}")
        
        if result2.get('clarification_needed'):
            print("❌ STILL ASKING FOR CLARIFICATION - AI DETECTION FAILED")
            print(f"Missing Info: {result2.get('missing_information', [])}")
        else:
            print("✅ CLARIFICATION RESOLVED - AI DETECTION WORKED!")
            print(f"Intent Type: {result2.get('intent_classification', {}).get('intent_type', 'N/A')}")
        
        print(f"\nResponse: {result2.get('response', 'No response')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_clarification())