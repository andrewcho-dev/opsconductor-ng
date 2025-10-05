"""
Focused Test Suite: Stage B Asset Query Tool Selection
Tests specific to the issue discovered in live E2E testing where
"Show me all assets" incorrectly selected prometheus tool instead of asset service tool
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, List, Any

# Import Stage B components
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_b.tool_registry import ToolRegistry
from pipeline.stages.stage_b.profile_loader import ProfileLoader

# Import schemas
from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, EntityV1, DecisionType, ConfidenceLevel, RiskLevel
from pipeline.schemas.selection_v1 import SelectionV1

# Import LLM components
from llm.client import LLMClient

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
def mock_profile_loader():
    """Mock ProfileLoader to avoid database connections"""
    from pipeline.stages.stage_b.optimization_schemas import OptimizationProfilesConfig
    
    loader = Mock(spec=ProfileLoader)
    # Return empty OptimizationProfilesConfig to force deterministic scoring
    empty_config = OptimizationProfilesConfig(version="1.0", tools={})
    loader.load = Mock(return_value=empty_config)
    return loader

@pytest.fixture
def tool_registry():
    """Tool registry with default tools"""
    return ToolRegistry()

@pytest.fixture
def stage_b_selector(mock_llm_client, tool_registry, mock_profile_loader):
    """Stage B Selector with mocked dependencies"""
    return StageBSelector(
        llm_client=mock_llm_client,
        tool_registry=tool_registry,
        profile_loader=mock_profile_loader
    )

# ============================================================================
# DECISION FIXTURES FOR ASSET QUERIES
# ============================================================================

@pytest.fixture
def decision_list_all_assets():
    """Decision for 'Show me all assets' query"""
    return DecisionV1(
        decision_id="dec_asset_list_001",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="information",
            action="list",
            confidence=0.9
        ),
        entities=[
            EntityV1(type="asset", value="all", confidence=0.85)
        ],
        overall_confidence=0.88,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        original_request="Show me all assets",
        context={},
        requires_approval=False,
        next_stage="stage_b"
    )

@pytest.fixture
def decision_list_linux_servers():
    """Decision for 'Show me all Linux servers' query"""
    return DecisionV1(
        decision_id="dec_asset_filter_001",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="information",
            action="filter",
            confidence=0.92
        ),
        entities=[
            EntityV1(type="asset", value="servers", confidence=0.9),
            EntityV1(type="os", value="Linux", confidence=0.95)
        ],
        overall_confidence=0.92,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        original_request="Show me all Linux servers",
        context={},
        requires_approval=False,
        next_stage="stage_b"
    )

@pytest.fixture
def decision_count_assets():
    """Decision for 'How many assets do we have?' query"""
    return DecisionV1(
        decision_id="dec_asset_count_001",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="information",
            action="count",
            confidence=0.88
        ),
        entities=[
            EntityV1(type="asset", value="all", confidence=0.85)
        ],
        overall_confidence=0.87,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        original_request="How many assets do we have?",
        context={},
        requires_approval=False,
        next_stage="stage_b"
    )

@pytest.fixture
def decision_show_asset_details():
    """Decision for 'Show me details for server web-01' query"""
    return DecisionV1(
        decision_id="dec_asset_detail_001",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="information",
            action="get",
            confidence=0.93
        ),
        entities=[
            EntityV1(type="asset", value="server", confidence=0.9),
            EntityV1(type="hostname", value="web-01", confidence=0.95)
        ],
        overall_confidence=0.93,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        original_request="Show me details for server web-01",
        context={},
        requires_approval=False,
        next_stage="stage_b"
    )

# ============================================================================
# DECISION FIXTURES FOR NON-ASSET QUERIES (SHOULD NOT SELECT ASSET TOOLS)
# ============================================================================

@pytest.fixture
def decision_show_metrics():
    """Decision for 'Show me CPU metrics' query - should select monitoring tool"""
    return DecisionV1(
        decision_id="dec_metrics_001",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        intent=IntentV1(
            category="monitoring",
            action="get_metrics",
            confidence=0.91
        ),
        entities=[
            EntityV1(type="metric", value="cpu", confidence=0.93)
        ],
        overall_confidence=0.92,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        original_request="Show me CPU metrics",
        context={},
        requires_approval=False,
        next_stage="stage_b"
    )

# ============================================================================
# TEST CASES: ASSET QUERY TOOL SELECTION
# ============================================================================

class TestAssetQueryToolSelection:
    """Test that asset queries select the correct asset service tools"""
    
    @pytest.mark.asyncio
    async def test_list_all_assets_selects_asset_tool(self, stage_b_selector, decision_list_all_assets):
        """
        CRITICAL TEST: Verify 'Show me all assets' selects asset service tool, NOT prometheus
        This is the exact issue discovered in live E2E testing
        """
        # Execute tool selection
        selection = await stage_b_selector.select_tools(decision_list_all_assets)
        
        # Verify selection was created
        assert selection is not None
        assert isinstance(selection, SelectionV1)
        
        # Verify at least one tool was selected
        assert len(selection.selected_tools) > 0
        
        # Get the selected tool name
        selected_tool_name = selection.selected_tools[0].tool_name
        
        # CRITICAL ASSERTION: Should NOT be prometheus
        assert "prometheus" not in selected_tool_name.lower(), \
            f"ERROR: Selected prometheus tool for asset query! Selected: {selected_tool_name}"
        
        # CRITICAL ASSERTION: Should be asset-related tool
        assert any(keyword in selected_tool_name.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"ERROR: Did not select asset-related tool! Selected: {selected_tool_name}"
        
        print(f"✅ PASS: Correctly selected '{selected_tool_name}' for 'Show me all assets'")
    
    @pytest.mark.asyncio
    async def test_filter_linux_servers_selects_asset_tool(self, stage_b_selector, decision_list_linux_servers):
        """Verify 'Show me all Linux servers' selects asset service tool with filter capability"""
        selection = await stage_b_selector.select_tools(decision_list_linux_servers)
        
        assert selection is not None
        assert len(selection.selected_tools) > 0
        
        selected_tool_name = selection.selected_tools[0].tool_name
        
        # Should NOT be prometheus
        assert "prometheus" not in selected_tool_name.lower(), \
            f"ERROR: Selected prometheus for Linux server query! Selected: {selected_tool_name}"
        
        # Should be asset-related
        assert any(keyword in selected_tool_name.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"ERROR: Did not select asset tool for Linux server query! Selected: {selected_tool_name}"
        
        print(f"✅ PASS: Correctly selected '{selected_tool_name}' for 'Show me all Linux servers'")
    
    @pytest.mark.asyncio
    async def test_count_assets_selects_asset_tool(self, stage_b_selector, decision_count_assets):
        """Verify 'How many assets do we have?' selects asset service tool"""
        selection = await stage_b_selector.select_tools(decision_count_assets)
        
        assert selection is not None
        assert len(selection.selected_tools) > 0
        
        selected_tool_name = selection.selected_tools[0].tool_name
        
        # Should be asset-related
        assert any(keyword in selected_tool_name.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"ERROR: Did not select asset tool for count query! Selected: {selected_tool_name}"
        
        print(f"✅ PASS: Correctly selected '{selected_tool_name}' for asset count query")
    
    @pytest.mark.asyncio
    async def test_asset_details_selects_asset_tool(self, stage_b_selector, decision_show_asset_details):
        """Verify 'Show me details for server web-01' selects asset service tool"""
        selection = await stage_b_selector.select_tools(decision_show_asset_details)
        
        assert selection is not None
        assert len(selection.selected_tools) > 0
        
        selected_tool_name = selection.selected_tools[0].tool_name
        
        # Should be asset-related
        assert any(keyword in selected_tool_name.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"ERROR: Did not select asset tool for details query! Selected: {selected_tool_name}"
        
        print(f"✅ PASS: Correctly selected '{selected_tool_name}' for asset details query")

# ============================================================================
# TEST CASES: NON-ASSET QUERIES SHOULD NOT SELECT ASSET TOOLS
# ============================================================================

class TestNonAssetQueryToolSelection:
    """Test that non-asset queries do NOT select asset tools"""
    
    @pytest.mark.asyncio
    async def test_metrics_query_does_not_select_asset_tool(self, stage_b_selector, decision_show_metrics):
        """Verify 'Show me CPU metrics' does NOT select asset tool"""
        selection = await stage_b_selector.select_tools(decision_show_metrics)
        
        assert selection is not None
        assert len(selection.selected_tools) > 0
        
        selected_tool_name = selection.selected_tools[0].tool_name
        
        # Should NOT be asset tool for metrics query
        assert not any(keyword in selected_tool_name.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"ERROR: Selected asset tool for metrics query! Selected: {selected_tool_name}"
        
        # Should be monitoring-related
        assert any(keyword in selected_tool_name.lower() for keyword in ["prometheus", "metric", "monitor"]), \
            f"ERROR: Did not select monitoring tool for metrics query! Selected: {selected_tool_name}"
        
        print(f"✅ PASS: Correctly selected '{selected_tool_name}' for metrics query")

# ============================================================================
# TEST CASES: TOOL REGISTRY VALIDATION
# ============================================================================

class TestToolRegistryAssetTools:
    """Test that tool registry has proper asset service tools registered"""
    
    def test_tool_registry_has_asset_tools(self, tool_registry):
        """Verify tool registry contains asset service tools"""
        all_tools = tool_registry.get_all_tools()
        
        # Find asset-related tools
        asset_tools = [
            tool for tool in all_tools 
            if any(keyword in tool.name.lower() for keyword in ["asset", "inventory", "cmdb"])
        ]
        
        assert len(asset_tools) > 0, \
            "ERROR: Tool registry does not contain any asset service tools!"
        
        print(f"✅ PASS: Found {len(asset_tools)} asset tools in registry")
        for tool in asset_tools:
            print(f"  - {tool.name}: {tool.description}")
    
    def test_asset_tools_have_list_capability(self, tool_registry):
        """Verify asset tools have 'list' capability"""
        asset_tools = [
            tool for tool in tool_registry.get_all_tools()
            if any(keyword in tool.name.lower() for keyword in ["asset", "inventory", "cmdb"])
        ]
        
        # Check if any asset tool has list capability
        tools_with_list = [
            tool for tool in asset_tools
            if any(cap.name.lower() in ["list", "list_assets", "query"] for cap in tool.capabilities)
        ]
        
        assert len(tools_with_list) > 0, \
            "ERROR: No asset tools have 'list' capability!"
        
        print(f"✅ PASS: Found {len(tools_with_list)} asset tools with list capability")
    
    def test_asset_tools_have_filter_capability(self, tool_registry):
        """Verify asset tools have 'filter' capability"""
        asset_tools = [
            tool for tool in tool_registry.get_all_tools()
            if any(keyword in tool.name.lower() for keyword in ["asset", "inventory", "cmdb"])
        ]
        
        # Check if any asset tool has filter capability
        tools_with_filter = [
            tool for tool in asset_tools
            if any(cap.name.lower() in ["filter", "search", "query"] for cap in tool.capabilities)
        ]
        
        assert len(tools_with_filter) > 0, \
            "ERROR: No asset tools have 'filter' capability!"
        
        print(f"✅ PASS: Found {len(tools_with_filter)} asset tools with filter capability")

# ============================================================================
# TEST CASES: CAPABILITY MATCHING
# ============================================================================

class TestAssetCapabilityMatching:
    """Test capability matching for asset queries"""
    
    def test_information_intent_matches_asset_capabilities(self, tool_registry):
        """Verify information intent with asset entities matches asset tool capabilities"""
        # Get asset tools
        asset_tools = [
            tool for tool in tool_registry.get_all_tools()
            if any(keyword in tool.name.lower() for keyword in ["asset", "inventory", "cmdb"])
        ]
        
        # Check if asset tools support information intent
        info_supporting_tools = [
            tool for tool in asset_tools
            if "information" in [intent.lower() for intent in tool.supported_intents]
        ]
        
        assert len(info_supporting_tools) > 0, \
            "ERROR: No asset tools support 'information' intent!"
        
        print(f"✅ PASS: Found {len(info_supporting_tools)} asset tools supporting information intent")

# ============================================================================
# INTEGRATION TEST: END-TO-END ASSET QUERY
# ============================================================================

class TestAssetQueryEndToEnd:
    """Integration test for complete asset query flow"""
    
    @pytest.mark.asyncio
    async def test_complete_asset_query_flow(self, stage_b_selector, decision_list_all_assets):
        """
        Test complete flow from decision to selection for asset query
        This simulates what happens in the live system
        """
        # Execute selection
        selection = await stage_b_selector.select_tools(decision_list_all_assets)
        
        # Verify selection structure
        assert selection is not None
        assert selection.selection_id is not None
        assert selection.decision_id == decision_list_all_assets.decision_id
        assert len(selection.selected_tools) > 0
        
        # Verify tool selection
        selected_tool = selection.selected_tools[0]
        assert selected_tool.tool_name is not None
        assert selected_tool.justification is not None
        
        # Verify it's an asset tool
        assert any(keyword in selected_tool.tool_name.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"ERROR: Selected wrong tool type: {selected_tool.tool_name}"
        
        # Verify execution policy
        assert selection.execution_policy is not None
        assert selection.execution_policy.requires_approval == False  # Info queries don't need approval
        
        # Verify next stage
        assert selection.next_stage in ["stage_c", "stage_d", "stage_e"]
        
        print(f"✅ PASS: Complete asset query flow successful")
        print(f"  Selected Tool: {selected_tool.tool_name}")
        print(f"  Justification: {selected_tool.justification}")
        print(f"  Next Stage: {selection.next_stage}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])