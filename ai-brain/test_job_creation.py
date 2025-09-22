#!/usr/bin/env python3
"""
Simple test script to test job creation without all the initialization overhead
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

# Mock the LLM engine to avoid Ollama dependency
class MockLLMEngine:
    def __init__(self, *args, **kwargs):
        pass
    
    async def chat(self, message, system_prompt=None, model=None):
        """Mock LLM responses for testing"""
        print(f"🔍 Mock LLM called with message: {message[:50]}...")
        print(f"🔍 System prompt: {system_prompt[:100] if system_prompt else 'None'}...")
        if "analyze" in message.lower() or "intent_type" in system_prompt:
            print("🔍 Mock LLM: Analysis request detected")
            return {
                "response": '''```json
{
    "intent_type": "service_management",
    "confidence": 0.95,
    "requirements": {
        "description": "Restart nginx service on server1",
        "targets": ["server1"],
        "actions": ["restart_service"],
        "parameters": {"service": "nginx"},
        "conditions": []
    },
    "target_systems": ["server1"],
    "risk_level": "low",
    "complexity": "simple",
    "estimated_duration": "2-5 minutes",
    "required_permissions": ["service_management"],
    "dependencies": [],
    "rollback_required": true
}
```'''
            }
        elif "workflow" in message.lower() or "steps" in system_prompt:
            print("🔍 Mock LLM: Planning request detected")
            return {
                "response": '''```json
{
    "workflow_type": "service_management",
    "steps": [
        {
            "id": "step_1",
            "name": "Check service status",
            "action": "check_service_status",
            "parameters": {"service": "nginx", "target": "server1"},
            "timeout": 30,
            "retry_count": 2
        },
        {
            "id": "step_2", 
            "name": "Restart nginx service",
            "action": "restart_service",
            "parameters": {"service": "nginx", "target": "server1"},
            "timeout": 60,
            "retry_count": 1
        },
        {
            "id": "step_3",
            "name": "Verify service is running",
            "action": "check_service_status",
            "parameters": {"service": "nginx", "target": "server1"},
            "timeout": 30,
            "retry_count": 2
        }
    ],
    "dependencies": [],
    "rollback_plan": [
        {
            "id": "rollback_1",
            "name": "Start nginx if stopped",
            "action": "start_service", 
            "parameters": {"service": "nginx", "target": "server1"}
        }
    ],
    "estimated_duration": "3 minutes",
    "risk_assessment": "Low risk - standard service restart"
}
```'''
            }
        elif "validate" in message.lower() or (system_prompt and ("validator" in system_prompt or "safety" in system_prompt)):
            print("🔍 Mock LLM: Validation request detected")
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
        elif "executable" in message.lower() or "automation" in system_prompt:
            return {
                "response": '''```json
{
    "job_id": "job_12345",
    "name": "Restart nginx on server1",
    "description": "Automated restart of nginx service on server1",
    "workflow_type": "service_management",
    "target_systems": ["server1"],
    "steps": [
        {
            "id": "step_1",
            "name": "Check service status",
            "action": "check_service_status",
            "parameters": {"service": "nginx", "target": "server1"},
            "timeout": 30
        },
        {
            "id": "step_2",
            "name": "Restart nginx service", 
            "action": "restart_service",
            "parameters": {"service": "nginx", "target": "server1"},
            "timeout": 60
        },
        {
            "id": "step_3",
            "name": "Verify service is running",
            "action": "check_service_status", 
            "parameters": {"service": "nginx", "target": "server1"},
            "timeout": 30
        }
    ],
    "schedule": "immediate",
    "priority": "medium",
    "timeout": 300,
    "retry_policy": {"max_retries": 2, "retry_delay": 30},
    "notifications": {"on_success": true, "on_failure": true},
    "rollback_plan": [
        {
            "id": "rollback_1",
            "name": "Start nginx if stopped",
            "action": "start_service",
            "parameters": {"service": "nginx", "target": "server1"}
        }
    ]
}
```'''
            }
        else:
            return {"response": "Mock response"}

# Patch the LLM engine import BEFORE importing the job creator
import sys
sys.modules['integrations.llm_client'] = type(sys)('mock_llm_client')
sys.modules['integrations.llm_client'].LLMEngine = MockLLMEngine

# Now import the job creator
from job_engine.llm_job_creator import LLMJobCreator

async def test_job_creation():
    """Test the job creation pipeline"""
    print("🚀 Testing OpsConductor Job Creation Pipeline")
    print("=" * 50)
    
    # Create job creator with mock LLM
    mock_llm = MockLLMEngine()
    job_creator = LLMJobCreator(mock_llm)
    
    # Test request
    request = "restart nginx service on server1"
    print(f"📝 Request: {request}")
    print()
    
    try:
        # Create the job
        print("🔄 Creating job...")
        result = await job_creator.create_job_from_natural_language(request)
        
        print("✅ Job Creation Result:")
        print(json.dumps(result, indent=2))
        
        if result.get("success"):
            print("\n🎉 SUCCESS: Job created successfully!")
            print(f"Job ID: {result.get('job_id', 'N/A')}")
            print(f"Steps: {len(result.get('steps', []))}")
        else:
            print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            if result.get('warnings'):
                print(f"Warnings: {result['warnings']}")
            if result.get('recommendations'):
                print(f"Recommendations: {result['recommendations']}")
                
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_job_creation())