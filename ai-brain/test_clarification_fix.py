#!/usr/bin/env python3
"""
Test script to verify the clarification fix for the fulfillment engine
"""

import asyncio
import sys
import os
import logging

# Add the ai-brain directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brains.intent_brain.intent_analyzer import IntentAnalyzer

# Mock LLM Engine for testing
class MockLLMEngine:
    def __init__(self, response_text="CLEAR"):
        self.response_text = response_text
    
    async def generate(self, prompt):
        print(f"🤖 LLM Prompt:\n{prompt}")
        print(f"🤖 LLM Response: {self.response_text}")
        return {"generated_text": self.response_text}

async def test_clarification_scenarios():
    """Test various scenarios to ensure clarification logic works correctly"""
    
    print("🧪 Testing Intent Analyzer Clarification Logic")
    print("=" * 60)
    
    # Test scenarios
    test_cases = [
        {
            "message": "create a job that pings 192.168.50.210 every 10 seconds",
            "expected_clear": True,
            "description": "Clear ping job request"
        },
        {
            "message": "monitor disk space on server1",
            "expected_clear": True,
            "description": "Clear monitoring request"
        },
        {
            "message": "check if nginx is running every 5 minutes",
            "expected_clear": True,
            "description": "Clear service check request"
        },
        {
            "message": "do something",
            "expected_clear": False,
            "description": "Vague request needing clarification"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"📝 Message: '{test_case['message']}'")
        
        # Mock LLM to return CLEAR for clear requests, UNCLEAR for vague ones
        if test_case['expected_clear']:
            mock_llm = MockLLMEngine("CLEAR")
        else:
            mock_llm = MockLLMEngine("UNCLEAR\nWhat specific action would you like to perform?")
        
        analyzer = IntentAnalyzer(llm_engine=mock_llm)
        
        try:
            needs_clarification, questions = await analyzer.needs_clarification(test_case['message'])
            
            if test_case['expected_clear']:
                if not needs_clarification:
                    print("✅ PASS: Request correctly identified as clear")
                else:
                    print(f"❌ FAIL: Request incorrectly needs clarification: {questions}")
            else:
                if needs_clarification:
                    print(f"✅ PASS: Request correctly needs clarification: {questions}")
                else:
                    print("❌ FAIL: Vague request incorrectly identified as clear")
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("🎯 Clarification test completed!")

async def test_with_real_llm():
    """Test with a real LLM call to see actual behavior"""
    print("\n🧪 Testing with Real LLM (if available)")
    print("=" * 60)
    
    # Try to import and use the real LLM engine
    try:
        from llm_engine.llm_engine import LLMEngine
        
        # Initialize real LLM engine
        llm_engine = LLMEngine()
        analyzer = IntentAnalyzer(llm_engine=llm_engine)
        
        test_message = "create a job that pings 192.168.50.210 every 10 seconds"
        print(f"📝 Testing message: '{test_message}'")
        
        needs_clarification, questions = await analyzer.needs_clarification(test_message)
        
        print(f"🤖 Needs clarification: {needs_clarification}")
        if questions:
            print(f"❓ Questions: {questions}")
        
        if not needs_clarification:
            print("✅ SUCCESS: Clear request properly identified!")
        else:
            print("❌ ISSUE: Clear request still asking for clarification")
            
    except Exception as e:
        print(f"⚠️  Could not test with real LLM: {e}")
        print("This is expected if LLM engine is not properly configured")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(test_clarification_scenarios())
    asyncio.run(test_with_real_llm())