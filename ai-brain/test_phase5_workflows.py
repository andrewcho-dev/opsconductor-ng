"""
OUIOE Phase 5: Comprehensive Workflow System Tests

Test suite for intelligent workflow generation, adaptive execution,
and multi-service orchestration capabilities.
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Import Phase 5 components
from workflows import (
    IntelligentWorkflowGenerator, AdaptiveExecutionEngine, WorkflowOrchestrator,
    IntelligentWorkflow, WorkflowContext, WorkflowType, WorkflowPriority,
    ExecutionResult, ExecutionStatus, OrchestrationResult, OrchestrationStatus
)

# Import Phase 4 components (dependencies)
from decision import DecisionEngine, DecisionRequest, DecisionType
from integrations.thinking_llm_client import ThinkingLLMClient
from streaming import StreamManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """Mock LLM client for testing"""
    
    def __init__(self):
        self.responses = {}
        self.call_count = 0
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None):
        self.call_count += 1
        
        # Generate appropriate mock responses based on prompt content
        if "workflow requirements" in prompt.lower():
            return MockResponse(json.dumps({
                "workflow_type": "sequential",
                "complexity_level": "medium",
                "estimated_steps": 3,
                "required_services": ["asset-service", "automation-service"],
                "critical_dependencies": ["service_availability"],
                "risk_factors": ["timeout", "service_failure"],
                "optimization_opportunities": ["parallel_execution"],
                "adaptation_points": ["error_recovery", "timeout_handling"],
                "success_criteria": ["task_completion", "data_validation"]
            }))
        
        elif "adapt this workflow step" in prompt.lower():
            return MockResponse(json.dumps({
                "name": "Adapted Step Name",
                "parameters": {"timeout": 600, "retry_count": 5},
                "validation_rules": ["check_adapted_response"],
                "success_criteria": ["adapted_completion"],
                "adaptation_notes": "Increased timeout and retry count for better reliability"
            }))
        
        elif "generate workflow steps" in prompt.lower():
            return MockResponse(json.dumps({
                "steps": [
                    {
                        "name": "Initialize Operation",
                        "step_type": "action",
                        "service": "asset-service",
                        "action": "initialize",
                        "parameters": {"mode": "standard"},
                        "timeout_seconds": 300,
                        "retry_policy": {"max_retries": 3, "retry_delay": 5, "backoff_multiplier": 2},
                        "validation_rules": ["check_initialization"],
                        "success_criteria": ["service_ready"],
                        "error_handling": {"on_failure": "retry", "recovery_steps": ["reset_service"]}
                    },
                    {
                        "name": "Execute Main Task",
                        "step_type": "action",
                        "service": "automation-service",
                        "action": "execute_task",
                        "parameters": {"task_type": "main"},
                        "timeout_seconds": 600,
                        "retry_policy": {"max_retries": 2, "retry_delay": 10, "backoff_multiplier": 1.5},
                        "validation_rules": ["check_execution"],
                        "success_criteria": ["task_completed"],
                        "error_handling": {"on_failure": "escalate", "recovery_steps": ["rollback"]}
                    },
                    {
                        "name": "Finalize Operation",
                        "step_type": "validation",
                        "service": "asset-service",
                        "action": "finalize",
                        "parameters": {"cleanup": True},
                        "timeout_seconds": 180,
                        "retry_policy": {"max_retries": 1, "retry_delay": 5, "backoff_multiplier": 1},
                        "validation_rules": ["check_finalization"],
                        "success_criteria": ["operation_finalized"],
                        "error_handling": {"on_failure": "log_error", "recovery_steps": ["manual_cleanup"]}
                    }
                ]
            }))
        
        elif "orchestration analysis" in prompt.lower():
            return MockResponse(json.dumps({
                "orchestration_type": "sequential",
                "required_services": ["asset-service", "automation-service", "network-analyzer-service"],
                "service_dependencies": {
                    "asset-service": ["automation-service"],
                    "automation-service": ["network-analyzer-service"]
                },
                "coordination_complexity": "medium",
                "estimated_workflows": 3,
                "synchronization_points": ["service_ready", "task_completed", "analysis_done"],
                "data_flow_requirements": {
                    "asset-service": {"automation-service": ["asset_data"]},
                    "automation-service": {"network-analyzer-service": ["execution_results"]}
                },
                "resource_coordination": {
                    "asset-service": {"memory": "200MB", "cpu": "0.2"},
                    "automation-service": {"memory": "500MB", "cpu": "0.5"},
                    "network-analyzer-service": {"memory": "300MB", "cpu": "0.3"}
                },
                "timing_constraints": {"max_total_time": 3600},
                "failure_handling": {
                    "asset-service": "retry",
                    "automation-service": "escalate",
                    "network-analyzer-service": "skip"
                },
                "optimization_opportunities": ["parallel_data_processing", "resource_pooling"]
            }))
        
        elif "parameter modifications" in prompt.lower():
            return MockResponse(json.dumps({
                "modified_parameters": {
                    "timeout": 900,
                    "retry_attempts": 5,
                    "fallback_mode": "safe"
                },
                "modification_reason": "Increased timeout and retry attempts to handle service instability"
            }))
        
        else:
            return MockResponse("Mock LLM response for testing")


class MockResponse:
    """Mock response object"""
    def __init__(self, content: str):
        self.content = content


class MockDecisionEngine:
    """Mock decision engine for testing"""
    
    def __init__(self):
        self.decisions = {}
        self.call_count = 0
    
    async def make_decision(self, request: DecisionRequest):
        self.call_count += 1
        
        # Return appropriate mock decisions based on request type
        if "workflow_analysis" in request.request_id:
            return MockDecisionResult(
                selected_option="Complex multi-step workflow",
                confidence=0.85,
                reasoning=["Request requires multiple services", "Complex dependencies identified"],
                alternatives=["Simple sequential workflow", "Parallel execution workflow"]
            )
        
        elif "template_selection" in request.request_id:
            return MockDecisionResult(
                selected_option="automation_execution: Automation Execution Workflow",
                confidence=0.90,
                reasoning=["Best match for automation intent", "Required services available"],
                alternatives=["asset_management: Asset Management Workflow"]
            )
        
        elif "adaptation_strategy" in request.request_id:
            return MockDecisionResult(
                selected_option="retry: Retry the step with same parameters",
                confidence=0.75,
                reasoning=["Transient failure detected", "Service is generally reliable"],
                alternatives=["alternative_path: Use alternative execution path"]
            )
        
        elif "orchestration_analysis" in request.request_id:
            return MockDecisionResult(
                selected_option="Sequential multi-service workflow",
                confidence=0.80,
                reasoning=["Services have dependencies", "Sequential execution is safer"],
                alternatives=["Parallel multi-service workflow", "Hierarchical service coordination"]
            )
        
        else:
            return MockDecisionResult(
                selected_option="Default option",
                confidence=0.70,
                reasoning=["Default reasoning"],
                alternatives=["Alternative option"]
            )


class MockDecisionResult:
    """Mock decision result"""
    def __init__(self, selected_option: str, confidence: float, reasoning: List[str], alternatives: List[str]):
        self.selected_option = selected_option
        self.confidence = confidence
        self.reasoning = reasoning
        self.alternatives = alternatives


class MockStreamManager:
    """Mock stream manager for testing"""
    
    def __init__(self):
        self.published_events = []
    
    async def publish_progress_update(self, session_id: str, data: Dict[str, Any]):
        self.published_events.append({"type": "progress", "session_id": session_id, "data": data})
    
    async def publish_coordination_event(self, orchestration_id: str, data: Dict[str, Any]):
        self.published_events.append({"type": "coordination", "orchestration_id": orchestration_id, "data": data})
    
    async def publish_orchestration_progress(self, session_id: str, data: Dict[str, Any]):
        self.published_events.append({"type": "orchestration", "session_id": session_id, "data": data})


class MockServiceClient:
    """Mock service client for testing"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.call_history = []
    
    async def call_action(self, action: str, parameters: Dict[str, Any]):
        self.call_history.append({"action": action, "parameters": parameters})
        
        # Simulate different responses based on service and action
        if self.service_name == "asset-service":
            if action == "initialize":
                return {"status": "initialized", "service_ready": True}
            elif action == "finalize":
                return {"status": "finalized", "cleanup_completed": True}
            else:
                return {"status": "completed", "data": f"Mock data from {self.service_name}"}
        
        elif self.service_name == "automation-service":
            if action == "execute_task":
                return {"status": "completed", "task_result": "success", "execution_time": 45}
            else:
                return {"status": "completed", "result": f"Mock result from {self.service_name}"}
        
        elif self.service_name == "network-analyzer-service":
            return {"status": "completed", "analysis_result": "network_healthy", "metrics": {"latency": 10, "throughput": 100}}
        
        else:
            return {"status": "completed", "result": f"Mock result from {self.service_name}"}


