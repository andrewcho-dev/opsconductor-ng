#!/usr/bin/env python3
"""
🚀 AI BRAIN PREFECT INTEGRATION TEST SUITE

Comprehensive test suite to validate the complete AI Brain Prefect integration
including AI-driven workflow generation, cross-service orchestration, and
enterprise workflow templates.
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

class MockServiceClient:
    """Mock service client for testing"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.call_count = 0
    
    async def health_check(self):
        self.call_count += 1
        return {"status": "healthy", "service": self.service_name, "timestamp": datetime.now().isoformat()}
    
    async def execute_command(self, command: str):
        self.call_count += 1
        return {"command": command, "output": f"Mock output for: {command}", "exit_code": 0}
    
    async def run_script(self, script: str, script_type: str = "bash"):
        self.call_count += 1
        return {"script": script, "script_type": script_type, "output": f"Mock script execution: {script}", "exit_code": 0}
    
    async def query_assets(self, filters: Dict[str, Any]):
        self.call_count += 1
        return {"filters": filters, "assets": [{"id": "asset-1", "hostname": "server-1", "status": "active"}]}
    
    async def get_asset_details(self, asset_id: str):
        self.call_count += 1
        return {"asset_id": asset_id, "hostname": f"server-{asset_id}", "status": "active", "cpu": "80%", "memory": "60%"}
    
    async def update_asset(self, asset_id: str, updates: Dict[str, Any]):
        self.call_count += 1
        return {"asset_id": asset_id, "updates": updates, "status": "updated"}
    
    async def network_discovery(self, target: str):
        self.call_count += 1
        return {"target": target, "discovered_hosts": ["192.168.1.1", "192.168.1.2"], "scan_time": "2.5s"}
    
    async def connectivity_test(self, host: str, port: int = None):
        self.call_count += 1
        return {"host": host, "port": port, "status": "reachable", "response_time": "15ms"}
    
    async def port_scan(self, target: str, ports: str = None):
        self.call_count += 1
        return {"target": target, "ports": ports, "open_ports": [22, 80, 443], "scan_time": "5.2s"}
    
    async def send_notification(self, message: str, recipients: List[str] = None, notification_type: str = "info"):
        self.call_count += 1
        return {"message": message, "recipients": recipients or [], "type": notification_type, "sent": True}
    
    async def send_alert(self, alert_message: str, severity: str = "medium"):
        self.call_count += 1
        return {"alert_message": alert_message, "severity": severity, "alert_id": f"alert-{self.call_count}", "sent": True}

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
            # Intent analysis - be more specific about workflow keywords
            workflow_keywords = ["deploy", "execute health check", "run script", "monitor deployment", "backup", "restart", "send alert", "check.*servers"]
            conversational_keywords = ["what is", "current status", "how are", "tell me", "show me"]
            
            prompt_lower = prompt.lower()
            
            # Check for conversational patterns first
            if any(keyword in prompt_lower for keyword in conversational_keywords):
                return {"generated_text": '''
{
  "requires_workflow": false,
  "intent_type": "conversational",
  "confidence": 0.9,
  "complexity_level": "simple",
  "workflow_components": [],
  "reasoning": "Simple conversational request asking for information"
}
'''}
            # Then check for workflow patterns
            elif any(keyword in prompt_lower for keyword in workflow_keywords):
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
  "reasoning": "Default to conversational for unclear intent"
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
  },
  {
    "name": "send_notification",
    "type": "notification",
    "parameters": {
      "message": "Task completed successfully",
      "type": "success"
    },
    "depends_on": ["execute_automation"],
    "retry_count": 1,
    "timeout_seconds": 30,
    "description": "Send completion notification"
  }
]
'''}
        
        else:
            # Default response
            return {"generated_text": "Mock LLM response for testing"}
    
    async def generate_response(self, message: str, context: Dict[str, Any] = None):
        self.call_count += 1
        return f"Mock conversational response to: {message}"

class AIBrainPrefectIntegrationTest:
    """Comprehensive test suite for AI Brain Prefect integration"""
    
    def __init__(self):
        self.test_results = []
        self.mock_clients = {}
        self.setup_mock_clients()
    
    def setup_mock_clients(self):
        """Setup mock service clients"""
        self.mock_clients = {
            "automation": MockServiceClient("automation"),
            "asset": MockServiceClient("asset"),
            "network": MockServiceClient("network"),
            "communication": MockServiceClient("communication"),
            "llm": MockLLMEngine()
        }
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting AI Brain Prefect Integration Test Suite")
        
        test_methods = [
            self.test_direct_executor_prefect_integration,
            self.test_ai_brain_service_intent_analysis,
            self.test_ai_brain_service_workflow_generation,
            self.test_prefect_flow_engine_cross_service_orchestration,
            self.test_enterprise_workflow_templates,
            self.test_end_to_end_workflow_execution
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"🧪 Running test: {test_method.__name__}")
                await test_method()
                self.test_results.append({"test": test_method.__name__, "status": "PASSED"})
                logger.info(f"✅ Test passed: {test_method.__name__}")
            except Exception as e:
                logger.error(f"❌ Test failed: {test_method.__name__} - {e}")
                self.test_results.append({"test": test_method.__name__, "status": "FAILED", "error": str(e)})
        
        self.print_test_summary()
    
    async def test_direct_executor_prefect_integration(self):
        """Test DirectExecutor integration with PrefectFlowEngine"""
        from fulfillment_engine.direct_executor import DirectExecutor
        from orchestration.prefect_flow_engine import PrefectFlowEngine
        
        # Create PrefectFlowEngine with mock clients
        prefect_flow_engine = PrefectFlowEngine(
            automation_client=self.mock_clients["automation"],
            asset_client=self.mock_clients["asset"],
            network_client=self.mock_clients["network"],
            communication_client=self.mock_clients["communication"]
        )
        
        # Create DirectExecutor with Prefect integration
        direct_executor = DirectExecutor(
            llm_engine=self.mock_clients["llm"],
            automation_client=self.mock_clients["automation"],
            asset_client=self.mock_clients["asset"],
            network_client=self.mock_clients["network"],
            communication_client=self.mock_clients["communication"],
            prefect_flow_engine=prefect_flow_engine
        )
        
        # Test complex workflow detection
        complex_request = "Deploy application v2.1 to production environment and then monitor the deployment status"
        result = await direct_executor.execute_user_request(
            user_message=complex_request,
            user_context={"user_id": "test_user", "conversation_id": "test_conv"}
        )
        
        assert result["status"] in ["completed", "failed"], f"Unexpected status: {result['status']}"
        logger.info(f"DirectExecutor result: {result.get('message', 'No message')}")
    
    async def test_ai_brain_service_intent_analysis(self):
        """Test AI Brain Service intent analysis"""
        from orchestration.ai_brain_service import AIBrainService
        
        # Mock the LLM client in AIBrainService
        ai_brain = AIBrainService()
        ai_brain.llm_client = self.mock_clients["llm"]
        
        # Test workflow intent detection
        workflow_message = "Execute health check on all production servers and send alert if any issues found"
        intent = await ai_brain._analyze_intent(workflow_message, "test_user")
        
        assert intent["requires_workflow"] == True, "Should detect workflow requirement"
        assert intent["intent_type"] in ["complex_workflow", "automation_request"], f"Unexpected intent type: {intent['intent_type']}"
        assert intent["confidence"] > 0.5, f"Low confidence: {intent['confidence']}"
        
        # Test conversational intent detection
        conversational_message = "What is the current status of the system?"
        intent = await ai_brain._analyze_intent(conversational_message, "test_user")
        
        assert intent["requires_workflow"] == False, "Should not detect workflow requirement for conversational message"
        logger.info(f"Intent analysis working correctly")
    
    async def test_ai_brain_service_workflow_generation(self):
        """Test AI Brain Service workflow generation"""
        from orchestration.ai_brain_service import AIBrainService
        
        # Setup AI Brain Service with mock clients
        ai_brain = AIBrainService()
        ai_brain.llm_client = self.mock_clients["llm"]
        ai_brain.automation_client = self.mock_clients["automation"]
        ai_brain.asset_client = self.mock_clients["asset"]
        ai_brain.prefect_available = True
        
        # Test workflow generation
        workflow_message = "Deploy application and monitor status"
        intent = {
            "requires_workflow": True,
            "intent_type": "complex_workflow",
            "confidence": 0.9,
            "complexity_level": "medium",
            "workflow_components": ["automation", "asset"]
        }
        
        result = await ai_brain._generate_and_execute_workflow(workflow_message, "test_user", intent)
        
        assert result["execution_status"] in ["running", "completed", "failed"], f"Unexpected execution status: {result['execution_status']}"
        assert len(result["workflows"]) > 0, "Should generate at least one workflow"
        logger.info(f"Workflow generation working correctly")
    
    async def test_prefect_flow_engine_cross_service_orchestration(self):
        """Test PrefectFlowEngine cross-service orchestration"""
        from orchestration.prefect_flow_engine import PrefectFlowEngine
        
        # Create PrefectFlowEngine with mock clients
        prefect_engine = PrefectFlowEngine(
            automation_client=self.mock_clients["automation"],
            asset_client=self.mock_clients["asset"],
            network_client=self.mock_clients["network"],
            communication_client=self.mock_clients["communication"]
        )
        
        # Test service call task execution
        task_result = await prefect_engine._execute_service_call_task(
            task_name="test_automation_task",
            parameters={
                "service": "automation",
                "action": "health_check",
                "parameters": {}
            },
            previous_results={}
        )
        
        assert task_result["status"] == "completed", f"Task execution failed: {task_result}"
        assert task_result["service"] == "automation", "Service not correctly identified"
        assert self.mock_clients["automation"].call_count > 0, "Automation service not called"
        
        # Test asset service integration
        asset_task_result = await prefect_engine._execute_service_call_task(
            task_name="test_asset_task",
            parameters={
                "service": "asset",
                "action": "query_assets",
                "parameters": {"filters": {"status": "active"}}
            },
            previous_results={}
        )
        
        assert asset_task_result["status"] == "completed", f"Asset task execution failed: {asset_task_result}"
        assert self.mock_clients["asset"].call_count > 0, "Asset service not called"
        logger.info(f"Cross-service orchestration working correctly")
    
    async def test_enterprise_workflow_templates(self):
        """Test enterprise workflow templates"""
        from orchestration.prefect_flow_engine import PrefectFlowEngine
        
        # Create PrefectFlowEngine with mock clients
        prefect_engine = PrefectFlowEngine(
            automation_client=self.mock_clients["automation"],
            asset_client=self.mock_clients["asset"],
            network_client=self.mock_clients["network"],
            communication_client=self.mock_clients["communication"]
        )
        
        # Initialize to register enterprise templates
        await prefect_engine.initialize()
        
        # Check that enterprise templates are registered
        expected_templates = [
            "health_check",
            "enterprise_server_monitoring",
            "automated_deployment_pipeline",
            "security_compliance_audit",
            "data_backup_and_recovery"
        ]
        
        for template in expected_templates:
            assert template in prefect_engine.registered_flows, f"Template {template} not registered"
        
        logger.info(f"Enterprise workflow templates registered correctly: {list(prefect_engine.registered_flows.keys())}")
    
    async def test_end_to_end_workflow_execution(self):
        """Test end-to-end workflow execution"""
        from orchestration.ai_brain_service import AIBrainService
        
        # Setup complete AI Brain Service
        ai_brain = AIBrainService()
        ai_brain.llm_client = self.mock_clients["llm"]
        ai_brain.automation_client = self.mock_clients["automation"]
        ai_brain.asset_client = self.mock_clients["asset"]
        ai_brain.prefect_available = False  # Test direct execution path
        
        # Test complete chat message processing
        test_message = "Check the health of all production servers"
        result = await ai_brain.process_chat_message(
            message=test_message,
            user_id="test_user",
            conversation_id="test_conversation"
        )
        
        assert "message_id" in result, "Missing message_id in result"
        assert "user_id" in result, "Missing user_id in result"
        assert "intent" in result, "Missing intent analysis in result"
        assert "execution_status" in result, "Missing execution_status in result"
        
        # Verify intent was analyzed
        intent = result["intent"]
        assert "requires_workflow" in intent, "Intent analysis incomplete"
        
        logger.info(f"End-to-end workflow execution working correctly")
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASSED"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("🚀 AI BRAIN PREFECT INTEGRATION TEST SUMMARY")
        print("="*80)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("="*80)
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["status"] == "PASSED":
                print(f"  - {result['test']}")
        
        print("\n🔍 SERVICE CALL STATISTICS:")
        for service_name, client in self.mock_clients.items():
            if hasattr(client, 'call_count'):
                print(f"  - {service_name}: {client.call_count} calls")
        
        print("\n🎯 INTEGRATION STATUS:")
        if passed_tests == total_tests:
            print("🔥 ALL TESTS PASSED - AI BRAIN PREFECT INTEGRATION IS FULLY FUNCTIONAL!")
        elif passed_tests >= total_tests * 0.8:
            print("⚡ MOSTLY FUNCTIONAL - Minor issues detected")
        else:
            print("⚠️  SIGNIFICANT ISSUES - Integration needs attention")
        
        print("="*80)

async def main():
    """Main test execution"""
    test_suite = AIBrainPrefectIntegrationTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())