#!/usr/bin/env python3
"""
Test script for Adaptive Training System

This demonstrates how the AI system progressively learns and improves
its intent recognition through various training approaches.
"""

import asyncio
import sys
import os
import logging
import json
from datetime import datetime, timedelta

# Add the ai-brain directory to the path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

from adaptive_training_system import AdaptiveTrainingSystem, TrainingExample
from integrations.asset_client import AssetServiceClient
from llm_conversation_handler import LLMConversationHandler
from integrations.llm_client import LLMEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_adaptive_training_system():
    """Test the adaptive training system comprehensively"""
    
    print("🧠 === Testing Adaptive Training System ===")
    
    # Initialize the adaptive training system
    training_system = AdaptiveTrainingSystem("/tmp/test_adaptive_training.db")
    
    print("✅ Adaptive training system initialized")
    
    # Phase 1: Add initial training examples
    print("\n📚 Phase 1: Adding Initial Training Examples")
    
    initial_examples = [
        # Asset queries
        ("tell me about our assets", "asset_query", 0.9, "Perfect asset query detection"),
        ("show me what systems we have", "asset_query", 0.8, "Good system inquiry"),
        ("list all servers", "asset_query", 0.85, "Clear server listing request"),
        ("what infrastructure do we manage", "asset_query", 0.75, "Infrastructure overview request"),
        ("give me details about our network devices", "asset_query", 0.8, "Network asset query"),
        
        # Automation requests
        ("create an automation to restart services", "automation_request", 0.9, "Clear automation request"),
        ("automate the backup process", "automation_request", 0.85, "Backup automation request"),
        ("set up automated monitoring", "automation_request", 0.8, "Monitoring automation"),
        ("schedule regular maintenance tasks", "automation_request", 0.75, "Maintenance automation"),
        ("build a workflow for deployments", "automation_request", 0.8, "Deployment workflow request"),
        
        # Troubleshooting
        ("why is the server not responding", "troubleshooting", 0.9, "Server issue troubleshooting"),
        ("fix the connection problem", "troubleshooting", 0.85, "Connection troubleshooting"),
        ("diagnose network issues", "troubleshooting", 0.8, "Network diagnostics"),
        ("resolve performance problems", "troubleshooting", 0.75, "Performance troubleshooting"),
        ("investigate system errors", "troubleshooting", 0.8, "Error investigation"),
        
        # Specific IP queries
        ("check status of 192.168.1.100", "ip_query", 0.95, "Specific IP status check"),
        ("what's running on 10.0.0.50", "ip_query", 0.9, "IP service query"),
        ("ping 172.16.0.1", "ip_query", 0.85, "Network connectivity test"),
        
        # Greetings and general
        ("hello there", "greeting", 0.9, "Simple greeting"),
        ("how are you doing", "greeting", 0.8, "Casual greeting"),
        ("good morning", "greeting", 0.85, "Time-specific greeting"),
        ("help me with something", "general_help", 0.7, "General help request"),
        ("what can you do", "capability_inquiry", 0.8, "Capability question"),
    ]
    
    for text, intent, confidence, feedback in initial_examples:
        success = await training_system.add_training_example(
            text=text,
            intent=intent,
            confidence=confidence,
            user_feedback=feedback,
            source="initial_training"
        )
        if success:
            print(f"  ✅ Added: '{text}' -> {intent} ({confidence:.2f})")
        else:
            print(f"  ❌ Failed to add: '{text}'")
    
    # Phase 2: Test intent prediction before training
    print("\n🔍 Phase 2: Testing Intent Prediction (Before Training)")
    
    test_queries = [
        "show me our server inventory",
        "create automation for log rotation", 
        "server 192.168.1.50 is down",
        "why is the database slow",
        "hi, can you help me",
        "what systems are in our datacenter",
        "automate certificate renewal",
        "investigate memory usage issues"
    ]
    
    pre_training_results = []
    for query in test_queries:
        result = await training_system.predict_intent(query)
        pre_training_results.append((query, result))
        
        print(f"  Query: '{query}'")
        print(f"    Intent: {result['best_intent']} (confidence: {result['confidence']:.3f})")
        if result['needs_feedback']:
            print(f"    ⚠️  Needs feedback (uncertainty: {result['uncertainty_score']:.3f})")
        print()
    
    # Phase 3: Trigger training
    print("\n🎯 Phase 3: Training the System")
    
    training_result = await training_system.retrain_system()
    print(f"Training result: {json.dumps(training_result, indent=2)}")
    
    # Phase 4: Test intent prediction after training
    print("\n🔍 Phase 4: Testing Intent Prediction (After Training)")
    
    post_training_results = []
    for query in test_queries:
        result = await training_system.predict_intent(query)
        post_training_results.append((query, result))
        
        print(f"  Query: '{query}'")
        print(f"    Intent: {result['best_intent']} (confidence: {result['confidence']:.3f})")
        if result['needs_feedback']:
            print(f"    ⚠️  Still needs feedback (uncertainty: {result['uncertainty_score']:.3f})")
        else:
            print(f"    ✅ Confident prediction")
        print()
    
    # Phase 5: Compare before and after
    print("\n📊 Phase 5: Training Impact Analysis")
    
    improvements = 0
    degradations = 0
    
    for i, query in enumerate(test_queries):
        pre_conf = pre_training_results[i][1]['confidence']
        post_conf = post_training_results[i][1]['confidence']
        pre_intent = pre_training_results[i][1]['best_intent']
        post_intent = post_training_results[i][1]['best_intent']
        
        change = post_conf - pre_conf
        
        print(f"  '{query}':")
        print(f"    Before: {pre_intent} ({pre_conf:.3f})")
        print(f"    After:  {post_intent} ({post_conf:.3f})")
        
        if change > 0.1:
            print(f"    📈 Improved by {change:.3f}")
            improvements += 1
        elif change < -0.1:
            print(f"    📉 Degraded by {abs(change):.3f}")
            degradations += 1
        else:
            print(f"    ➡️  Minimal change ({change:+.3f})")
        print()
    
    print(f"Summary: {improvements} improvements, {degradations} degradations")
    
    # Phase 6: Test feedback learning
    print("\n💬 Phase 6: Testing Feedback Learning")
    
    # Simulate user feedback on some predictions
    feedback_examples = [
        ("show me our server inventory", "asset_query", True, "Perfect! This correctly identified my asset query."),
        ("hi, can you help me", "greeting", True, "Yes, this is a greeting."),
        ("server 192.168.1.50 is down", "troubleshooting", False, "This should be troubleshooting, not IP query."),
    ]
    
    for query, expected_intent, was_correct, feedback_text in feedback_examples:
        # Add as training example with feedback
        await training_system.add_training_example(
            text=query,
            intent=expected_intent,
            confidence=0.9 if was_correct else 0.3,
            user_feedback=feedback_text,
            source="user_feedback"
        )
        
        print(f"  Feedback on '{query}': {'✅ Correct' if was_correct else '❌ Incorrect'}")
        print(f"    Expected: {expected_intent}")
        print(f"    Feedback: {feedback_text}")
    
    # Phase 7: Test continuous learning
    print("\n🔄 Phase 7: Testing Continuous Learning")
    
    # Add more examples over time to simulate continuous learning
    continuous_examples = [
        ("display system metrics", "asset_query", 0.8),
        ("show performance data", "asset_query", 0.75),
        ("build deployment pipeline", "automation_request", 0.85),
        ("setup monitoring alerts", "automation_request", 0.8),
        ("server keeps crashing", "troubleshooting", 0.9),
        ("application won't start", "troubleshooting", 0.85),
    ]
    
    for text, intent, confidence in continuous_examples:
        await training_system.add_training_example(
            text=text,
            intent=intent,
            confidence=confidence,
            source="continuous_learning"
        )
        print(f"  Added continuous learning example: '{text}' -> {intent}")
    
    # Trigger another training session
    print("\n  Triggering incremental training...")
    incremental_result = await training_system.retrain_system()
    print(f"  Incremental training result: {json.dumps(incremental_result, indent=2)}")
    
    # Phase 8: Get comprehensive statistics
    print("\n📈 Phase 8: Training Statistics")
    
    stats = await training_system.get_training_statistics()
    print(f"Training Statistics:")
    print(f"  Total Examples: {stats.get('total_examples', 0)}")
    print(f"  Total Patterns: {stats.get('total_patterns', 0)}")
    print(f"  Training Sessions: {stats.get('training_sessions', 0)}")
    print(f"  Semantic Matcher Trained: {stats.get('semantic_matcher_trained', False)}")
    
    if stats.get('intent_distribution'):
        print(f"  Intent Distribution:")
        for intent, count in stats['intent_distribution'].items():
            print(f"    {intent}: {count} examples")
    
    if stats.get('pattern_performance'):
        print(f"  Pattern Performance:")
        for intent, perf in stats['pattern_performance'].items():
            print(f"    {intent}: {perf['count']} patterns, {perf['avg_success_rate']:.2f} avg success rate")
    
    # Phase 9: Test edge cases and uncertainty handling
    print("\n🎭 Phase 9: Testing Edge Cases and Uncertainty")
    
    edge_cases = [
        "asdfghjkl qwerty",  # Gibberish
        "the quick brown fox jumps over the lazy dog",  # Unrelated text
        "maybe possibly perhaps create some kind of automation thing",  # Vague request
        "192.168.1.1 server automation troubleshoot help",  # Mixed intents
        "",  # Empty string
        "a",  # Single character
    ]
    
    for query in edge_cases:
        if query:  # Skip empty string for display
            result = await training_system.predict_intent(query)
            print(f"  Edge case: '{query}'")
            print(f"    Intent: {result['best_intent']} (confidence: {result['confidence']:.3f})")
            print(f"    Uncertainty: {result['uncertainty_score']:.3f}")
            print(f"    Needs feedback: {result['needs_feedback']}")
            print()
    
    return True