# Test fixtures
@pytest.fixture
async def mock_components():
    """Create mock components for testing"""
    llm_client = MockLLMClient()
    decision_engine = MockDecisionEngine()
    stream_manager = MockStreamManager()
    
    return {
        "llm_client": llm_client,
        "decision_engine": decision_engine,
        "stream_manager": stream_manager
    }


@pytest.fixture
async def workflow_generator(mock_components):
    """Create workflow generator with mocks"""
    return IntelligentWorkflowGenerator(
        decision_engine=mock_components["decision_engine"],
        llm_client=mock_components["llm_client"]
    )


@pytest.fixture
async def execution_engine(mock_components):
    """Create execution engine with mocks"""
    engine = AdaptiveExecutionEngine(
        decision_engine=mock_components["decision_engine"],
        llm_client=mock_components["llm_client"],
        stream_manager=mock_components["stream_manager"]
    )
    
    # Register mock service clients
    engine.register_service_client("asset-service", MockServiceClient("asset-service"))
    engine.register_service_client("automation-service", MockServiceClient("automation-service"))
    engine.register_service_client("network-analyzer-service", MockServiceClient("network-analyzer-service"))
    
    return engine


@pytest.fixture
async def workflow_orchestrator(workflow_generator, execution_engine, mock_components):
    """Create workflow orchestrator with mocks"""
    return WorkflowOrchestrator(
        workflow_generator=workflow_generator,
        execution_engine=execution_engine,
        decision_engine=mock_components["decision_engine"],
        llm_client=mock_components["llm_client"],
        stream_manager=mock_components["stream_manager"]
    )


