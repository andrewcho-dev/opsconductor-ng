#!/usr/bin/env python3
"""
Test script for Progressive Intent Learning System
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
from training_system import AITrainingSystem, TrainingMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_progressive_learning():
    """Test the progressive learning system"""
    
    print("=== Testing Progressive Intent Learning System ===")
    
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
    
    # Initialize training system
    training_system = AITrainingSystem(conversation_handler)
    
    print("✅ All components initialized successfully")
    
    # Start a training session
    session_id = await training_system.start_training_session(
        TrainingMode.ACTIVE, 
        "Testing progressive learning capabilities"
    )
    print(f"✅ Started training session: {session_id}")
    
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
            
            # Process for learning
            learning_result = await training_system.process_interaction_for_learning(
                message, result.get("response", ""), "test_user", intent_analysis, session_id
            )
            
            if learning_result.get("should_request_feedback"):
                print(f"   🔄 System suggests requesting feedback")
            
            if learning_result.get("learning_opportunities"):
                print(f"   📚 Learning opportunities: {len(learning_result['learning_opportunities'])}")
                for opp in learning_result["learning_opportunities"]:
                    print(f"      - {opp['type']}: {opp['description']}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    # Test feedback collection
    print("\n=== Testing Feedback Collection ===")
    
    # Simulate user feedback on some interactions
    feedback_examples = [
        {
            "type": "satisfaction",
            "rating": 5,
            "comment": "Perfect response!"
        },
        {
            "type": "intent_correction", 
            "interpretation_id": "test_id",
            "correct_intent": "asset_query",
            "comment": "I was asking about assets, not automation"
        },
        {
            "type": "suggestion",
            "suggestion": "Could you provide more detailed asset information?"
        }
    ]
    
    for feedback in feedback_examples:
        result = await training_system.collect_user_feedback("test_interaction", feedback)
        print(f"✅ Processed {feedback['type']} feedback: {result.get('improvements_made', [])}")
    
    # Get learning statistics
    print("\n=== Learning Statistics ===")
    
    intent_stats = await conversation_handler.get_intent_learning_stats()
    print(f"Intent Recognition Stats:")
    print(f"  - Total patterns: {intent_stats.get('total_patterns', 0)}")
    print(f"  - Total interpretations: {intent_stats.get('total_interpretations', 0)}")
    print(f"  - Overall accuracy: {intent_stats.get('overall_accuracy', 0):.2f}")
    
    training_stats = training_system.get_training_statistics()
    print(f"\nTraining System Stats:")
    print(f"  - Total sessions: {training_stats.get('total_training_sessions', 0)}")
    print(f"  - User patterns: {training_stats.get('total_user_patterns', 0)}")
    
    # Test pattern optimization
    print("\n=== Testing Pattern Optimization ===")
    
    optimization_result = await training_system.auto_optimize_system()
    print(f"Optimizations applied: {optimization_result.get('optimizations_applied', [])}")
    
    # Generate training report
    print("\n=== Training Report ===")
    
    report = await training_system.generate_training_report(days=1)
    print(f"Training Report (last 1 day):")
    print(f"  - Sessions: {report['training_sessions']['total_sessions']}")
    print(f"  - Interactions: {report['training_sessions']['total_interactions']}")
    print(f"  - Feedback rate: {report['training_sessions']['feedback_rate']:.2f}")
    
    if report.get("recommendations"):
        print(f"  - Recommendations:")
        for rec in report["recommendations"]:
            print(f"    • {rec}")
    
    # End training session
    session_result = await training_system.end_training_session(session_id)
    print(f"\n✅ Training session completed: {session_result}")
    
    return True

async def main():
    """Main test function"""
    success = await test_progressive_learning()
    
    if success:
        print("\n🎉 SUCCESS: Progressive learning system is working!")
    else:
        print("\n💥 FAILURE: Progressive learning system has issues!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())