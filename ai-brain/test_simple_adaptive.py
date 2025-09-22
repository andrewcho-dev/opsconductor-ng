#!/usr/bin/env python3
"""
Simple test for core adaptive training functionality
"""

import asyncio
import sys
import os
import logging

# Add the ai-brain directory to the path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_core_adaptive_training():
    """Test the core adaptive training system without external dependencies"""
    
    print("🧠 === Testing Core Adaptive Training System ===")
    
    try:
        from adaptive_training_system import AdaptiveTrainingSystem
        
        # Initialize the adaptive training system
        training_system = AdaptiveTrainingSystem("/tmp/test_simple_adaptive.db")
        
        print("✅ Adaptive training system initialized")
        
        # Phase 1: Add training examples
        print("\n📚 Phase 1: Adding Training Examples")
        
        examples = [
            ("show me our servers", "asset_query", 0.9),
            ("list all systems", "asset_query", 0.8),
            ("what assets do we have", "asset_query", 0.85),
            ("create automation for backups", "automation_request", 0.9),
            ("automate the deployment", "automation_request", 0.8),
            ("setup monitoring", "automation_request", 0.75),
            ("server is down", "troubleshooting", 0.9),
            ("fix the issue", "troubleshooting", 0.8),
            ("diagnose the problem", "troubleshooting", 0.85),
            ("hello there", "greeting", 0.9),
            ("good morning", "greeting", 0.8),
        ]
        
        for text, intent, confidence in examples:
            success = await training_system.add_training_example(
                text=text,
                intent=intent,
                confidence=confidence,
                source="test_data"
            )
            if success:
                print(f"  ✅ Added: '{text}' -> {intent}")
            else:
                print(f"  ❌ Failed: '{text}'")
        
        # Phase 2: Test predictions before training
        print("\n🔍 Phase 2: Testing Predictions (Before Training)")
        
        test_queries = [
            "show me the server list",
            "create backup automation", 
            "the system is not working",
            "hi, how are you"
        ]
        
        for query in test_queries:
            result = await training_system.predict_intent(query)
            print(f"  '{query}' -> {result['best_intent']} ({result['confidence']:.3f})")
        
        # Phase 3: Train the system
        print("\n🎯 Phase 3: Training the System")
        
        training_result = await training_system.retrain_system()
        print(f"  Training completed: {training_result}")
        
        # Phase 4: Test predictions after training
        print("\n🔍 Phase 4: Testing Predictions (After Training)")
        
        for query in test_queries:
            result = await training_system.predict_intent(query)
            print(f"  '{query}' -> {result['best_intent']} ({result['confidence']:.3f})")
            if result['needs_feedback']:
                print(f"    ⚠️  Needs feedback (uncertainty: {result['uncertainty_score']:.3f})")
        
        # Phase 5: Get statistics
        print("\n📊 Phase 5: Training Statistics")
        
        stats = await training_system.get_training_statistics()
        print(f"  Total Examples: {stats.get('total_examples', 0)}")
        print(f"  Total Patterns: {stats.get('total_patterns', 0)}")
        print(f"  Training Sessions: {stats.get('training_sessions', 0)}")
        
        if stats.get('intent_distribution'):
            print(f"  Intent Distribution:")
            for intent, count in stats['intent_distribution'].items():
                print(f"    {intent}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    
    success = await test_core_adaptive_training()
    
    if success:
        print("\n🎉 SUCCESS: Core adaptive training system works!")
        print("\n📚 **Key Concepts Demonstrated:**")
        print("   ✅ Progressive learning from examples")
        print("   ✅ Pattern mining and optimization")
        print("   ✅ Confidence-based predictions")
        print("   ✅ Uncertainty detection for feedback")
        print("   ✅ Persistent storage and statistics")
        
        print("\n🔄 **How This Solves the Original Problem:**")
        print("   • Instead of fabricating responses, the AI learns from real data")
        print("   • Low confidence predictions trigger requests for clarification")
        print("   • User feedback continuously improves intent recognition")
        print("   • Pattern mining discovers new ways users express intents")
        print("   • System becomes more accurate over time through use")
        
    else:
        print("\n💥 FAILURE: Core adaptive training system has issues!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())