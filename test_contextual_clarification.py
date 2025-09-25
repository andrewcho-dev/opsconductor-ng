#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

async def test_contextual_clarification():
    """Test the contextual clarification system"""
    
    print("🧪 Testing Contextual Clarification System")
    print("=" * 60)
    
    try:
        # Import after setting up the path
        sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain')
        from main import pure_llm_chat_endpoint, ChatRequest, ai_engine
        
        # Test 1: Original request that should trigger clarification
        print("📝 Test 1: Original request (should trigger clarification)")
        print("-" * 60)
        
        original_request = ChatRequest(
            message="Create a recurring job to monitor SFP RX and TX strength values from a Ciena switch",
            conversation_id="test-contextual-clarification",
            user_id=1
        )
        
        result1 = await pure_llm_chat_endpoint(original_request, ai_engine)
        print(f"Intent: {result1.get('intent', 'N/A')}")
        print(f"Clarification Needed: {result1.get('clarification_needed', False)}")
        if result1.get('clarification_needed'):
            print("✅ CORRECTLY ASKED FOR CLARIFICATION")
            print(f"Missing Info: {result1.get('missing_information', [])}")
            print(f"Questions: {result1.get('clarifying_questions', [])}")
        else:
            print("❌ SHOULD HAVE ASKED FOR CLARIFICATION")
        
        print("\n" + "=" * 60)
        
        # Test 2: Follow-up with clarification (should combine contexts)
        print("📝 Test 2: Follow-up with clarification (should combine contexts)")
        print("-" * 60)
        
        followup_request = ChatRequest(
            message="run every day at midnight and trigger if there is less than 10GB left",
            conversation_id="test-contextual-clarification",
            user_id=1
        )
        
        result2 = await pure_llm_chat_endpoint(followup_request, ai_engine)
        print(f"Intent: {result2.get('intent', 'N/A')}")
        print(f"Clarification Needed: {result2.get('clarification_needed', False)}")
        
        if result2.get('clarification_needed'):
            print("❌ STILL ASKING FOR CLARIFICATION - CONTEXT COMBINATION FAILED")
            print(f"Missing Info: {result2.get('missing_information', [])}")
        else:
            print("✅ CLARIFICATION RESOLVED - CONTEXT COMBINATION WORKED!")
            print(f"Intent Type: {result2.get('intent_classification', {}).get('intent_type', 'N/A')}")
            print(f"Confidence: {result2.get('confidence', 'N/A')}")
        
        print(f"\nResponse: {result2.get('response', 'No response')}")
        
        # Test 3: Non-clarification message (should be handled normally)
        print("\n" + "=" * 60)
        print("📝 Test 3: Non-clarification message (should be handled normally)")
        print("-" * 60)
        
        normal_request = ChatRequest(
            message="What is the weather like today?",
            conversation_id="test-contextual-clarification",
            user_id=1
        )
        
        result3 = await pure_llm_chat_endpoint(normal_request, ai_engine)
        print(f"Intent: {result3.get('intent', 'N/A')}")
        print(f"Should be conversation, not clarification: {result3.get('intent', 'N/A') != 'clarification_needed'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_contextual_clarification())