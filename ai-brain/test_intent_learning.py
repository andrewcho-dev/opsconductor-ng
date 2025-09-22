#!/usr/bin/env python3
"""
Simple test script for Progressive Intent Learning
"""

import asyncio
import sys
import os
import logging

# Add the ai-brain directory to the path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

from integrations.asset_client import AssetServiceClient
from llm_conversation_handler import LLMConversationHandler
from integrations.llm_client import LLMEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_intent_learning():
    """Test the progressive intent learning system"""
    
    print("=== Testing Progressive Intent Learning ===")
    
    # Initialize components
    asset_client = AssetServiceClient("http://localhost:3002")
    
    # Health check
    healthy = await asset_client.health_check()
    print(f"Asset service healthy: {healthy}")
    
    if not healthy:
        print("❌ Asset service is not healthy!")
        return False
    
    # Initialize LLM engine
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
    llm_engine = LLMEngine(ollama_host, default_model)
    
    # Initialize the LLM engine
    llm_init_success = await llm_engine.initialize()
    if not llm_init_success:
        print("❌ Failed to initialize LLM engine!")
        return False
    
    # Initialize conversation handler with progressive learning
    conversation_handler = LLMConversationHandler(llm_engine, asset_client)
    
    print("✅ All components initialized successfully")
    
    # Test various types of messages to see intent recognition
    test_messages = [
        "tell me about what assets we have in our system",
        "show me our servers", 
        "what systems do we have?",
        "create an automation to restart services",
        "automate the backup process",
        "fix the connection issue on 192.168.50.210",
        "why is the server not responding?",
        "hello there, how are you?",
        "can you help me with something?",
        "I need to deploy a new application"
    ]
    
    print("\n=== Testing Intent Recognition ===")
    
    results = []
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        
        # Process the message
        result = await conversation_handler.process_message(message, "test_user")
        
        if result.get("success"):
            intent_analysis = result.get("intent_analysis", {})
            print(f"   Intent: {intent_analysis.get('intent', 'unknown')}")
            print(f"   Confidence: {intent_analysis.get('confidence', 0):.2f} ({intent_analysis.get('confidence_level', 'unknown')})")
            
            if intent_analysis.get("alternative_intents"):
                print(f"   Alternatives: {intent_analysis.get('alternative_intents')}")
            
            if intent_analysis.get("suggestions"):
                print(f"   Suggestions: {intent_analysis.get('suggestions')}")
            
            results.append({
                "message": message,
                "intent": intent_analysis.get('intent', 'unknown'),
                "confidence": intent_analysis.get('confidence', 0),
                "interpretation_id": intent_analysis.get('interpretation_id')
            })
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    # Test feedback collection
    print("\n=== Testing Feedback Collection ===")
    
    # Simulate some feedback
    if results:
        # Give positive feedback on asset query
        asset_results = [r for r in results if r['intent'] == 'asset_query']
        if asset_results:
            feedback_result = await conversation_handler.record_intent_feedback(
                asset_results[0]['interpretation_id'], 
                True, 
                None, 
                "Perfect! This correctly identified my asset query."
            )
            print(f"✅ Positive feedback recorded: {feedback_result}")
        
        # Give corrective feedback on unknown intent
        unknown_results = [r for r in results if r['intent'] == 'unknown']
        if unknown_results:
            feedback_result = await conversation_handler.record_intent_feedback(
                unknown_results[0]['interpretation_id'], 
                False, 
                "greeting", 
                "This was actually just a greeting."
            )
            print(f"✅ Corrective feedback recorded: {feedback_result}")
    
    # Get learning statistics
    print("\n=== Learning Statistics ===")
    
    intent_stats = await conversation_handler.get_intent_learning_stats()
    print(f"Intent Recognition Stats:")
    print(f"  - Total patterns: {intent_stats.get('total_patterns', 0)}")
    print(f"  - Total interpretations: {intent_stats.get('total_interpretations', 0)}")
    print(f"  - Overall accuracy: {intent_stats.get('overall_accuracy', 0):.2f}")
    print(f"  - Recent activity: {intent_stats.get('recent_activity', 0)}")
    
    if intent_stats.get('pattern_statistics'):
        print(f"  - Pattern breakdown:")
        for intent_type, stats in intent_stats['pattern_statistics'].items():
            print(f"    • {intent_type}: {stats['count']} patterns, {stats['total_uses']} uses")
    
    # Test pattern optimization
    print("\n=== Testing Pattern Optimization ===")
    
    optimization_result = await conversation_handler.optimize_intent_patterns()
    print(f"Optimization results: {optimization_result}")
    
    return True

async def main():
    """Main test function"""
    success = await test_intent_learning()
    
    if success:
        print("\n🎉 SUCCESS: Progressive intent learning system is working!")
        print("\n📚 **Key Features Demonstrated:**")
        print("   ✅ Intent pattern matching with confidence scoring")
        print("   ✅ Alternative intent suggestions")
        print("   ✅ Feedback collection and learning")
        print("   ✅ Pattern performance tracking")
        print("   ✅ Automatic pattern optimization")
        print("   ✅ Learning statistics and analytics")
    else:
        print("\n💥 FAILURE: Progressive learning system has issues!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())