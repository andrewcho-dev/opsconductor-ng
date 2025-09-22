#!/usr/bin/env python3
"""
Simple test to debug the validation issue
"""
import asyncio
import sys
import os
import json
import logging
from datetime import datetime

# Enable debug logging
logging.basicConfig(level=logging.INFO)

# Add the current directory to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

# Create a simple mock that just returns validation success
class SimpleMockLLMEngine:
    def __init__(self, *args, **kwargs):
        pass
    
    async def chat(self, message, system_prompt=None, model=None):
        print(f"🔍 LLM called with message: {message[:100]}...")
        print(f"🔍 System prompt contains: {'validator' if system_prompt and 'validator' in system_prompt else 'other'}")
        
        # Always return validation success
        return {
            "response": '''```json
{
    "is_valid": true,
    "safety_score": 0.85,
    "warnings": ["Service restart may cause brief downtime"],
    "recommendations": ["Consider maintenance window for production systems"],
    "required_approvals": []
}
```'''
        }

# Import and patch
from job_engine.llm_job_creator import JobAnalysis, JobPlan, JobValidation, LLMJobCreator

async def test_validation_only():
    """Test just the validation step"""
    print("🚀 Testing Validation Step Only")
    print("=" * 40)
    
    # Create mock LLM and job creator
    mock_llm = SimpleMockLLMEngine()
    job_creator = LLMJobCreator(mock_llm)
    
    # Create mock analysis and plan
    analysis = JobAnalysis(
        intent_type="service_management",
        confidence=0.95,
        requirements={"service": "nginx", "target": "server1"},
        target_systems=["server1"],
        risk_level="low",
        complexity="simple",
        estimated_duration="2-5 minutes"
    )
    
    plan = JobPlan(
        workflow_type="service_management",
        steps=[
            {"id": "step_1", "name": "Restart nginx", "action": "restart_service"}
        ],
        dependencies=[],
        validation_checks=[],
        rollback_plan=[]
    )
    
    print("📝 Testing validation with mock data...")
    
    try:
        # Test validation directly
        validation = await job_creator._validate_plan("restart nginx", analysis, plan, None)
        
        print(f"✅ Validation Result:")
        print(f"  - is_valid: {validation.is_valid}")
        print(f"  - safety_score: {validation.safety_score}")
        print(f"  - warnings: {validation.warnings}")
        print(f"  - recommendations: {validation.recommendations}")
        
        if validation.is_valid:
            print("\n🎉 SUCCESS: Validation passed!")
        else:
            print("\n❌ FAILED: Validation failed")
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_validation_only())