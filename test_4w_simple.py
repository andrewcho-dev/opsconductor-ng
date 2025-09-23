#!/usr/bin/env python3
"""
Simple test for the 4W Framework components
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain/brains/intent_brain')

# Import the 4W analyzer directly
from four_w_analyzer import FourWAnalyzer, ActionType

async def test_4w_analyzer():
    """Test the 4W analyzer directly."""
    
    print("🧠 Testing 4W Framework Analyzer")
    print("=" * 50)
    
    # Initialize the 4W analyzer
    analyzer = FourWAnalyzer()
    
    # Test cases
    test_cases = [
        {
            "message": "Check the status of the web server",
            "expected_action": ActionType.INFORMATION,
            "description": "Information request - status check"
        },
        {
            "message": "Install monitoring on the database servers",
            "expected_action": ActionType.PROVISIONING, 
            "description": "Provisioning request - install software"
        },
        {
            "message": "The API is returning 500 errors, need help fixing it",
            "expected_action": ActionType.DIAGNOSTIC,
            "description": "Diagnostic request - troubleshoot issue"
        },
        {
            "message": "Restart the nginx service on web01",
            "expected_action": ActionType.OPERATIONAL,
            "description": "Operational request - service restart"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['description']}")
        print(f"Input: '{test_case['message']}'")
        print("-" * 40)
        
        try:
            # Analyze the intent using 4W framework
            result = await analyzer.analyze_4w(test_case['message'])
            
            print(f"✅ Analysis completed in {result.processing_time:.2f}s")
            print(f"📊 Overall Confidence: {result.overall_confidence:.1%}")
            print()
            
            # Display 4W analysis
            print("🎯 WHAT Analysis:")
            print(f"  Action Type: {result.what_analysis.action_type.value}")
            print(f"  Specific Outcome: {result.what_analysis.specific_outcome}")
            print(f"  Root Need: {result.what_analysis.root_need}")
            print(f"  Confidence: {result.what_analysis.confidence:.1%}")
            print()
            
            print("📍 WHERE/WHAT Analysis:")
            print(f"  Target Systems: {result.where_what_analysis.target_systems}")
            print(f"  Scope Level: {result.where_what_analysis.scope_level.value}")
            print(f"  Confidence: {result.where_what_analysis.confidence:.1%}")
            print()
            
            print("⏰ WHEN Analysis:")
            print(f"  Urgency: {result.when_analysis.urgency.value}")
            print(f"  Timeline Type: {result.when_analysis.timeline_type.value}")
            print(f"  Confidence: {result.when_analysis.confidence:.1%}")
            print()
            
            print("🔧 HOW Analysis:")
            print(f"  Method Preference: {result.how_analysis.method_preference.value}")
            print(f"  Rollback Needed: {result.how_analysis.rollback_needed}")
            print(f"  Testing Required: {result.how_analysis.testing_required}")
            print(f"  Confidence: {result.how_analysis.confidence:.1%}")
            print()
            
            print("📋 Resource Analysis:")
            print(f"  Resource Complexity: {result.resource_complexity}")
            print(f"  Estimated Effort: {result.estimated_effort}")
            print(f"  Required Capabilities: {result.required_capabilities}")
            print()
            
            if result.missing_information:
                print("❓ Missing Information:")
                for missing in result.missing_information:
                    print(f"  - {missing}")
                print()
            
            if result.clarifying_questions:
                print("❓ Clarifying Questions:")
                for question in result.clarifying_questions:
                    print(f"  - {question}")
                print()
            
            # Verify expected action type
            actual_action = result.what_analysis.action_type
            expected_action = test_case['expected_action']
            
            if actual_action == expected_action:
                print(f"✅ Action type matches expectation: {actual_action.value}")
            else:
                print(f"⚠️  Action type mismatch: expected {expected_action.value}, got {actual_action.value}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 50)
    
    print("\n🎉 4W Framework testing completed!")

if __name__ == "__main__":
    asyncio.run(test_4w_analyzer())