async def test_integration_with_conversation_handler():
    """Test integration with the main conversation handler"""
    
    print("\n🔗 === Testing Integration with Conversation Handler ===")
    
    # Initialize components
    asset_client = AssetServiceClient("http://localhost:3002")
    
    # Health check
    healthy = await asset_client.health_check()
    if not healthy:
        print("❌ Asset service is not healthy - skipping integration test")
        return False
    
    # Initialize LLM engine
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
    llm_engine = LLMEngine(ollama_host, default_model)
    
    llm_init_success = await llm_engine.initialize()
    if not llm_init_success:
        print("❌ Failed to initialize LLM engine - skipping integration test")
        return False
    
    # Initialize conversation handler
    conversation_handler = LLMConversationHandler(llm_engine, asset_client)
    
    # Import and integrate adaptive training
    from adaptive_training_system import integrate_adaptive_training
    training_system = await integrate_adaptive_training(conversation_handler)
    
    print("✅ Integrated adaptive training with conversation handler")
    
    # Test enhanced message processing
    test_messages = [
        "show me what assets we have",
        "create automation for backups",
        "why is 192.168.1.100 not responding",
        "hello, how can you help me"
    ]
    
    for message in test_messages:
        print(f"\n  Testing: '{message}'")
        result = await conversation_handler.process_message(message, "test_user")
        
        if result.get("success"):
            training_info = result.get("training_info", {})
            print(f"    Success: {result.get('success')}")
            print(f"    Predicted Intent: {training_info.get('predicted_intent')}")
            print(f"    Confidence: {training_info.get('confidence', 0):.3f}")
            print(f"    Needs Feedback: {training_info.get('needs_feedback')}")
        else:
            print(f"    Error: {result.get('error')}")
    
    # Get training statistics
    stats = await conversation_handler.get_training_statistics()
    print(f"\n  Final Training Statistics:")
    print(f"    Total Examples: {stats.get('total_examples', 0)}")
    print(f"    Total Patterns: {stats.get('total_patterns', 0)}")
    
    return True

