#!/usr/bin/env python3
"""
Test the iterative clarification system to ensure it properly combines
original requests with clarification responses and re-analyzes iteratively.
"""

import asyncio
import sys
import os

# Add the project root to Python path
project_root = '/home/opsconductor/opsconductor-ng'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add ai-brain directory to path
ai_brain_path = os.path.join(project_root, 'ai-brain')
if ai_brain_path not in sys.path:
    sys.path.insert(0, ai_brain_path)

from main import pure_llm_chat_endpoint, _conversation_contexts, ChatRequest

async def test_iterative_clarification():
    """Test the iterative clarification system"""
    
    print("🧪 TESTING ITERATIVE CLARIFICATION SYSTEM")
    print("=" * 60)
    
    # Test 1: Original request that needs clarification
    print("\n1️⃣ STEP 1: Original request (should need clarification)")
    original_request = ChatRequest(
        message="create a job that runs every day to check the remaining disk space on each windows machine and warns if it is critical",
        conversation_id="test-iterative-clarification",
        user_id=123
    )
    
    try:
        # We need to create a mock AI engine for testing
        class MockAIEngine:
            def __init__(self):
                self.llm_engine = None
                
        ai_engine = MockAIEngine()
        response1 = await pure_llm_chat_endpoint(original_request, ai_engine)
        print(f"✅ Response 1: {response1.get('response', 'No response')[:200]}...")
        print(f"🔍 Clarification needed: {response1.get('clarification_needed', False)}")
        print(f"🔍 Missing info: {response1.get('missing_information', [])}")
        
        # Check if context was stored
        conversation_id = "test-iterative-clarification"
        if conversation_id in _conversation_contexts:
            print(f"✅ Context stored for conversation {conversation_id}")
            stored_context = _conversation_contexts[conversation_id]
            print(f"🔍 Awaiting clarification: {stored_context.get('awaiting_clarification', False)}")
            print(f"🔍 Original message stored: {stored_context.get('original_message', 'None')[:100]}...")
        else:
            print(f"❌ No context stored for conversation {conversation_id}")
            return
            
    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        return
    
    print("\n" + "="*60)
    
    # Test 2: Clarification response (should combine with original)
    print("\n2️⃣ STEP 2: Clarification response (should combine with original)")
    clarification_request = ChatRequest(
        message="run every day at midnight and trigger if there is less than 10GB left",
        conversation_id="test-iterative-clarification",
        user_id=123
    )
    
    try:
        response2 = await pure_llm_chat_endpoint(clarification_request, ai_engine)
        print(f"✅ Response 2: {response2.get('response', 'No response')[:200]}...")
        print(f"🔍 Clarification needed: {response2.get('clarification_needed', False)}")
        print(f"🔍 Missing info: {response2.get('missing_information', [])}")
        
        # Check if context was updated/cleared
        if conversation_id in _conversation_contexts:
            stored_context = _conversation_contexts[conversation_id]
            print(f"🔍 Still awaiting clarification: {stored_context.get('awaiting_clarification', False)}")
        else:
            print(f"✅ Context cleared for conversation {conversation_id} (analysis complete)")
            
    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        return
    
    print("\n" + "="*60)
    
    # Test 3: If still needs clarification, test another round
    if response2.get('clarification_needed', False):
        print("\n3️⃣ STEP 3: Additional clarification needed - testing iterative flow")
        additional_clarification = ChatRequest(
            message="send email alerts to admin@company.com",
            conversation_id="test-iterative-clarification", 
            user_id=123
        )
        
        try:
            response3 = await pure_llm_chat_endpoint(additional_clarification, ai_engine)
            print(f"✅ Response 3: {response3.get('response', 'No response')[:200]}...")
            print(f"🔍 Clarification needed: {response3.get('clarification_needed', False)}")
            print(f"🔍 Missing info: {response3.get('missing_information', [])}")
            
        except Exception as e:
            print(f"❌ Step 3 failed: {e}")
    
    print("\n" + "="*60)
    print("🎯 ITERATIVE CLARIFICATION TEST COMPLETE")
    
    # Show final context state
    print(f"\n📊 Final context state:")
    if conversation_id in _conversation_contexts:
        print(f"🔍 Context still exists: {_conversation_contexts[conversation_id]}")
    else:
        print(f"✅ Context properly cleaned up")

if __name__ == "__main__":
    asyncio.run(test_iterative_clarification())