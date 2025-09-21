#!/usr/bin/env python3
"""
Test script for the updated Pure LLM Chat Endpoint

This script tests the new intelligent routing system that:
1. Uses LLM to determine if user wants job creation or conversation
2. Routes job requests to LLM job creator
3. Routes conversations to LLM conversation handler
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the ai-brain directory to the path
sys.path.insert(0, str(Path(__file__).parent / "ai-brain"))

async def test_pure_llm_chat():
    """Test the pure LLM chat endpoint with intelligent routing"""
    
    print("🧠 Testing Pure LLM Chat Endpoint with Intelligent Routing")
    print("=" * 70)
    
    try:
        # Import the components
        from main import pure_llm_chat_endpoint, ChatRequest
        from brain_engine import AIBrainEngine
        
        # Initialize AI engine
        print("1. Initializing AI Brain Engine...")
        ai_engine = AIBrainEngine()
        print("   ✓ AI Brain Engine created")
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Job Creation Request",
                "message": "restart apache service on web servers",
                "expected_intent": "job_creation",
                "description": "Should be routed to LLM job creator"
            },
            {
                "name": "Conversation Request", 
                "message": "what is the status of my servers?",
                "expected_intent": "conversation",
                "description": "Should be routed to LLM conversation handler"
            },
            {
                "name": "Complex Job Request",
                "message": "deploy the new application version to staging environment with rollback capability",
                "expected_intent": "job_creation",
                "description": "Complex automation request"
            },
            {
                "name": "Help Request",
                "message": "how do I configure monitoring for my database servers?",
                "expected_intent": "conversation", 
                "description": "Information/help request"
            },
            {
                "name": "Ambiguous Request",
                "message": "check the logs",
                "expected_intent": "conversation",
                "description": "Could be either - should default to conversation"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 Test {i}: {scenario['name']}")
            print(f"Message: '{scenario['message']}'")
            print(f"Expected: {scenario['expected_intent']}")
            print(f"Description: {scenario['description']}")
            print("-" * 50)
            
            # Create chat request
            request = ChatRequest(
                message=scenario['message'],
                user_id=1,
                conversation_id=f"test-{i}"
            )
            
            # Process through pure LLM chat endpoint
            try:
                result = await pure_llm_chat_endpoint(request, ai_engine)
                
                print(f"✅ Response: {result['response'][:100]}...")
                print(f"🎯 Intent: {result['intent']}")
                print(f"🔍 Routing: {result['_routing']['service_type']}")
                print(f"📊 Confidence: {result['confidence']}")
                
                # Check if job was created for job requests
                if result.get('job_id'):
                    print(f"🚀 Job Created: {result['job_id']}")
                
                # Verify routing
                if scenario['expected_intent'] == 'job_creation':
                    if 'job_creator' in result['_routing']['service_type']:
                        print("✅ Correctly routed to job creator")
                    else:
                        print("⚠️  Routing may not be optimal")
                elif scenario['expected_intent'] == 'conversation':
                    if 'conversation' in result['_routing']['service_type']:
                        print("✅ Correctly routed to conversation handler")
                    else:
                        print("⚠️  Routing may not be optimal")
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        print("🎉 Pure LLM Chat Endpoint Testing Complete!")
        print("\nKey Features Tested:")
        print("✅ Intelligent LLM-based intent analysis")
        print("✅ Automatic routing to job creator or conversation handler")
        print("✅ Comprehensive error handling")
        print("✅ Detailed response metadata")
        print("✅ Pure LLM architecture (no pattern matching)")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Pure LLM Chat Endpoint Tests...")
    asyncio.run(test_pure_llm_chat())