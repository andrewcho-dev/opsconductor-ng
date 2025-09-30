"""
Phase 4 Test Suite - Stage D Answerer
Comprehensive testing for response generation and user communication

This test suite validates the Stage D Answerer implementation including:
- Response generation from execution plans
- Approval workflow handling
- Context-aware answering
- User-friendly message formatting
- Clarification request generation
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

# Import Stage D components
from pipeline.stages.stage_d.answerer import StageDAnswerer
from pipeline.stages.stage_d.response_formatter import ResponseFormatter
from pipeline.stages.stage_d.approval_handler import ApprovalHandler
from pipeline.stages.stage_d.context_analyzer import ContextAnalyzer

# Import schemas
from pipeline.schemas.decision_v1 import (
    DecisionV1, IntentV1, EntityV1, ConfidenceLevel, RiskLevel, DecisionType
)
from pipeline.schemas.selection_v1 import (
    SelectionV1, SelectedTool, ToolCapability, RiskLevel as SelectionRiskLevel
)
from pipeline.schemas.plan_v1 import (
    PlanV1, ExecutionPlan, ExecutionStep, SafetyCheck, ExecutionMetadata
)
from pipeline.schemas.response_v1 import (
    ResponseV1, ResponseType, ConfidenceLevel as ResponseConfidence,
    ExecutionSummary, ApprovalPoint, ActionSuggestion,
    ClarificationResponse, ClarificationRequest
)

# Mock LLM client for testing
class MockLLMClient:
    """Mock LLM client for testing"""
    
    def __init__(self):
        self.connected = True
    
    async def generate_response(self, prompt: str) -> str:
        """Generate mock response based on prompt content"""
        if "information" in prompt.lower():
            return "I'll gather the requested system information using the planned tools. This will provide comprehensive insights into your system status."
        elif "plan summary" in prompt.lower():
            return "I've created a comprehensive execution plan that will safely perform the requested operation with built-in safety measures."
        elif "approval" in prompt.lower():
            return "This operation requires approval due to its high-risk nature. Please review the plan and provide necessary approvals before execution."
        elif "execution" in prompt.lower() or "ready" in prompt.lower():
            return "The execution plan is ready to run. All safety checks are in place and the operation can proceed immediately."
        elif "clarification" in prompt.lower():
            return "I need some additional information to create the best plan for your request. Please provide the missing details."
        else:
            return "I've processed your request and created an appropriate response."
    
    async def health_check(self) -> bool:
        return True

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    return MockLLMClient()

@pytest.fixture
def sample_decision():
    """Sample decision from Stage A"""
    return DecisionV1(
        decision_id="dec_test_001",
        decision_type=DecisionType.ACTION,
        timestamp="2024-01-01T12:00:00Z",
        intent=IntentV1(
            category="service_management",
            action="restart_service",
            confidence=0.85
        ),
        entities=[
            EntityV1(type="hostname", value="web-server-01", confidence=0.9),
            EntityV1(type="service", value="nginx", confidence=0.95)
        ],
        overall_confidence=0.85,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.MEDIUM,
        original_request="Restart nginx service on web-server-01",
        context={},
        requires_approval=True,
        next_stage="stage_b"
    )

@pytest.fixture
def sample_selection():
    """Sample selection from Stage B"""
    from pipeline.schemas.selection_v1 import ExecutionPolicy
    
    return SelectionV1(
        selection_id="sel_test_001",
        decision_id="dec_test_001",
        timestamp="2024-01-01T12:00:01Z",
        selected_tools=[
            SelectedTool(
                tool_name="systemctl",
                justification="Required for service management operations",
                inputs_needed=["service_name", "action"],
                execution_order=1,
                depends_on=[]
            )
        ],
        total_tools=1,
        policy=ExecutionPolicy(
            requires_approval=True,
            production_environment=True,
            risk_level=SelectionRiskLevel.MEDIUM,
            max_execution_time=300,
            parallel_execution=False,
            rollback_required=False
        ),
        additional_inputs_needed=[],
        environment_requirements={},
        selection_confidence=0.85,
        next_stage="stage_c",
        ready_for_execution=False
    )

@pytest.fixture
def sample_plan():
    """Sample plan from Stage C"""
    return PlanV1(
        plan=ExecutionPlan(
            steps=[
                ExecutionStep(
                    id="step_001_check_service",
                    description="Check current service status",
                    tool="systemctl",
                    inputs={"service": "nginx", "action": "status"},
                    preconditions=["service_exists"],
                    success_criteria=["status_retrieved"],
                    failure_handling="Log error and continue",
                    estimated_duration=10,
                    depends_on=[],
                    execution_order=1
                ),
                ExecutionStep(
                    id="step_002_restart_service",
                    description="Restart nginx service",
                    tool="systemctl",
                    inputs={"service": "nginx", "action": "restart"},
                    preconditions=["service_exists", "approval_obtained"],
                    success_criteria=["service_restarted", "service_healthy"],
                    failure_handling="Attempt rollback to previous state",
                    estimated_duration=30,
                    depends_on=["step_001_check_service"],
                    execution_order=2
                )
            ],
            safety_checks=[
                SafetyCheck(
                    id="safety_001",
                    check="Verify service is running before restart",
                    stage="before",
                    failure_action="abort"
                ),
                SafetyCheck(
                    id="safety_002", 
                    check="Monitor service health after restart",
                    stage="after",
                    failure_action="warn"
                )
            ],
            rollback_plan=[]  # Rollback removed
        ),
        execution_metadata=ExecutionMetadata(
            total_estimated_time=40,
            risk_factors=["production_environment", "service_restart"],
            approval_points=["step_002_restart_service"],
            checkpoints=["step_001_check_service"],
            observability_config={
                "metrics": ["service_status", "response_time"],
                "alerts": ["service_down", "high_response_time"],
                "logs": ["service_logs", "system_logs"]
            }
        ),
        timestamp="2024-01-01T12:00:02Z",
        processing_time_ms=150
    )

# ============================================================================
# RESPONSE V1 SCHEMA TESTS
# ============================================================================

class TestResponseV1Schema:
    """Test Response V1 schema validation and structure"""
    
    def test_response_v1_schema_structure(self):
        """Test Response V1 schema basic structure"""
        response = ResponseV1(
            response_type=ResponseType.PLAN_SUMMARY,
            message="Test response message",
            confidence=ResponseConfidence.HIGH,
            response_id="test_001",
            processing_time_ms=100
        )
        
        assert response.response_type == ResponseType.PLAN_SUMMARY
        assert response.message == "Test response message"
        assert response.confidence == ResponseConfidence.HIGH
        assert response.approval_required == False
        assert response.approval_points == []
        assert response.suggested_actions == []
        assert response.warnings == []
        assert response.limitations == []
        assert response.response_id == "test_001"
        assert response.processing_time_ms == 100
    
    def test_execution_summary_validation(self):
        """Test ExecutionSummary schema validation"""
        summary = ExecutionSummary(
            total_steps=5,
            estimated_duration=180,
            risk_level="medium",
            tools_involved=["systemctl", "journalctl"],
            safety_checks=12,
            approval_points=2
        )
        
        assert summary.total_steps == 5
        assert summary.estimated_duration == 180
        assert summary.risk_level == "medium"
        assert summary.tools_involved == ["systemctl", "journalctl"]
        assert summary.safety_checks == 12
        assert summary.approval_points == 2
    
    def test_approval_point_validation(self):
        """Test ApprovalPoint schema validation"""
        approval = ApprovalPoint(
            step_id="step_003_restart_service",
            reason="Production service restart requires approval",
            risk_level="high",
            approver_role="operations_manager"
        )
        
        assert approval.step_id == "step_003_restart_service"
        assert approval.reason == "Production service restart requires approval"
        assert approval.risk_level == "high"
        assert approval.approver_role == "operations_manager"
    
    def test_clarification_response_validation(self):
        """Test ClarificationResponse schema validation"""
        clarification = ClarificationResponse(
            message="I need more information",
            clarifications_needed=[
                ClarificationRequest(
                    question="Which environment?",
                    options=["dev", "prod"],
                    required=True,
                    context="Environment affects safety procedures"
                )
            ],
            response_id="clarify_001",
            processing_time_ms=150
        )
        
        assert clarification.response_type == ResponseType.CLARIFICATION
        assert clarification.message == "I need more information"
        assert len(clarification.clarifications_needed) == 1
        assert clarification.clarifications_needed[0].question == "Which environment?"

# ============================================================================
# RESPONSE FORMATTER TESTS
# ============================================================================

class TestResponseFormatter:
    """Test response formatting functionality"""
    
    @pytest.mark.asyncio
    async def test_format_information_response(self, mock_llm_client, sample_decision, sample_plan):
        """Test information response formatting"""
        formatter = ResponseFormatter(mock_llm_client)
        
        analysis = {
            "sources": ["system_monitoring"],
            "insights": ["System status will be checked"],
            "technical_details": {"tools": ["systemctl"]}
        }
        
        response = await formatter.format_information_response(
            sample_decision, sample_plan, analysis
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "information" in response.lower()
    
    @pytest.mark.asyncio
    async def test_format_plan_summary(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test plan summary formatting"""
        formatter = ResponseFormatter(mock_llm_client)
        
        response = await formatter.format_plan_summary(
            sample_decision, sample_selection, sample_plan
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "plan" in response.lower()
    
    @pytest.mark.asyncio
    async def test_format_approval_request(self, mock_llm_client, sample_decision, sample_plan):
        """Test approval request formatting"""
        formatter = ResponseFormatter(mock_llm_client)
        
        approval_points = [
            ApprovalPoint(
                step_id="step_002_restart_service",
                reason="Production service restart",
                risk_level="high",
                approver_role="operations_manager"
            )
        ]
        
        response = await formatter.format_approval_request(
            sample_decision, sample_plan, approval_points
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "approval" in response.lower()
    
    @pytest.mark.asyncio
    async def test_format_execution_ready(self, mock_llm_client, sample_decision, sample_plan):
        """Test execution ready formatting"""
        formatter = ResponseFormatter(mock_llm_client)
        
        response = await formatter.format_execution_ready(
            sample_decision, sample_plan
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "ready" in response.lower() or "execute" in response.lower()
    
    @pytest.mark.asyncio
    async def test_format_clarification_message(self, mock_llm_client, sample_decision):
        """Test clarification message formatting"""
        formatter = ResponseFormatter(mock_llm_client)
        
        clarifications = [
            ClarificationRequest(
                question="Which environment should I target?",
                options=["development", "production"],
                required=True,
                context="Environment affects safety procedures"
            )
        ]
        
        response = await formatter.format_clarification_message(
            sample_decision, clarifications
        )
        
        assert isinstance(response, str)
        assert len(response) > 0

# ============================================================================
# APPROVAL HANDLER TESTS
# ============================================================================

class TestApprovalHandler:
    """Test approval handling functionality"""
    
    def test_process_approval_points(self):
        """Test approval point processing"""
        handler = ApprovalHandler()
        
        approval_metadata = [
            {
                "step_id": "step_002_restart_service",
                "reason": "Production service restart requires approval",
                "risk_level": "high",
                "operation_type": "service_restart"
            }
        ]
        
        approval_points = handler.process_approval_points(approval_metadata)
        
        assert len(approval_points) == 1
        assert approval_points[0].step_id == "step_002_restart_service"
        assert approval_points[0].risk_level == "high"
        assert approval_points[0].approver_role == "operations_manager"
    
    def test_validate_approval_workflow(self):
        """Test approval workflow validation"""
        handler = ApprovalHandler()
        
        approval_points = [
            ApprovalPoint(
                step_id="step_001",
                reason="High-risk operation",
                risk_level="high",
                approver_role="operations_manager"
            ),
            ApprovalPoint(
                step_id="step_002",
                reason="Security change",
                risk_level="critical",
                approver_role="security_officer"
            )
        ]
        
        validation = handler.validate_approval_workflow(approval_points)
        
        assert validation["valid"] == True
        assert "approval_summary" in validation
        assert validation["approval_summary"]["operations_manager"] == 1
        assert validation["approval_summary"]["security_officer"] == 1
    
    def test_get_approval_summary(self):
        """Test approval summary generation"""
        handler = ApprovalHandler()
        
        approval_points = [
            ApprovalPoint(
                step_id="step_001",
                reason="High-risk operation",
                risk_level="high",
                approver_role="operations_manager"
            )
        ]
        
        summary = handler.get_approval_summary(approval_points)
        
        assert summary["total_approvals"] == 1
        assert "operations_manager" in summary["required_roles"]
        assert summary["risk_breakdown"]["high"] == 1
        assert summary["estimated_approval_time"] > 0
    
    def test_format_approval_requirements(self):
        """Test approval requirements formatting"""
        handler = ApprovalHandler()
        
        approval_points = [
            ApprovalPoint(
                step_id="step_001",
                reason="Production service restart",
                risk_level="high",
                approver_role="operations_manager"
            )
        ]
        
        requirements = handler.format_approval_requirements(approval_points)
        
        assert len(requirements) == 1
        assert "operations manager" in requirements[0].lower()
        assert "approval required" in requirements[0].lower()

# ============================================================================
# CONTEXT ANALYZER TESTS
# ============================================================================

class TestContextAnalyzer:
    """Test context analysis functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_information_request(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test information request analysis"""
        analyzer = ContextAnalyzer(mock_llm_client)
        
        # Modify decision for information request
        sample_decision.intent.category = "system_status"
        
        analysis = await analyzer.analyze_information_request(
            sample_decision, sample_selection, sample_plan
        )
        
        assert "sources" in analysis
        assert "insights" in analysis
        assert isinstance(analysis["sources"], list)
        assert isinstance(analysis["insights"], list)
    
    @pytest.mark.asyncio
    async def test_analyze_execution_context(self, mock_llm_client, sample_decision, sample_plan):
        """Test execution context analysis"""
        analyzer = ContextAnalyzer(mock_llm_client)
        
        analysis = await analyzer.analyze_execution_context(
            sample_decision, sample_plan
        )
        
        assert "complexity" in analysis
        assert "risks" in analysis
        assert "insights" in analysis
        assert "dependencies" in analysis
        assert "recommendations" in analysis
        
        assert analysis["complexity"] in ["low", "medium", "high"]
        assert isinstance(analysis["risks"], list)
        assert isinstance(analysis["insights"], list)

# ============================================================================
# STAGE D ANSWERER TESTS
# ============================================================================

class TestStageDAnswerer:
    """Test main Stage D Answerer functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_response_plan_summary(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test plan summary response generation"""
        answerer = StageDAnswerer(mock_llm_client)
        
        response = await answerer.generate_response(
            sample_decision, sample_selection, sample_plan
        )
        
        assert isinstance(response, ResponseV1)
        assert response.response_type == ResponseType.APPROVAL_REQUEST  # Due to approval points
        assert response.confidence in [ResponseConfidence.HIGH, ResponseConfidence.MEDIUM, ResponseConfidence.LOW]
        assert response.approval_required == True
        assert len(response.approval_points) > 0
        assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_information(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test information response generation"""
        answerer = StageDAnswerer(mock_llm_client)
        
        # Modify for information request
        sample_decision.intent.category = "system_status"
        sample_plan.execution_metadata.approval_points = []  # Remove approval points
        
        response = await answerer.generate_response(
            sample_decision, sample_selection, sample_plan
        )
        
        assert isinstance(response, ResponseV1)
        assert response.response_type == ResponseType.INFORMATION
        assert response.approval_required == False
        assert len(response.suggested_actions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_execution_ready(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test execution ready response generation"""
        answerer = StageDAnswerer(mock_llm_client)
        
        # Modify for low-risk execution ready
        sample_selection.policy.risk_level = RiskLevel.LOW
        sample_plan.execution_metadata.approval_points = []  # Remove approval points
        
        response = await answerer.generate_response(
            sample_decision, sample_selection, sample_plan
        )
        
        assert isinstance(response, ResponseV1)
        assert response.response_type == ResponseType.EXECUTION_READY
        assert response.approval_required == False
        assert response.execution_summary is not None
    
    @pytest.mark.asyncio
    async def test_request_clarification(self, mock_llm_client, sample_decision):
        """Test clarification request generation"""
        answerer = StageDAnswerer(mock_llm_client)
        
        missing_info = ["environment", "service_name"]
        
        clarification = await answerer.request_clarification(
            sample_decision, missing_info
        )
        
        assert isinstance(clarification, ClarificationResponse)
        assert clarification.response_type == ResponseType.CLARIFICATION
        assert len(clarification.clarifications_needed) == 2
        assert clarification.processing_time_ms > 0
    
    def test_health_status(self, mock_llm_client):
        """Test health status reporting"""
        answerer = StageDAnswerer(mock_llm_client)
        
        health = answerer.get_health_status()
        
        assert health["stage_d_answerer"] == "healthy"
        assert "components" in health
        assert "statistics" in health
        assert health["components"]["response_formatter"] == "healthy"
        assert health["components"]["approval_handler"] == "healthy"
        assert health["components"]["context_analyzer"] == "healthy"
    
    def test_get_capabilities(self, mock_llm_client):
        """Test capabilities reporting"""
        answerer = StageDAnswerer(mock_llm_client)
        
        capabilities = answerer.get_capabilities()
        
        assert capabilities["component"] == "stage_d_answerer"
        assert "capabilities" in capabilities
        assert "response_types" in capabilities
        assert "confidence_levels" in capabilities
        assert "features" in capabilities
        
        # Check specific capabilities
        assert "user_friendly_response_generation" in capabilities["capabilities"]
        assert "approval_workflow_handling" in capabilities["capabilities"]
        assert "context_aware_answering" in capabilities["capabilities"]

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_invalid_plan_handling(self, mock_llm_client, sample_decision, sample_selection):
        """Test handling of invalid execution plans"""
        answerer = StageDAnswerer(mock_llm_client)
        
        # Create invalid plan with no steps
        invalid_plan = PlanV1(
            plan=ExecutionPlan(
                steps=[],
                safety_checks=[],
                rollback_plan=[]
            ),
            execution_metadata=ExecutionMetadata(
                total_estimated_time=0,
                risk_factors=[],
                approval_points=[],
                checkpoints=[],
                observability_config={}
            ),
            timestamp="2024-01-01T12:00:02Z",
            processing_time_ms=50
        )
        
        response = await answerer.generate_response(
            sample_decision, sample_selection, invalid_plan
        )
        
        assert isinstance(response, ResponseV1)
        assert response.execution_summary.total_steps == 0
    
    @pytest.mark.asyncio
    async def test_llm_failure_fallback(self, sample_decision, sample_selection, sample_plan):
        """Test fallback when LLM fails"""
        # Create mock LLM that fails
        failing_llm = Mock()
        failing_llm.generate_response = AsyncMock(side_effect=Exception("LLM failed"))
        
        answerer = StageDAnswerer(failing_llm)
        
        response = await answerer.generate_response(
            sample_decision, sample_selection, sample_plan
        )
        
        assert isinstance(response, ResponseV1)
        # Should still generate a response even with LLM failure
    
    @pytest.mark.asyncio
    async def test_empty_clarification_handling(self, mock_llm_client, sample_decision):
        """Test handling of empty clarification requests"""
        answerer = StageDAnswerer(mock_llm_client)
        
        clarification = await answerer.request_clarification(
            sample_decision, []
        )
        
        assert isinstance(clarification, ClarificationResponse)
        # When no missing info is provided, should still generate a helpful clarification
        assert len(clarification.clarifications_needed) >= 1

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_response_generation_performance(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test response generation performance"""
        answerer = StageDAnswerer(mock_llm_client)
        
        start_time = time.time()
        response = await answerer.generate_response(
            sample_decision, sample_selection, sample_plan
        )
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert isinstance(response, ResponseV1)
        assert processing_time < 2000  # Should complete within 2 seconds
        assert response.processing_time_ms > 0
        assert response.processing_time_ms < 2000
    
    @pytest.mark.asyncio
    async def test_concurrent_response_generation(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test concurrent response generation"""
        answerer = StageDAnswerer(mock_llm_client)
        
        # Generate multiple responses concurrently
        tasks = []
        for i in range(5):
            task = answerer.generate_response(
                sample_decision, sample_selection, sample_plan
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 5
        for response in responses:
            assert isinstance(response, ResponseV1)
            assert response.processing_time_ms > 0
    
    def test_statistics_tracking(self, mock_llm_client):
        """Test statistics tracking accuracy"""
        answerer = StageDAnswerer(mock_llm_client)
        
        initial_stats = answerer.stats.copy()
        
        # Simulate some responses
        answerer._update_statistics(ResponseType.PLAN_SUMMARY, 100)
        answerer._update_statistics(ResponseType.APPROVAL_REQUEST, 150)
        
        assert answerer.stats["responses_generated"] == initial_stats["responses_generated"] + 2
        assert answerer.stats["approval_requests_created"] == initial_stats["approval_requests_created"] + 1
        assert answerer.stats["average_response_time_ms"] > 0

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test integration with other pipeline stages"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_response_generation(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test complete end-to-end response generation"""
        answerer = StageDAnswerer(mock_llm_client)
        
        # Test the complete flow
        response = await answerer.generate_response(
            sample_decision, sample_selection, sample_plan
        )
        
        # Validate complete response structure
        assert isinstance(response, ResponseV1)
        assert response.response_type in [rt for rt in ResponseType]
        assert response.confidence in [cl for cl in ResponseConfidence]
        assert response.execution_summary is not None
        assert response.execution_summary.total_steps == len(sample_plan.plan.steps)
        assert response.execution_summary.estimated_duration == sample_plan.execution_metadata.total_estimated_time
        assert len(response.suggested_actions) > 0
        assert response.response_id is not None
        assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_schema_compatibility(self, mock_llm_client, sample_decision, sample_selection, sample_plan):
        """Test schema compatibility across pipeline stages"""
        answerer = StageDAnswerer(mock_llm_client)
        
        response = await answerer.generate_response(
            sample_decision, sample_selection, sample_plan
        )
        
        # Test serialization/deserialization
        response_dict = response.model_dump()
        reconstructed = ResponseV1(**response_dict)
        
        assert reconstructed.response_type == response.response_type
        assert reconstructed.message == response.message
        assert reconstructed.confidence == response.confidence
        assert reconstructed.approval_required == response.approval_required
    
    def test_component_health_integration(self, mock_llm_client):
        """Test health status integration across components"""
        answerer = StageDAnswerer(mock_llm_client)
        
        health = answerer.get_health_status()
        
        # Verify all components report healthy
        assert health["stage_d_answerer"] == "healthy"
        assert all(
            status == "healthy" 
            for status in health["components"].values()
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])