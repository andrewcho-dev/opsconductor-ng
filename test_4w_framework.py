#!/usr/bin/env python3
"""
Test script for the 4W Framework Intent Brain implementation
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

# Import using direct path since ai-brain has hyphens
import importlib.util
spec = importlib.util.spec_from_file_location(
    "intent_brain", 
    "/home/opsconductor/opsconductor-ng/ai-brain/brains/intent_brain/intent_brain.py"
)
intent_brain_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intent_brain_module)
IntentBrain = intent_brain_module.IntentBrain

async def test_4w_framework():
    """Test the 4W framework with various user requests."""
    
    print("🧠 Testing 4W Framework Intent Brain")
    print("=" * 50)
    
    # Initialize the Intent Brain
    intent_brain = IntentBrain()
    
    # Test cases covering different action types
    test_cases = [
        {
            "message": "Check the status of the web server",
            "expected_action": "information",
            "description": "Information request - status check"
        },
        {
            "message": "Install monitoring on the database servers",
            "expected_action": "provisioning", 
            "description": "Provisioning request - install software"
        },
        {
            "message": "The API is returning 500 errors, need help fixing it",
            "expected_action": "diagnostic",
            "description": "Diagnostic request - troubleshoot issue"
        },
        {
            "message": "Restart the nginx service on web01",
            "expected_action": "operational",
            "description": "Operational request - service restart"
        },
        {
            "message": "URGENT: Production database is down!",
            "expected_action": "diagnostic",
            "description": "Critical diagnostic request"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['description']}")
        print(f"Input: '{test_case['message']}'")
        print("-" * 40)
        
        try:
            # Analyze the intent
            result = await intent_brain.analyze_intent(test_case['message'])
            
            # Extract 4W analysis results
            four_w = result.four_w_analysis
            
            print(f"✅ Analysis completed in {result.processing_time:.2f}s")
            print(f"📊 Overall Confidence: {result.overall_confidence:.1%}")
            print()
            
            # Display 4W analysis
            print("🎯 WHAT Analysis:")
            print(f"  Action Type: {four_w.what_analysis.action_type.value}")
            print(f"  Specific Outcome: {four_w.what_analysis.specific_outcome}")
            print(f"  Root Need: {four_w.what_analysis.root_need}")
            print(f"  Confidence: {four_w.what_analysis.confidence:.1%}")
            print()
            
            print("📍 WHERE/WHAT Analysis:")
            print(f"  Target Systems: {four_w.where_what_analysis.target_systems}")
            print(f"  Scope Level: {four_w.where_what_analysis.scope_level.value}")
            print(f"  Confidence: {four_w.where_what_analysis.confidence:.1%}")
            print()
            
            print("⏰ WHEN Analysis:")
            print(f"  Urgency: {four_w.when_analysis.urgency.value}")
            print(f"  Timeline Type: {four_w.when_analysis.timeline_type.value}")
            print(f"  Confidence: {four_w.when_analysis.confidence:.1%}")
            print()
            
            print("🔧 HOW Analysis:")
            print(f"  Method Preference: {four_w.how_analysis.method_preference.value}")
            print(f"  Rollback Needed: {four_w.how_analysis.rollback_needed}")
            print(f"  Testing Required: {four_w.how_analysis.testing_required}")
            print(f"  Confidence: {four_w.how_analysis.confidence:.1%}")
            print()
            
            print("📋 Resource Analysis:")
            print(f"  Resource Complexity: {four_w.resource_complexity}")
            print(f"  Estimated Effort: {four_w.estimated_effort}")
            print(f"  Required Capabilities: {four_w.required_capabilities}")
            print()
            
            print("🎯 Intent Summary:")
            print(f"  {result.intent_summary}")
            print()
            
            print("📝 Recommended Approach:")
            print(f"  {result.recommended_approach}")
            print()
            
            if four_w.missing_information:
                print("❓ Missing Information:")
                for missing in four_w.missing_information:
                    print(f"  - {missing}")
                print()
            
            if four_w.clarifying_questions:
                print("❓ Clarifying Questions:")
                for question in four_w.clarifying_questions:
                    print(f"  - {question}")
                print()
            
            # Verify expected action type
            actual_action = four_w.what_analysis.action_type.value
            expected_action = test_case['expected_action']
            
            if actual_action == expected_action:
                print(f"✅ Action type matches expectation: {actual_action}")
            else:
                print(f"⚠️  Action type mismatch: expected {expected_action}, got {actual_action}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 50)
    
    print("\n🎉 4W Framework testing completed!")

if __name__ == "__main__":
    asyncio.run(test_4w_framework())