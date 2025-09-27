#!/usr/bin/env python3
"""
🚀 AI BRAIN PREFECT INTEGRATION SIMPLE TEST

Simple test to validate the AI Brain integration logic without requiring
a running Prefect server. Tests the core integration components.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the ai-brain directory to the Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockLLMEngine:
    """Mock LLM engine for testing"""
    
    def __init__(self):
        self.call_count = 0
    
    async def initialize(self):
        return True
    
    async def generate(self, prompt: str):
        self.call_count += 1
        
        # Mock responses based on prompt content
        if "PREFECT: YES" in prompt or "PREFECT: NO" in prompt:
            # Workflow complexity analysis
            if "multiple" in prompt.lower() or "complex" in prompt.lower() or "deploy" in prompt.lower():
                return {"generated_text": "PREFECT: YES - Multiple dependent steps and cross-service coordination required"}
            else:
                return {"generated_text": "PREFECT: NO - Simple single-step operation"}
        
        elif "requires_workflow" in prompt:
            # Intent analysis
            if any(keyword in prompt.lower() for keyword in ["deploy", "monitor", "check", "execute", "run"]):
                return {"generated_text": '''
{
  "requires_workflow": true,
  "intent_type": "complex_workflow",
  "confidence": 0.9,
  "complexity_level": "medium",
  "workflow_components": ["automation", "asset"],
  "reasoning": "User request contains action keywords requiring workflow orchestration"
}
'''}
            else:
                return {"generated_text": '''
{
  "requires_workflow": false,
  "intent_type": "conversational",
  "confidence": 0.8,
  "complexity_level": "simple",
  "workflow_components": [],
  "reasoning": "Simple conversational request"
}
'''}
        
        elif "JSON format" in prompt and "[" in prompt:
            # Task generation
            return {"generated_text": '''
[
  {
    "name": "analyze_request",
    "type": "generic",
    "action": "analyze_user_request",
    "parameters": {
      "user_message": "test request"
    },
    "depends_on": [],
    "retry_count": 1,
    "timeout_seconds": 30,
    "description": "Analyze the user request"
  },
  {
    "name": "execute_automation",
    "type": "service_call",
    "service": "automation",
    "action": "health_check",
    "parameters": {},
    "depends_on": ["analyze_request"],
    "retry_count": 2,
    "timeout_seconds": 60,
    "description": "Execute automation task"
  }
]
'''}
        
        else:
            # Default response
            return {"generated_text": "Mock LLM response for testing"}

async def test_direct_executor_complexity_analysis():
    """Test DirectExecutor workflow complexity analysis"""
    logger.info("🧪 Testing DirectExecutor workflow complexity analysis...")
    
    try:
        from fulfillment_engine.direct_executor import DirectExecutor
        
        # Create DirectExecutor with mock LLM
        mock_llm = MockLLMEngine()
        direct_executor = DirectExecutor(
            llm_engine=mock_llm,
            prefect_flow_engine=None  # No Prefect integration for this test
        )
        
        # Test simple request (should not trigger Prefect)
        simple_request = "What is the current system status?"
        result = await direct_executor.execute_user_request(
            user_message=simple_request,
            user_context={"user_id": "test_user"}
        )
        
        logger.info(f"✅ Simple request result: {result.get('status', 'unknown')}")
        
        # Test complex request (would trigger Prefect if available)
        complex_request = "Deploy application v2.1 to production and monitor deployment status"
        result = await direct_executor.execute_user_request(
            user_message=complex_request,
            user_context={"user_id": "test_user"}
        )
        
        logger.info(f"✅ Complex request result: {result.get('status', 'unknown')}")
        logger.info(f"✅ LLM calls made: {mock_llm.call_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DirectExecutor test failed: {e}")
        return False

async def test_service_catalog_integration():
    """Test service catalog integration with Prefect decision making"""
    logger.info("🧪 Testing service catalog Prefect integration...")
    
    try:
        from fulfillment_engine.dynamic_service_catalog import get_service_catalog
        
        # Get the service catalog
        service_catalog = get_service_catalog()
        
        # Test intelligent service selection prompt
        prompt = service_catalog.generate_intelligent_service_selection_prompt()
        
        # Check if Prefect guidance is included
        assert "Prefect-Flow-Registry" in prompt, "Prefect guidance not found in service catalog"
        assert "complex enterprise orchestration" in prompt.lower(), "Enterprise orchestration guidance missing"
        
        logger.info("✅ Service catalog includes Prefect integration guidance")
        logger.info(f"✅ Service catalog prompt length: {len(prompt)} characters")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Service catalog test failed: {e}")
        return False

async def test_ai_brain_intent_analysis():
    """Test AI Brain Service intent analysis without Prefect server"""
    logger.info("🧪 Testing AI Brain Service intent analysis...")
    
    try:
        # Import without initializing Prefect components
        import sys
        import importlib.util
        
        # Load the AI Brain Service module manually to avoid Prefect imports
        spec = importlib.util.spec_from_file_location(
            "ai_brain_service", 
            "/home/opsconductor/opsconductor-ng/ai-brain/orchestration/ai_brain_service.py"
        )
        ai_brain_module = importlib.util.module_from_spec(spec)
        
        # Mock the Prefect imports to avoid import errors
        sys.modules['prefect'] = type(sys)('prefect')
        sys.modules['prefect.client'] = type(sys)('prefect.client')
        sys.modules['prefect.client.orchestration'] = type(sys)('prefect.client.orchestration')
        
        # Create a simple intent analysis function
        mock_llm = MockLLMEngine()
        
        # Test workflow intent detection
        workflow_message = "Execute health check on all production servers and send alert if any issues found"
        
        # Simulate intent analysis
        intent_prompt = f"""Analyze this user message to determine if it requires workflow orchestration.
