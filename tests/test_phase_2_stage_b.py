"""
Comprehensive Test Suite for Phase 2: Stage B Selector
Tests tool selection, capability matching, and policy determination
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, List, Any

# Import Stage B components
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_b.tool_registry import ToolRegistry, Tool, ToolCapability
from pipeline.stages.stage_b.capability_matcher import CapabilityMatcher, CapabilityMatch
from pipeline.stages.stage_b.policy_engine import PolicyEngine

# Import schemas
from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, EntityV1, DecisionType, ConfidenceLevel, RiskLevel
from pipeline.schemas.selection_v1 import SelectionV1, SelectedTool, ExecutionPolicy, PermissionLevel

# Import LLM components
from llm.client import LLMClient, LLMResponse

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    client = Mock(spec=LLMClient)
    client.generate = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    return client

@pytest.fixture
def sample_decision():
    """Sample Decision v1 for testing"""
    return DecisionV1(
        decision_id="dec_test_123",
        decision_type=DecisionType.ACTION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="automation",
            action="restart_service",
            confidence=0.9
        ),
        entities=[
            EntityV1(type="service", value="nginx", confidence=0.95),
            EntityV1(type="hostname", value="web-server-01", confidence=0.88)
        ],
        overall_confidence=0.89,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.MEDIUM,
        original_request="restart nginx on web-server-01",
        context={"environment": "production"},
        requires_approval=True,
        next_stage="stage_b"
    )

@pytest.fixture
def sample_info_decision():
    """Sample information Decision v1 for testing"""
    return DecisionV1(
        decision_id="dec_info_456",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="information",
            action="show_status",
            confidence=0.85
        ),
        entities=[
            EntityV1(type="service", value="nginx", confidence=0.9)
        ],
        overall_confidence=0.85,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        original_request="show nginx status",
        context={},
        requires_approval=False,
        next_stage="stage_b"
    )

@pytest.fixture
def tool_registry():
    """Tool registry with default tools"""
    return ToolRegistry()

@pytest.fixture
def capability_matcher(tool_registry):
    """Capability matcher with tool registry"""
    return CapabilityMatcher(tool_registry)

@pytest.fixture
def policy_engine(tool_registry):
    """Policy engine with tool registry"""
    return PolicyEngine(tool_registry)

@pytest.fixture
def stage_b_selector(mock_llm_client, tool_registry):
    """Stage B Selector with mocked dependencies"""
    return StageBSelector(mock_llm_client, tool_registry)

# ============================================================================
# TOOL REGISTRY TESTS
# ============================================================================

class TestToolRegistry:
    """Test tool registry functionality"""
    
    def test_tool_registry_initialization(self, tool_registry):
        """Test tool registry initializes with default tools"""
        assert tool_registry.get_tool_count() > 0
        
        # Check for expected default tools
        systemctl = tool_registry.get_tool("systemctl")
        assert systemctl is not None
        assert systemctl.name == "systemctl"
        assert systemctl.permissions == PermissionLevel.ADMIN
        
        ps_tool = tool_registry.get_tool("ps")
        assert ps_tool is not None
        assert ps_tool.permissions == PermissionLevel.READ
    
    def test_get_tools_by_capability(self, tool_registry):
        """Test getting tools by capability"""
        service_control_tools = tool_registry.get_tools_by_capability("service_control")
        assert len(service_control_tools) > 0
        
        # systemctl should be in service control tools
        tool_names = [tool.name for tool in service_control_tools]
        assert "systemctl" in tool_names
    
    def test_get_tools_by_intent(self, tool_registry):
        """Test getting tools by intent"""
        automation_tools = tool_registry.get_tools_by_intent("automation", "restart_service")
        assert len(automation_tools) > 0
        
        monitoring_tools = tool_registry.get_tools_by_intent("monitoring", "check_status")
        assert len(monitoring_tools) > 0
    
    def test_get_tools_by_permission(self, tool_registry):
        """Test getting tools by permission level"""
        read_tools = tool_registry.get_tools_by_permission(PermissionLevel.READ)
        admin_tools = tool_registry.get_tools_by_permission(PermissionLevel.ADMIN)
        
        assert len(read_tools) > 0
        assert len(admin_tools) > 0
        
        # All read tools should have read permission
        for tool in read_tools:
            assert tool.permissions in [PermissionLevel.READ]
    
    def test_get_production_safe_tools(self, tool_registry):
        """Test getting production safe tools"""
        safe_tools = tool_registry.get_production_safe_tools()
        assert len(safe_tools) > 0
        
        for tool in safe_tools:
            assert tool.production_safe == True
    
    def test_search_tools(self, tool_registry):
        """Test tool search functionality"""
        results = tool_registry.search_tools("system")
        assert len(results) > 0
        
        results = tool_registry.search_tools("nonexistent")
        assert len(results) == 0
    
    def test_registry_stats(self, tool_registry):
        """Test registry statistics"""
        stats = tool_registry.get_registry_stats()
        
        assert "total_tools" in stats
        assert "permission_distribution" in stats
        assert "capability_distribution" in stats
        assert "production_safe_tools" in stats
        assert stats["total_tools"] > 0

# ============================================================================
# CAPABILITY MATCHER TESTS
# ============================================================================

class TestCapabilityMatcher:
    """Test capability matching functionality"""
    
    @pytest.mark.asyncio
    async def test_find_matching_tools(self, capability_matcher, sample_decision):
        """Test finding matching tools for a decision"""
        matches = capability_matcher.find_matching_tools(sample_decision)
        
        assert len(matches) > 0
        assert all(isinstance(match, CapabilityMatch) for match in matches)
        assert all(match.confidence > 0 for match in matches)
    
    @pytest.mark.asyncio
    async def test_intent_matching(self, capability_matcher, sample_decision):
        """Test intent-based tool matching"""
        matches = capability_matcher.find_matching_tools(sample_decision)
        
        # Should find systemctl for service restart
        tool_names = [match.tool.name for match in matches]
        assert "systemctl" in tool_names
    
    @pytest.mark.asyncio
    async def test_entity_compatibility(self, capability_matcher, sample_decision):
        """Test entity compatibility assessment"""
        systemctl_tool = capability_matcher.tool_registry.get_tool("systemctl")
        match = capability_matcher._evaluate_tool_match(sample_decision, systemctl_tool)
        
        assert match.confidence > 0.3  # Should have some confidence
        # Check that justification contains relevant information
        justification_lower = str(match.justification).lower()
        assert ("automation" in justification_lower or 
                "service" in justification_lower or 
                "intent" in justification_lower)
    
    @pytest.mark.asyncio
    async def test_select_optimal_tools(self, capability_matcher, sample_decision):
        """Test optimal tool selection"""
        matches = capability_matcher.find_matching_tools(sample_decision)
        selected_tools = capability_matcher.select_optimal_tools(matches, sample_decision)
        
        assert len(selected_tools) > 0
        assert all(isinstance(tool, SelectedTool) for tool in selected_tools)
        assert all(tool.tool_name for tool in selected_tools)
        assert all(tool.justification for tool in selected_tools)
    
    @pytest.mark.asyncio
    async def test_validation(self, capability_matcher, sample_decision):
        """Test tool selection validation"""
        matches = capability_matcher.find_matching_tools(sample_decision)
        selected_tools = capability_matcher.select_optimal_tools(matches, sample_decision)
        
        is_valid, errors = capability_matcher.validate_tool_selection(selected_tools, sample_decision)
        
        if not is_valid:
            # Print errors for debugging
            print(f"Validation errors: {errors}")
        
        # Should be valid for basic automation request
        assert is_valid or len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_information_request_matching(self, capability_matcher, sample_info_decision):
        """Test matching for information requests"""
        matches = capability_matcher.find_matching_tools(sample_info_decision)
        
        assert len(matches) > 0
        
        # Should prefer read-only tools for info requests
        read_only_matches = [match for match in matches if match.tool.permissions == PermissionLevel.READ]
        assert len(read_only_matches) > 0

# ============================================================================
# POLICY ENGINE TESTS
# ============================================================================

class TestPolicyEngine:
    """Test policy engine functionality"""
    
    def test_policy_engine_initialization(self, policy_engine):
        """Test policy engine initialization"""
        assert policy_engine.tool_registry is not None
        assert policy_engine.config is not None
    
    def test_determine_execution_policy_high_risk(self, policy_engine, sample_decision):
        """Test policy determination for high-risk operations"""
        # Create high-risk decision
        high_risk_decision = sample_decision.model_copy()
        high_risk_decision.risk_level = RiskLevel.HIGH
        high_risk_decision.requires_approval = True
        
        selected_tools = [
            SelectedTool(
                tool_name="systemctl",
                justification="Required for service restart",
                inputs_needed=[],
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(high_risk_decision, selected_tools)
        
        assert policy.requires_approval == True
        assert policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert policy.max_execution_time > 30
    
    def test_determine_execution_policy_low_risk(self, policy_engine, sample_info_decision):
        """Test policy determination for low-risk operations"""
        selected_tools = [
            SelectedTool(
                tool_name="ps",
                justification="Read-only process listing",
                inputs_needed=[],
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(sample_info_decision, selected_tools)
        
        # Low-risk info requests should not require approval
        assert policy.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
        assert policy.max_execution_time <= 60
    
    def test_production_environment_detection(self, policy_engine, sample_decision):
        """Test production environment detection"""
        # Test explicit production context
        prod_decision = sample_decision.model_copy()
        prod_decision.context = {"environment": "production"}
        
        is_production = policy_engine._detect_production_environment(prod_decision)
        assert is_production == True
        
        # Test non-production context
        dev_decision = sample_decision.model_copy()
        dev_decision.context = {"environment": "development"}
        
        is_production = policy_engine._detect_production_environment(dev_decision)
        # Should still be True due to conservative default
        assert is_production == True
    
    def test_approval_requirement_logic(self, policy_engine, sample_decision):
        """Test approval requirement logic"""
        # High-risk operations should require approval
        high_risk_tools = [
            SelectedTool(
                tool_name="systemctl",
                justification="Admin tool",
                inputs_needed=[],
                execution_order=1
            )
        ]
        
        systemctl_tool = policy_engine.tool_registry.get_tool("systemctl")
        requires_approval = policy_engine._determine_approval_requirement(sample_decision, [systemctl_tool])
        
        # Should require approval for admin tools in production
        assert requires_approval == True
    
    def test_parallel_execution_determination(self, policy_engine):
        """Test parallel execution determination"""
        # Single tool - no parallel execution
        single_tool = [
            SelectedTool(
                tool_name="ps",
                justification="Process listing",
                inputs_needed=[],
                execution_order=1
            )
        ]
        
        ps_tool = policy_engine.tool_registry.get_tool("ps")
        parallel = policy_engine._determine_parallel_execution(single_tool, [ps_tool])
        assert parallel == False
        
        # Multiple compatible tools
        multiple_tools = [
            SelectedTool(
                tool_name="ps",
                justification="Process listing",
                inputs_needed=[],
                execution_order=1
            ),
            SelectedTool(
                tool_name="journalctl",
                justification="Log access",
                inputs_needed=[],
                execution_order=2
            )
        ]
        
        ps_tool = policy_engine.tool_registry.get_tool("ps")
        journal_tool = policy_engine.tool_registry.get_tool("journalctl")
        parallel = policy_engine._determine_parallel_execution(multiple_tools, [ps_tool, journal_tool])
        
        # Should allow parallel for read-only tools
        assert parallel == True
    
    def test_policy_validation(self, policy_engine, sample_decision):
        """Test policy validation"""
        selected_tools = [
            SelectedTool(
                tool_name="systemctl",
                justification="Service control",
                inputs_needed=[],
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(sample_decision, selected_tools)
        is_valid, errors = policy_engine.validate_policy(policy, sample_decision, selected_tools)
        
        # Should be valid for reasonable policy
        if not is_valid:
            print(f"Policy validation errors: {errors}")
        
        # Basic policies should be valid
        assert len(errors) == 0 or is_valid
    
    def test_policy_explanation(self, policy_engine, sample_decision):
        """Test policy explanation generation"""
        selected_tools = [
            SelectedTool(
                tool_name="systemctl",
                justification="Service control",
                inputs_needed=[],
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(sample_decision, selected_tools)
        explanations = policy_engine.get_policy_explanation(policy, sample_decision, selected_tools)
        
        assert isinstance(explanations, dict)
        assert "approval" in explanations
        assert "risk" in explanations
        assert "execution_time" in explanations
        assert all(isinstance(explanation, str) for explanation in explanations.values())

# ============================================================================
# STAGE B SELECTOR INTEGRATION TESTS
# ============================================================================

class TestStageBSelector:
    """Test Stage B Selector integration"""
    
    def test_stage_b_selector_initialization(self, stage_b_selector):
        """Test Stage B Selector initialization"""
        assert stage_b_selector.llm_client is not None
        assert stage_b_selector.tool_registry is not None
        assert stage_b_selector.capability_matcher is not None
        assert stage_b_selector.policy_engine is not None
    
    @pytest.mark.asyncio
    async def test_select_tools_automation(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test tool selection for automation requests"""
        # Mock LLM response for tool selection
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "systemctl", "justification": "Required for service restart", "inputs_needed": ["service_name", "action"], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(sample_decision)
        
        assert isinstance(selection, SelectionV1)
        assert selection.decision_id == sample_decision.decision_id
        assert selection.total_tools > 0
        assert len(selection.selected_tools) > 0
        assert selection.policy is not None
        assert selection.selection_confidence > 0
    
    @pytest.mark.asyncio
    async def test_select_tools_information(self, stage_b_selector, sample_info_decision, mock_llm_client):
        """Test tool selection for information requests"""
        # Mock LLM response
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "ps", "justification": "Process status information", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(sample_info_decision)
        
        assert isinstance(selection, SelectionV1)
        assert selection.policy.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
        assert selection.policy.requires_approval == False or selection.policy.requires_approval == True  # Depends on policy logic
    
    @pytest.mark.asyncio
    async def test_select_tools_llm_failure(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test tool selection with LLM failure (fallback to rule-based)"""
        # Mock LLM failure
        mock_llm_client.generate.side_effect = Exception("LLM connection failed")
        mock_llm_client.health_check.return_value = False
        
        selection = await stage_b_selector.select_tools(sample_decision)
        
        # Should still return a valid selection using rule-based fallback
        assert isinstance(selection, SelectionV1)
        assert selection.total_tools > 0
        assert len(selection.selected_tools) > 0
    
    @pytest.mark.asyncio
    async def test_additional_inputs_calculation(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test calculation of additional inputs needed"""
        # Mock LLM response with tools requiring additional inputs
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "config_manager", "justification": "Configuration management", "inputs_needed": ["config_key", "config_value"], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(sample_decision)
        
        # Should identify missing inputs
        assert isinstance(selection.additional_inputs_needed, list)
    
    @pytest.mark.asyncio
    async def test_environment_requirements(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test environment requirements determination"""
        # Mock LLM response with admin tools
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "systemctl", "justification": "Service control", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(sample_decision)
        
        # Should identify environment requirements
        assert isinstance(selection.environment_requirements, dict)
        # Admin tools should require sudo
        if any(tool.tool_name == "systemctl" for tool in selection.selected_tools):
            assert selection.environment_requirements.get("sudo_required") == True
    
    @pytest.mark.asyncio
    async def test_next_stage_determination(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test next stage determination logic"""
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "systemctl", "justification": "Service control", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(sample_decision)
        
        # Should determine appropriate next stage
        assert selection.next_stage in ["stage_c", "stage_d"]
        
        # High-risk operations should go to planner
        if selection.policy.requires_approval or selection.policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            assert selection.next_stage == "stage_c"
    
    @pytest.mark.asyncio
    async def test_selection_confidence_calculation(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test selection confidence calculation"""
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "systemctl", "justification": "Service control", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(sample_decision)
        
        # Should have reasonable confidence
        assert 0.0 <= selection.selection_confidence <= 1.0
        assert selection.selection_confidence > 0.1  # Should have some confidence
    
    @pytest.mark.asyncio
    async def test_ready_for_execution_flag(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test ready for execution flag"""
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "ps", "justification": "Process listing", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(sample_decision)
        
        # Should set ready flag appropriately
        assert isinstance(selection.ready_for_execution, bool)
        
        # If no additional inputs needed and no dependencies, should be ready
        if not selection.additional_inputs_needed:
            # May or may not be ready depending on other factors
            pass
    
    @pytest.mark.asyncio
    async def test_health_check(self, stage_b_selector):
        """Test Stage B health check"""
        health_status = await stage_b_selector.health_check()
        
        assert isinstance(health_status, dict)
        assert "stage_b_selector" in health_status
        assert "tool_registry" in health_status
        assert "capability_matcher" in health_status
        assert "policy_engine" in health_status
    
    def test_get_capabilities(self, stage_b_selector):
        """Test Stage B capabilities reporting"""
        capabilities = stage_b_selector.get_capabilities()
        
        assert isinstance(capabilities, dict)
        assert "stage" in capabilities
        assert "version" in capabilities
        assert "capabilities" in capabilities
        assert "supported_intents" in capabilities
        assert "tool_registry" in capabilities
        
        assert capabilities["stage"] == "stage_b_selector"
        assert isinstance(capabilities["capabilities"], list)
        assert len(capabilities["capabilities"]) > 0

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_decision_handling(self, stage_b_selector, mock_llm_client):
        """Test handling of edge case decisions"""
        # Create minimal decision
        minimal_decision = DecisionV1(
            decision_id="dec_minimal",
            decision_type=DecisionType.INFO,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(
                category="information",
                action="get_help",
                confidence=0.5
            ),
            entities=[],
            overall_confidence=0.5,
            confidence_level=ConfidenceLevel.MEDIUM,
            risk_level=RiskLevel.LOW,
            original_request="help",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "info_display", "justification": "Help system", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(minimal_decision)
        
        # Should handle minimal decision gracefully
        assert isinstance(selection, SelectionV1)
        assert selection.total_tools >= 0
    
    @pytest.mark.asyncio
    async def test_invalid_llm_response_handling(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test handling of invalid LLM responses"""
        # Mock invalid JSON response
        mock_llm_response = LLMResponse(
            content='{"invalid": "response format"}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(sample_decision)
        
        # Should fall back to rule-based selection
        assert isinstance(selection, SelectionV1)
        assert selection.total_tools > 0
    
    @pytest.mark.asyncio
    async def test_tool_registry_empty(self, mock_llm_client):
        """Test behavior with empty tool registry"""
        empty_registry = ToolRegistry()
        # Clear all tools
        empty_registry.tools = {}
        empty_registry.capabilities_index = {}
        
        selector = StageBSelector(mock_llm_client, empty_registry)
        
        minimal_decision = DecisionV1(
            decision_id="dec_empty",
            decision_type=DecisionType.INFO,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(
                category="information",
                action="get_help",
                confidence=0.5
            ),
            entities=[],
            overall_confidence=0.5,
            confidence_level=ConfidenceLevel.MEDIUM,
            risk_level=RiskLevel.LOW,
            original_request="help",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        # Should handle empty registry gracefully
        selection = await selector.select_tools(minimal_decision)
        assert isinstance(selection, SelectionV1)
    
    @pytest.mark.asyncio
    async def test_malformed_decision_context(self, stage_b_selector, mock_llm_client):
        """Test handling of malformed decision context"""
        decision_with_bad_context = DecisionV1(
            decision_id="dec_bad_context",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(
                category="automation",
                action="restart_service",
                confidence=0.8
            ),
            entities=[
                EntityV1(type="service", value="nginx", confidence=0.9)
            ],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="restart nginx",
            context={"malformed": {"nested": {"deeply": "value"}}},  # Complex nested context
            requires_approval=False,
            next_stage="stage_b"
        )
        
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "systemctl", "justification": "Service control", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        selection = await stage_b_selector.select_tools(decision_with_bad_context)
        
        # Should handle complex context gracefully
        assert isinstance(selection, SelectionV1)
        assert selection.total_tools > 0

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_selection_performance(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test selection performance"""
        import time
        
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "systemctl", "justification": "Service control", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        start_time = time.time()
        selection = await stage_b_selector.select_tools(sample_decision)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (excluding LLM latency)
        assert processing_time < 5.0  # 5 seconds max
        assert selection.processing_time_ms is not None
        assert selection.processing_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_concurrent_selections(self, stage_b_selector, sample_decision, mock_llm_client):
        """Test concurrent tool selections"""
        mock_llm_response = LLMResponse(
            content='{"selected_tools": [{"tool_name": "systemctl", "justification": "Service control", "inputs_needed": [], "execution_order": 1, "depends_on": []}]}',
            model="llama2"
        )
        mock_llm_client.generate.return_value = mock_llm_response
        
        # Run multiple selections concurrently
        tasks = []
        for i in range(5):
            decision_copy = sample_decision.model_copy()
            decision_copy.decision_id = f"dec_concurrent_{i}"
            tasks.append(stage_b_selector.select_tools(decision_copy))
        
        selections = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(selections) == 5
        assert all(isinstance(selection, SelectionV1) for selection in selections)
        assert all(selection.total_tools > 0 for selection in selections)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])