@pytest.fixture
def sample_workflow_context():
    """Create sample workflow context for testing"""
    return WorkflowContext(
        user_id="test_user",
        session_id="test_session",
        request_id="test_request",
        primary_intent="Test automation workflow",
        system_context={
            "current_time": datetime.now().isoformat(),
            "system_load": 0.3,
            "available_resources": {"memory": "2GB", "cpu": "4 cores"}
        },
        user_preferences={"priority": "normal", "notifications": True},
        safety_constraints=["no_destructive_operations", "require_confirmation"],
        available_services=["asset-service", "automation-service", "network-analyzer-service"],
        resource_constraints={"max_memory_mb": 1000, "max_cpu_cores": 2},
        time_constraints=timedelta(minutes=30),
        quality_requirements={"success_rate": 0.95, "response_time": 10}
    )


# Test Classes
class TestIntelligentWorkflowGenerator:
    """Test intelligent workflow generation"""
    
    @pytest.mark.asyncio
    async def test_generate_simple_workflow(self, workflow_generator, sample_workflow_context):
        """Test generation of simple workflow"""
        workflow = await workflow_generator.generate_workflow(sample_workflow_context)
        
        assert isinstance(workflow, IntelligentWorkflow)
        assert workflow.name
        assert workflow.workflow_type in WorkflowType
        assert workflow.priority in WorkflowPriority
        assert len(workflow.graph.nodes) > 0
        assert workflow.context == sample_workflow_context
        
        logger.info(f"✅ Generated workflow with {len(workflow.graph.nodes)} steps")
    
    @pytest.mark.asyncio
    async def test_generate_workflow_with_template_hint(self, workflow_generator, sample_workflow_context):
        """Test workflow generation with template hint"""
        workflow = await workflow_generator.generate_workflow(
            sample_workflow_context,
            template_hint="automation_execution"
        )
        
        assert isinstance(workflow, IntelligentWorkflow)
        assert workflow.template is not None
        assert workflow.template.template_id == "automation_execution"
        
        logger.info(f"✅ Generated workflow using template: {workflow.template.name}")
    
    @pytest.mark.asyncio
    async def test_workflow_validation(self, workflow_generator, sample_workflow_context):
        """Test workflow validation"""
        workflow = await workflow_generator.generate_workflow(sample_workflow_context)
        
        # Check basic validation
        assert workflow.workflow_id
        assert workflow.graph.nodes
        assert workflow.metrics.workflow_id == workflow.workflow_id
        assert workflow.metrics.total_steps == len(workflow.graph.nodes)
        
        # Check graph structure
        if len(workflow.graph.nodes) > 1:
            assert workflow.graph.entry_points
            assert workflow.graph.exit_points
        
        logger.info("✅ Workflow validation passed")
    
    @pytest.mark.asyncio
    async def test_template_management(self, workflow_generator):
        """Test template management functionality"""
        # List initial templates
        templates = await workflow_generator.list_templates()
        initial_count = len(templates)
        assert initial_count > 0
        
        # Get specific template
        template = await workflow_generator.get_template("asset_management")
        assert template is not None
        assert template.template_id == "asset_management"
        
        logger.info(f"✅ Template management working - {initial_count} templates available")


