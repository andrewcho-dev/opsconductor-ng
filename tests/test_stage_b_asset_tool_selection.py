"""
Real Integration Tests for Stage B Asset Tool Selection
Tests the actual tool selection logic with real services - NO MOCKS!
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone

# Import Stage B components
from pipeline.stages.stage_b.selector import StageBSelector
from llm.ollama_client import OllamaClient

# Import schemas
from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, EntityV1, DecisionType, ConfidenceLevel, RiskLevel


async def create_real_stage_b():
    """Helper to create a real Stage B with real Ollama LLM client"""
    llm_config = {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
        "timeout": 120
    }
    llm_client = OllamaClient(llm_config)
    await llm_client.connect()
    
    # Use default ProfileLoader (loads from database)
    stage_b = StageBSelector(llm_client=llm_client)
    return stage_b


@pytest.mark.asyncio
class TestAssetQueryRealToolSelection:
    """Test that asset queries select the correct asset tools"""
    
    async def test_list_all_assets_query(self):
        """Test: 'Show me all assets' should select asset tool, NOT prometheus"""
        real_stage_b = await create_real_stage_b()
        
        decision = DecisionV1(
            decision_id="test_asset_list",
            decision_type=DecisionType.INFO,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(
                category="asset_management",
                action="list_assets",
                confidence=0.95
            ),
            entities=[],
            overall_confidence=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="Show me all assets",
            context={},
            requires_approval=False,
            next_stage="stage_b",
            reasoning="User wants to see all assets in the system"
        )
        
        selection = await real_stage_b.select_tools(decision)
        
        # Verify we got a selection
        assert selection is not None
        assert len(selection.selected_tools) > 0
        
        # Verify the selected tool is an asset tool
        selected_tool = selection.selected_tools[0]
        print(f"\n🔍 Selected tool: {selected_tool.tool_name}")
        print(f"🔍 Justification: {selected_tool.justification}")
        print(f"🔍 Inputs needed: {selected_tool.inputs_needed}")
        
        # CRITICAL: Should NOT be prometheus
        assert "prometheus" not in selected_tool.tool_name.lower(), \
            f"❌ BUG CONFIRMED: Selected prometheus tool instead of asset tool!\n" \
            f"   Tool: {selected_tool.tool_name}\n" \
            f"   Justification: {selected_tool.justification}\n" \
            f"   This is the exact bug discovered in E2E testing!"
        
        # Should be an asset-related tool
        assert any(keyword in selected_tool.tool_name.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"ERROR: Selected tool '{selected_tool.tool_name}' is not an asset tool!"
    
    
    async def test_list_linux_servers_query(self):
        """Test: 'Show me all Linux servers' should select asset tool"""
        real_stage_b = await create_real_stage_b()
        
        decision = DecisionV1(
            decision_id="test_linux_servers",
            decision_type=DecisionType.INFO,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(
                category="asset_management",
                action="list_assets",
                confidence=0.92
            ),
            entities=[
                EntityV1(type="os_type", value="Linux", confidence=0.95),
                EntityV1(type="asset_type", value="server", confidence=0.90)
            ],
            overall_confidence=0.92,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="Show me all Linux servers",
            context={},
            requires_approval=False,
            next_stage="stage_b",
            reasoning="User wants to see all Linux servers"
        )
        
        selection = await real_stage_b.select_tools(decision)
        
        assert selection is not None
        assert len(selection.selected_tools) > 0
        
        selected_tool = selection.selected_tools[0]
        print(f"\n🔍 Selected tool for Linux servers: {selected_tool.tool_name}")
        
        # Should NOT be prometheus
        assert "prometheus" not in selected_tool.tool_name.lower()
        
        # Should be asset-related
        assert any(keyword in selected_tool.tool_name.lower() for keyword in ["asset", "inventory", "cmdb"])
    
    
    async def test_count_assets_query(self):
        """Test: 'How many assets do we have?' should select asset tool"""
        real_stage_b = await create_real_stage_b()
        
        decision = DecisionV1(
            decision_id="test_count_assets",
            decision_type=DecisionType.INFO,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(
                category="asset_management",
                action="count_assets",
                confidence=0.90
            ),
            entities=[],
            overall_confidence=0.90,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="How many assets do we have?",
            context={},
            requires_approval=False,
            next_stage="stage_b",
            reasoning="User wants to know the total number of assets"
        )
        
        selection = await real_stage_b.select_tools(decision)
        
        assert selection is not None
        assert len(selection.selected_tools) > 0
        
        selected_tool = selection.selected_tools[0]
        print(f"\n🔍 Selected tool for counting assets: {selected_tool.tool_name}")
        
        assert "prometheus" not in selected_tool.tool_name.lower()
        assert any(keyword in selected_tool.tool_name.lower() for keyword in ["asset", "inventory", "cmdb"])
    
    
    async def test_metrics_query_should_not_select_asset_tool(self):
        """Test: Metrics queries should select prometheus, NOT asset tools"""
        real_stage_b = await create_real_stage_b()
        
        decision = DecisionV1(
            decision_id="test_metrics",
            decision_type=DecisionType.INFO,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=IntentV1(
                category="monitoring",
                action="query_metrics",
                confidence=0.95
            ),
            entities=[
                EntityV1(type="metric", value="cpu_usage", confidence=0.95)
            ],
            overall_confidence=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            risk_level=RiskLevel.LOW,
            original_request="Show me CPU usage",
            context={},
            requires_approval=False,
            next_stage="stage_b",
            reasoning="User wants to see CPU metrics"
        )
        
        selection = await real_stage_b.select_tools(decision)
        
        assert selection is not None
        assert len(selection.selected_tools) > 0
        
        selected_tool = selection.selected_tools[0]
        print(f"\n🔍 Selected tool for metrics: {selected_tool.tool_name}")
        
        # For metrics, prometheus is correct
        assert any(keyword in selected_tool.tool_name.lower() for keyword in ["prometheus", "metric", "monitor"])


@pytest.mark.asyncio
class TestToolRegistryHasAssetTools:
    """Verify that the tool registry actually has asset tools registered"""
    
    async def test_tool_registry_has_asset_tools(self):
        """Verify asset tools are registered in the tool registry"""
        real_stage_b = await create_real_stage_b()
        registry = real_stage_b.tool_registry
        
        # Get all tools
        all_tools = registry.get_all_tools()
        print(f"\n📋 Total tools in registry: {len(all_tools)}")
        
        for tool in all_tools:
            print(f"  - {tool.name}: {tool.capabilities}")
        
        # Should have at least one asset tool
        asset_tools = [t for t in all_tools if any("asset" in cap.name.lower() for cap in t.capabilities)]
        
        assert len(asset_tools) > 0, \
            f"ERROR: No asset tools found in registry! Available tools: {[t.name for t in all_tools]}"
        
        print(f"\n✅ Found {len(asset_tools)} asset tools:")
        for tool in asset_tools:
            print(f"  - {tool.name}: {[cap.name for cap in tool.capabilities]}")