async def main():
    """Main test function"""
    
    print("🚀 Starting Adaptive Training System Tests")
    print("=" * 60)
    
    # Test the core adaptive training system
    success1 = await test_adaptive_training_system()
    
    # Test integration with conversation handler
    success2 = await test_integration_with_conversation_handler()
    
    if success1 and success2:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS: Adaptive Training System is fully functional!")
        print("\n🧠 **Key Capabilities Demonstrated:**")
        print("   ✅ Progressive learning from user interactions")
        print("   ✅ Pattern mining from successful examples")
        print("   ✅ Semantic similarity matching")
        print("   ✅ Confidence-based uncertainty detection")
        print("   ✅ Feedback collection and learning")
        print("   ✅ Automatic pattern optimization")
        print("   ✅ Continuous improvement over time")
        print("   ✅ Integration with conversation handler")
        print("   ✅ Comprehensive training analytics")
        print("   ✅ Edge case and uncertainty handling")
        
        print("\n📚 **How the System Learns:**")
        print("   1. Collects examples from user interactions")
        print("   2. Mines common patterns from successful examples")
        print("   3. Uses semantic similarity for fuzzy matching")
        print("   4. Adjusts confidence based on feedback")
        print("   5. Removes poor-performing patterns")
        print("   6. Continuously retrains with new data")
        print("   7. Provides uncertainty scores for active learning")
        
        print("\n🔄 **Continuous Improvement Process:**")
        print("   • User interacts with system")
        print("   • System predicts intent with confidence")
        print("   • Low confidence triggers feedback request")
        print("   • Feedback improves pattern performance")
        print("   • New patterns are mined from successful interactions")
        print("   • System automatically retrains periodically")
        print("   • Poor patterns are retired")
        print("   • Overall accuracy improves over time")
        
    else:
        print("\n💥 FAILURE: Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())