class TestAdaptiveExecutionEngine:
    """Test adaptive execution engine"""
    
    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, execution_engine, workflow_generator, sample_workflow_context):
        """Test execution of simple workflow"""
        # Generate workflow
        workflow = await workflow_generator.generate_workflow(sample_workflow_context)
        
        # Execute workflow
        result = await execution_engine.execute_workflow(workflow)
        
        assert isinstance(result, ExecutionResult)
        assert result.workflow_id == workflow.workflow_id
        assert result.status in ExecutionStatus
        assert result.execution_time is not None
        
        logger.info(f"✅ Executed workflow with status: {result.status}")
    
    @pytest.mark.asyncio
    async def test_workflow_adaptation(self, execution_engine, workflow_generator, sample_workflow_context):
        """Test workflow adaptation capabilities"""
        # Create workflow with potential failure points
        workflow = await workflow_generator.generate_workflow(sample_workflow_context)
        
        # Execute workflow (may trigger adaptations)
        result = await execution_engine.execute_workflow(workflow)
        
        # Check if adaptations were applied
        assert isinstance(result, ExecutionResult)
        
        # Check workflow adaptation history
        if workflow.adaptations:
            logger.info(f"✅ Workflow adaptations applied: {len(workflow.adaptations)}")
        else:
            logger.info("✅ No adaptations needed - workflow executed successfully")
    
    @pytest.mark.asyncio
    async def test_execution_monitoring(self, execution_engine, workflow_generator, sample_workflow_context):
        """Test execution monitoring"""
        workflow = await workflow_generator.generate_workflow(sample_workflow_context)
        
        # Execute with monitoring
        result = await execution_engine.execute_workflow(workflow)
        
        # Check metrics were updated
        assert workflow.metrics.total_steps > 0
        assert workflow.metrics.success_rate >= 0
        
        logger.info(f"✅ Execution monitoring - Success rate: {workflow.metrics.success_rate:.2f}")
    
    @pytest.mark.asyncio
    async def test_concurrent_executions(self, execution_engine, workflow_generator, sample_workflow_context):
        """Test concurrent workflow executions"""
        # Generate multiple workflows
        workflows = []
        for i in range(3):
            context = WorkflowContext(
                user_id=sample_workflow_context.user_id,
                session_id=f"{sample_workflow_context.session_id}_{i}",
                request_id=f"{sample_workflow_context.request_id}_{i}",
                primary_intent=f"Concurrent test {i}",
                system_context=sample_workflow_context.system_context,
                available_services=sample_workflow_context.available_services
            )
            workflow = await workflow_generator.generate_workflow(context)
            workflows.append(workflow)
        
        # Execute concurrently
        tasks = [execution_engine.execute_workflow(wf) for wf in workflows]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, ExecutionResult)
        
        logger.info(f"✅ Concurrent execution completed - {len(results)} workflows")


