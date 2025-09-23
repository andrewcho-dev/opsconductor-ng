#!/usr/bin/env python3
"""
Demonstration comparing keyword-based vs intent-based AI response systems

This shows the difference between:
1. Current system: Keyword matching to specific automation scripts
2. Proposed system: Intent classification with template-driven response construction
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Current system
from job_engine.template_aware_job_creator import TemplateAwareJobCreator

# Proposed system  
from job_engine.intent_based_response_engine import IntentBasedResponseEngine

from integrations.llm_client import LLMEngine
from integrations.automation_client import AutomationServiceClient

async def demonstrate_approaches():
    """Compare keyword-based vs intent-based approaches"""
    
    print("🔍 AI Response System Comparison")
    print("=" * 60)
    print("Comparing Keyword Matching vs Intent Classification approaches")
    print()
    
    # Initialize both systems
    print("🧠 Initializing AI systems...")
    ollama_host = "http://ollama:11434"
    default_model = "llama3.2:3b"
    llm_engine = LLMEngine(ollama_host, default_model)
    await llm_engine.initialize()
    
    automation_client = AutomationServiceClient("http://automation-service:3003")
    
    # Current keyword-based system
    keyword_system = TemplateAwareJobCreator(llm_engine, automation_client)
    
    # Proposed intent-based system
    intent_system = IntentBasedResponseEngine(llm_engine, automation_client)
    
    print("✅ Both systems initialized")
    
    # Test scenarios that reveal the differences
    test_scenarios = [
        {
            "request": "install remote probe on 192.168.50.211",
            "description": "Basic probe installation - should work in both systems"
        },
        {
            "request": "I need to deploy a monitoring agent to our production server for network analytics",
            "description": "Same intent, different wording - tests flexibility"
        },
        {
            "request": "Can you help me set up network monitoring on our Windows server at 192.168.50.211?",
            "description": "Question format with same underlying intent"
        },
        {
            "request": "Our network monitoring is down, we need to reinstall the probe on 192.168.50.211",
            "description": "Incident context with installation request"
        },
        {
            "request": "What's the status of the probe installation on 192.168.50.211?",
            "description": "Information request - not installation"
        },
        {
            "request": "Install Docker on the web server",
            "description": "Different installation type - no specific template"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"🎯 Scenario {i}: {scenario['description']}")
        print(f"Request: \"{scenario['request']}\"")
        print("-" * 60)
        
        # Test current keyword-based system
        print("\n🔤 CURRENT SYSTEM (Keyword-Based Template Matching):")
        try:
            keyword_match = await keyword_system._find_matching_template(scenario['request'], {})
            if keyword_match and keyword_match.confidence >= 0.7:
                print(f"   ✅ Found template match: {keyword_match.template_name}")
                print(f"   📊 Confidence: {keyword_match.confidence}")
                print(f"   🧠 Reasoning: {keyword_match.reasoning}")
                print(f"   ⚡ Action: Execute specific automation script")
            else:
                print(f"   ❌ No template match found")
                print(f"   ⚡ Action: Fall back to generic LLM workflow generation")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test proposed intent-based system
        print("\n🧠 PROPOSED SYSTEM (Intent-Based Response Construction):")
        try:
            intent = await intent_system.analyze_intent(scenario['request'])
            print(f"   🎯 Intent: {intent.primary_category.value}.{intent.subcategory.value}")
            print(f"   📊 Confidence: {intent.confidence}")
            print(f"   🧠 Reasoning: {intent.reasoning}")
            print(f"   📝 Entities: {intent.extracted_entities}")
            print(f"   🔍 Context: {intent.context_factors}")
            
            # Show what the response construction would do
            if intent.confidence >= 0.7:
                print(f"   ⚡ Action: Use {intent.primary_category.value} response template")
                print(f"      • Execute analysis framework")
                print(f"      • Extract/validate parameters") 
                print(f"      • Apply confidence thresholds")
                print(f"      • Choose appropriate response strategy")
            else:
                print(f"   ⚡ Action: Request clarification (low confidence)")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("📊 COMPARISON SUMMARY")
    print("-" * 60)
    
    print("\n🔤 KEYWORD-BASED SYSTEM:")
    print("   ✅ Pros:")
    print("      • Simple and fast")
    print("      • Works well for exact matches")
    print("      • Direct mapping to automation scripts")
    print("   ❌ Cons:")
    print("      • Brittle - fails with different wording")
    print("      • No understanding of intent or context")
    print("      • Hard to extend to new scenarios")
    print("      • Binary match/no-match decisions")
    
    print("\n🧠 INTENT-BASED SYSTEM:")
    print("   ✅ Pros:")
    print("      • Understands intent regardless of wording")
    print("      • Flexible response construction")
    print("      • Confidence-based decision making")
    print("      • Extensible framework for new intents")
    print("      • Context-aware analysis")
    print("      • ITIL-aligned categorization")
    print("   ❌ Cons:")
    print("      • More complex to implement")
    print("      • Requires more LLM calls")
    print("      • Needs comprehensive template library")
    
    print("\n🎯 RECOMMENDATION:")
    print("   The intent-based approach provides:")
    print("   • True understanding vs pattern matching")
    print("   • Structured response construction")
    print("   • Confidence-based safeguards")
    print("   • Extensible architecture")
    print("   • Better handling of edge cases")

if __name__ == "__main__":
    asyncio.run(demonstrate_approaches())