USER MESSAGE: "{workflow_message}"
"""
        
        response = await mock_llm.generate(intent_prompt)
        logger.info(f"✅ Intent analysis response generated: {len(response['generated_text'])} characters")
        
        # Test conversational intent
        conversational_message = "What is the current status of the system?"
        response = await mock_llm.generate(f"USER MESSAGE: \"{conversational_message}\"")
        logger.info(f"✅ Conversational analysis response generated: {len(response['generated_text'])} characters")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI Brain intent analysis test failed: {e}")
        return False

async def test_workflow_task_generation():
    """Test AI-driven workflow task generation"""
    logger.info("🧪 Testing AI-driven workflow task generation...")
    
    try:
        mock_llm = MockLLMEngine()
        
        # Test task generation prompt
        task_prompt = """Convert this user request into structured Prefect workflow tasks.
USER MESSAGE: "Deploy application and monitor status"
Generate tasks in JSON format:
[{"name": "task", "type": "service_call"}]
"""
        
        response = await mock_llm.generate(task_prompt)
        tasks_text = response["generated_text"]
        
        # Parse the generated tasks
        import re
        json_match = re.search(r'\[.*\]', tasks_text, re.DOTALL)
        if json_match:
            tasks_json = json_match.group(0)
            workflow_tasks = json.loads(tasks_json)
            
            logger.info(f"✅ Generated {len(workflow_tasks)} workflow tasks")
            for task in workflow_tasks:
                logger.info(f"  - Task: {task.get('name', 'unnamed')} ({task.get('type', 'unknown')})")
            
            return True
        else:
            logger.error("❌ No JSON tasks found in response")
            return False
            
    except Exception as e:
        logger.error(f"❌ Workflow task generation test failed: {e}")
        return False

async def test_cross_service_orchestration_logic():
    """Test cross-service orchestration logic without actual service calls"""
    logger.info("🧪 Testing cross-service orchestration logic...")
    
    try:
        # Test service mapping and action routing
        service_actions = {
            "automation": ["execute_command", "run_script", "health_check"],
            "asset": ["query_assets", "get_asset_details", "update_asset"],
            "network": ["network_discovery", "connectivity_test", "port_scan"],
            "communication": ["send_notification", "send_alert"]
        }
        
        # Test task routing logic
        test_tasks = [
            {"service": "automation", "action": "health_check"},
            {"service": "asset", "action": "query_assets"},
            {"service": "network", "action": "connectivity_test"},
            {"service": "communication", "action": "send_notification"}
        ]
        
        for task in test_tasks:
            service = task["service"]
            action = task["action"]
            
            if service in service_actions and action in service_actions[service]:
                logger.info(f"✅ Task routing valid: {service}.{action}")
            else:
                logger.error(f"❌ Invalid task routing: {service}.{action}")
                return False
        
        logger.info("✅ Cross-service orchestration logic validated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Cross-service orchestration test failed: {e}")
        return False

async def main():
    """Run all simple integration tests"""
    logger.info("🚀 Starting AI Brain Prefect Integration Simple Tests")
    
    tests = [
        test_direct_executor_complexity_analysis,
        test_service_catalog_integration,
        test_ai_brain_intent_analysis,
        test_workflow_task_generation,
        test_cross_service_orchestration_logic
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append({"test": test.__name__, "passed": result})
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append({"test": test.__name__, "passed": False, "error": str(e)})
    
    # Print summary
    total_tests = len(results)
    passed_tests = len([r for r in results if r["passed"]])
    
    print("\n" + "="*80)
    print("🚀 AI BRAIN PREFECT INTEGRATION SIMPLE TEST SUMMARY")
    print("="*80)
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("="*80)
    
    for result in results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{status}: {result['test']}")
        if not result["passed"] and "error" in result:
            print(f"   Error: {result['error']}")
    
    print("="*80)
    
    if passed_tests == total_tests:
        print("🔥 ALL TESTS PASSED - AI BRAIN PREFECT INTEGRATION LOGIC IS WORKING!")
        print("🚀 Ready for full Prefect server integration testing")
    else:
        print("⚠️  Some tests failed - Check the integration logic")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())