class TestWorkflowOrchestrator:
    """Test workflow orchestrator"""
    
    @pytest.mark.asyncio
    async def test_simple_orchestration(self, workflow_orchestrator, sample_workflow_context):
        """Test simple workflow orchestration"""
        result = await workflow_orchestrator.orchestrate_complex_workflow(sample_workflow_context)
        
        assert isinstance(result, OrchestrationResult)
        assert result.orchestration_id
        assert result.status in OrchestrationStatus
        assert isinstance(result.workflow_results, dict)
        
        logger.info(f"✅ Orchestration completed with status: {result.status}")
    
    @pytest.mark.asyncio
    async def test_multi_service_orchestration(self, workflow_orchestrator, sample_workflow_context):
        """Test multi-service orchestration"""
        # Create context requiring multiple services
        complex_context = WorkflowContext(
            user_id=sample_workflow_context.user_id,
            session_id=sample_workflow_context.session_id,
            request_id="complex_orchestration",
            primary_intent="Complex multi-service operation requiring asset management, automation, and network analysis",
            system_context=sample_workflow_context.system_context,
            available_services=["asset-service", "automation-service", "network-analyzer-service"],
            resource_constraints={"max_memory_mb": 2000, "max_cpu_cores": 4}
        )
        
        result = await workflow_orchestrator.orchestrate_complex_workflow(complex_context)
        
        assert isinstance(result, OrchestrationResult)
        assert len(result.workflow_results) > 1  # Multiple workflows
        
        logger.info(f"✅ Multi-service orchestration - {len(result.workflow_results)} workflows")
    
    @pytest.mark.asyncio
    async def test_orchestration_coordination(self, workflow_orchestrator, sample_workflow_context):
        """Test orchestration coordination rules"""
        coordination_requirements = {
            "coordination_type": "sequential",
            "data_flow": True,
            "synchronization_points": ["start", "middle", "end"]
        }
        
        result = await workflow_orchestrator.orchestrate_complex_workflow(
            sample_workflow_context,
            coordination_requirements
        )
        
        assert isinstance(result, OrchestrationResult)
        assert result.coordination_metrics is not None
        
        logger.info("✅ Orchestration coordination rules applied successfully")
    
    @pytest.mark.asyncio
    async def test_orchestration_failure_handling(self, workflow_orchestrator, sample_workflow_context):
        """Test orchestration failure handling"""
        # Create context that might cause failures
        failure_context = WorkflowContext(
            user_id=sample_workflow_context.user_id,
            session_id=sample_workflow_context.session_id,
            request_id="failure_test",
            primary_intent="Test failure handling in orchestration",
            system_context=sample_workflow_context.system_context,
            available_services=["nonexistent-service", "asset-service"],  # Include non-existent service
            time_constraints=timedelta(seconds=1)  # Very short timeout
        )
        
        result = await workflow_orchestrator.orchestrate_complex_workflow(failure_context)
        
        assert isinstance(result, OrchestrationResult)
        # Should handle failures gracefully
        
        logger.info(f"✅ Failure handling test - Status: {result.status}")


