#!/usr/bin/env python3
"""
Test script to debug job creation pipeline
"""
import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng/shared')

from job_engine.llm_job_creator import LLMJobCreator
from integrations.llm_client import LLMEngine
from integrations.automation_client import AutomationServiceClient

async def test_job_creation():
    """Test the job creation pipeline with debugging"""
    
    # Initialize components
    llm_engine = LLMEngine(ollama_host="http://ollama:11434", default_model="llama3.2:latest")
    await llm_engine.initialize()
    automation_client = AutomationServiceClient(automation_service_url="http://automation-service:3003")
    job_creator = LLMJobCreator(llm_engine, automation_client)
    
    # Test request
    description = "Create a job to restart nginx service on server 192.168.1.100"
    
    print(f"🧪 Testing job creation for: {description}")
    
    try:
        # Test each stage individually
        print("\n📊 STAGE 1: Analysis")
        analysis = await job_creator._analyze_request(description, {})
        if analysis:
            print(f"✅ Analysis successful: {analysis.intent_type}")
            print(f"   Risk level: {analysis.risk_level}")
            print(f"   Target systems: {analysis.target_systems}")
        else:
            print("❌ Analysis failed")
            return
        
        print("\n📋 STAGE 2: Planning")
        plan = await job_creator._generate_plan(description, analysis, {})
        if plan:
            print(f"✅ Plan generated: {plan.workflow_type}")
            print(f"   Steps: {len(plan.steps)}")
            print(f"   Dependencies: {plan.dependencies}")
        else:
            print("❌ Planning failed")
            return
            
        print("\n🔍 STAGE 3: Validation")
        validation = await job_creator._validate_plan(description, analysis, plan, {})
        print(f"   Is valid: {validation.is_valid}")
        print(f"   Safety score: {validation.safety_score}")
        print(f"   Warnings: {validation.warnings}")
        print(f"   Recommendations: {validation.recommendations}")
        
        if not validation.is_valid:
            print("❌ Validation failed - this is where the pipeline stops")
            print("   Let's try to create the job anyway...")
            
            # Try to create the job bypassing validation
            print("\n🚀 STAGE 4: Job Creation (bypassing validation)")
            result = await job_creator._create_executable_job(description, analysis, plan, validation, {})
            print(f"   Job creation result: {result}")
        else:
            print("✅ Validation passed")
            
            print("\n🚀 STAGE 4: Job Creation")
            result = await job_creator._create_executable_job(description, analysis, plan, validation, {})
            print(f"   Job creation result: {result}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_job_creation())