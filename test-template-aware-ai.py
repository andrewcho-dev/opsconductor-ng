#!/usr/bin/env python3
"""
Test script to verify the Template-Aware AI system can properly handle remote probe installations
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the ai-brain directory to the path
sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain')

from job_engine.template_aware_job_creator import TemplateAwareJobCreator
from integrations.llm_client import LLMEngine
from integrations.automation_client import AutomationServiceClient

async def test_template_aware_ai():
    """Test the template-aware AI system"""
    
    print("🧠 Testing Template-Aware AI System")
    print("=" * 60)
    
    try:
        # Initialize components
        print("📋 Initializing AI components...")
        
        # Initialize LLM engine
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
        llm_engine = LLMEngine(ollama_host, default_model)
        
        # Initialize the LLM engine properly
        llm_initialized = await llm_engine.initialize()
        if not llm_initialized:
            print("❌ Failed to initialize LLM engine")
            return
        
        # Initialize automation client
        automation_client = AutomationServiceClient("http://automation-service:3003")
        
        # Initialize template-aware job creator
        job_creator = TemplateAwareJobCreator(llm_engine, automation_client)
        
        print("✅ Components initialized successfully")
        
        # Test 1: Check template knowledge
        print("\n📚 Testing Template Knowledge...")
        knowledge = job_creator.get_template_knowledge_summary()
        print(f"Templates known: {knowledge['templates_known']}")
        print(f"Template files: {knowledge['template_files']}")
        
        # Test 2: List available templates
        print("\n📁 Listing Available Templates...")
        templates = await job_creator._get_available_templates()
        print(f"Found {len(templates)} templates:")
        for template in templates:
            print(f"  - {template['filename']}: {template['name']}")
        
        # Test 3: Test remote probe installation request
        print("\n🚀 Testing Remote Probe Installation Request...")
        
        test_requests = [
            "install remote probe on 192.168.50.211",
            "deploy OpsConductor network probe to 192.168.50.211",
            "setup monitoring probe on windows server 192.168.50.211",
            "I need to install a remote probe on the windows system at 192.168.50.211"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n🔍 Test {i}: '{request}'")
            
            # Test template matching
            template_match = await job_creator._find_matching_template(request, None)
            
            if template_match:
                print(f"✅ Template Match Found:")
                print(f"   Template: {template_match.template_name}")
                print(f"   Confidence: {template_match.confidence:.2f}")
                print(f"   Reasoning: {template_match.reasoning}")
                
                if template_match.confidence >= 0.7:
                    # Test parameter extraction
                    parameters = await job_creator._extract_template_parameters(request, template_match, None)
                    print(f"   Parameters: {json.dumps(parameters, indent=4)}")
                    
                    # Test full job creation (but don't actually execute)
                    print(f"   🎯 This would execute the template with extracted parameters")
                else:
                    print(f"   ⚠️  Confidence too low for execution")
            else:
                print(f"❌ No template match found")
        
        # Test 4: Full job creation test (simulation)
        print("\n🎯 Testing Full Job Creation Process...")
        
        test_request = "install remote probe on 192.168.50.211"
        print(f"Request: '{test_request}'")
        
        # Check automation service health first
        health = await automation_client.health_check()
        print(f"Automation Service Health: {'✅ Healthy' if health else '❌ Unhealthy'}")
        
        if health:
            print("🚀 Executing full job creation...")
            
            # This will actually create and execute the job
            result = await job_creator.create_job_from_natural_language(test_request)
            
            print("📊 Job Creation Result:")
            print(f"   Success: {result.get('success')}")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Execution ID: {result.get('execution_id')}")
            print(f"   Method: {result.get('method', 'unknown')}")
            
            if result.get('template_used'):
                template_info = result['template_used']
                print(f"   Template Used: {template_info['template_name']}")
                print(f"   Template Confidence: {template_info['confidence']:.2f}")
                print(f"   Parameters Applied: {json.dumps(template_info['parameters_applied'], indent=6)}")
            
            if result.get('success'):
                print("✅ Job created and started successfully!")
                print(f"   Response: {result.get('response', 'No response message')}")
            else:
                print(f"❌ Job creation failed: {result.get('error', 'Unknown error')}")
        else:
            print("⚠️  Automation service not available - skipping actual job execution")
        
        print("\n🎉 Template-Aware AI Testing Complete!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_template_aware_ai())