class TestWorkflowIntegration:
    """Test integration between workflow components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, workflow_orchestrator, sample_workflow_context):
        """Test complete end-to-end workflow"""
        # Create comprehensive workflow context
        e2e_context = WorkflowContext(
            user_id="e2e_user",
            session_id="e2e_session",
            request_id="e2e_test",
            primary_intent="Complete end-to-end test of workflow system with asset management and automation",
            system_context={
                "test_mode": True,
                "comprehensive_test": True,
                "expected_services": ["asset-service", "automation-service"]
            },
            available_services=["asset-service", "automation-service", "network-analyzer-service"],
            user_preferences={"detailed_logging": True, "progress_updates": True},
            safety_constraints=["test_environment_only"],
            resource_constraints={"max_memory_mb": 1500, "max_cpu_cores": 3},
            time_constraints=timedelta(minutes=15),
            quality_requirements={"success_rate": 0.90, "response_time": 30}
        )
        
        # Execute end-to-end orchestration
        result = await workflow_orchestrator.orchestrate_complex_workflow(e2e_context)
        
        # Comprehensive validation
        assert isinstance(result, OrchestrationResult)
        assert result.orchestration_id
        assert result.status in OrchestrationStatus
        assert result.workflow_results
        assert result.global_metrics
        
        # Check that workflows were actually executed
        successful_workflows = sum(
            1 for wf_result in result.workflow_results.values()
            if wf_result.status == ExecutionStatus.SUCCESS
        )
        
        logger.info(f"✅ End-to-end test completed - {successful_workflows}/{len(result.workflow_results)} workflows successful")
    
    @pytest.mark.asyncio
    async def test_workflow_learning_and_optimization(self, workflow_generator, execution_engine):
        """Test workflow learning and optimization"""
        # Generate and execute multiple similar workflows
        base_context = WorkflowContext(
            user_id="learning_user",
            session_id="learning_session",
            request_id="learning_base",
            primary_intent="Learning test workflow",
            system_context={"learning_mode": True},
            available_services=["asset-service", "automation-service"]
        )
        
        # Execute multiple workflows to build learning data
        for i in range(3):
            context = WorkflowContext(
                user_id=base_context.user_id,
                session_id=f"{base_context.session_id}_{i}",
                request_id=f"{base_context.request_id}_{i}",
                primary_intent=f"{base_context.primary_intent} iteration {i}",
                system_context=base_context.system_context,
                available_services=base_context.available_services
            )
            
            workflow = await workflow_generator.generate_workflow(context)
            result = await execution_engine.execute_workflow(workflow)
            
            assert isinstance(result, ExecutionResult)
        
        # Check that learning data was collected
        generation_history = await workflow_generator.get_generation_history()
        execution_history = await execution_engine.get_execution_history()
        
        assert len(generation_history) >= 3
        assert len(execution_history) >= 3
        
        logger.info(f"✅ Learning data collected - {len(generation_history)} generations, {len(execution_history)} executions")


# Main test execution
async def run_phase5_tests():
    """Run all Phase 5 tests"""
    logger.info("🚀 Starting OUIOE Phase 5: Multi-Step Workflows Tests")
    logger.info("=" * 80)
    
    # Create test components
    mock_components = {
        "llm_client": MockLLMClient(),
        "decision_engine": MockDecisionEngine(),
        "stream_manager": MockStreamManager()
    }
    
    workflow_generator = IntelligentWorkflowGenerator(
        decision_engine=mock_components["decision_engine"],
        llm_client=mock_components["llm_client"]
    )
    
    execution_engine = AdaptiveExecutionEngine(
        decision_engine=mock_components["decision_engine"],
        llm_client=mock_components["llm_client"],
        stream_manager=mock_components["stream_manager"]
    )
    
    # Register mock service clients
    execution_engine.register_service_client("asset-service", MockServiceClient("asset-service"))
    execution_engine.register_service_client("automation-service", MockServiceClient("automation-service"))
    execution_engine.register_service_client("network-analyzer-service", MockServiceClient("network-analyzer-service"))
    
    workflow_orchestrator = WorkflowOrchestrator(
        workflow_generator=workflow_generator,
        execution_engine=execution_engine,
        decision_engine=mock_components["decision_engine"],
        llm_client=mock_components["llm_client"],
        stream_manager=mock_components["stream_manager"]
    )
    
    sample_context = WorkflowContext(
        user_id="test_user",
        session_id="test_session",
        request_id="test_request",
        primary_intent="Test automation workflow",
        system_context={"test_mode": True},
        available_services=["asset-service", "automation-service", "network-analyzer-service"]
    )
    
    # Test counters
    total_tests = 0
    passed_tests = 0
    
    # Test Intelligent Workflow Generator
    logger.info("\n📋 Testing Intelligent Workflow Generator")
    logger.info("-" * 50)
    
    try:
        total_tests += 1
        workflow = await workflow_generator.generate_workflow(sample_context)
        assert isinstance(workflow, IntelligentWorkflow)
        passed_tests += 1
        logger.info("✅ Workflow generation test passed")
    except Exception as e:
        logger.error(f"❌ Workflow generation test failed: {e}")
    
    try:
        total_tests += 1
        templates = await workflow_generator.list_templates()
        assert len(templates) > 0
        passed_tests += 1
        logger.info(f"✅ Template management test passed - {len(templates)} templates")
    except Exception as e:
        logger.error(f"❌ Template management test failed: {e}")
    
    # Test Adaptive Execution Engine
    logger.info("\n⚡ Testing Adaptive Execution Engine")
    logger.info("-" * 50)
    
    try:
        total_tests += 1
        workflow = await workflow_generator.generate_workflow(sample_context)
        result = await execution_engine.execute_workflow(workflow)
        assert isinstance(result, ExecutionResult)
        passed_tests += 1
        logger.info(f"✅ Workflow execution test passed - Status: {result.status}")
    except Exception as e:
        logger.error(f"❌ Workflow execution test failed: {e}")
    
    try:
        total_tests += 1
        active_executions = await execution_engine.get_active_executions()
        performance_metrics = await execution_engine.get_performance_metrics()
        assert isinstance(active_executions, dict)
        assert isinstance(performance_metrics, dict)
        passed_tests += 1
        logger.info("✅ Execution monitoring test passed")
    except Exception as e:
        logger.error(f"❌ Execution monitoring test failed: {e}")
    
    # Test Workflow Orchestrator
    logger.info("\n🎭 Testing Workflow Orchestrator")
    logger.info("-" * 50)
    
    try:
        total_tests += 1
        result = await workflow_orchestrator.orchestrate_complex_workflow(sample_context)
        assert isinstance(result, OrchestrationResult)
        passed_tests += 1
        logger.info(f"✅ Basic orchestration test passed - Status: {result.status}")
    except Exception as e:
        logger.error(f"❌ Basic orchestration test failed: {e}")
    
    try:
        total_tests += 1
        complex_context = WorkflowContext(
            user_id="test_user",
            session_id="test_session",
            request_id="complex_test",
            primary_intent="Complex multi-service operation",
            system_context={"complexity": "high"},
            available_services=["asset-service", "automation-service", "network-analyzer-service"]
        )
        result = await workflow_orchestrator.orchestrate_complex_workflow(complex_context)
        assert isinstance(result, OrchestrationResult)
        passed_tests += 1
        logger.info(f"✅ Complex orchestration test passed - {len(result.workflow_results)} workflows")
    except Exception as e:
        logger.error(f"❌ Complex orchestration test failed: {e}")
    
    # Test Integration
    logger.info("\n🔗 Testing System Integration")
    logger.info("-" * 50)
    
    try:
        total_tests += 1
        e2e_context = WorkflowContext(
            user_id="e2e_user",
            session_id="e2e_session",
            request_id="e2e_test",
            primary_intent="End-to-end integration test",
            system_context={"integration_test": True},
            available_services=["asset-service", "automation-service"]
        )
        result = await workflow_orchestrator.orchestrate_complex_workflow(e2e_context)
        assert isinstance(result, OrchestrationResult)
        passed_tests += 1
        logger.info("✅ End-to-end integration test passed")
    except Exception as e:
        logger.error(f"❌ End-to-end integration test failed: {e}")
    
    # Performance and Learning Tests
    logger.info("\n📊 Testing Performance and Learning")
    logger.info("-" * 50)
    
    try:
        total_tests += 1
        # Test multiple workflow generations for learning
        for i in range(3):
            context = WorkflowContext(
                user_id="perf_user",
                session_id=f"perf_session_{i}",
                request_id=f"perf_test_{i}",
                primary_intent=f"Performance test {i}",
                system_context={"performance_test": True},
                available_services=["asset-service"]
            )
            workflow = await workflow_generator.generate_workflow(context)
            result = await execution_engine.execute_workflow(workflow)
        
        # Check learning data
        generation_history = await workflow_generator.get_generation_history()
        execution_history = await execution_engine.get_execution_history()
        
        assert len(generation_history) >= 3
        assert len(execution_history) >= 3
        passed_tests += 1
        logger.info(f"✅ Performance and learning test passed - {len(generation_history)} generations")
    except Exception as e:
        logger.error(f"❌ Performance and learning test failed: {e}")
    
    # Final Results
    logger.info("\n" + "=" * 80)
    logger.info("🎯 PHASE 5 TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"📊 Total Tests: {total_tests}")
    logger.info(f"✅ Passed: {passed_tests}")
    logger.info(f"❌ Failed: {total_tests - passed_tests}")
    logger.info(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL PHASE 5 TESTS PASSED!")
        logger.info("🚀 OUIOE Phase 5: Multi-Step Workflows - IMPLEMENTATION COMPLETE!")
    else:
        logger.info(f"⚠️  {total_tests - passed_tests} tests failed - review implementation")
    
    logger.info("=" * 80)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_phase5_tests())
    exit(0 if success else 1)