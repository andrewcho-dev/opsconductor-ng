"""
End-to-End Intensive Testing for Asset Queries
Tests the FULL pipeline: Stage A → Stage B → Stage C with REAL services

NO MOCKS - All components are real:
- Real Ollama LLM
- Real Stage A (intent classification)
- Real Stage B (tool selection)
- Real Stage C (execution planning)
- Real database tool catalog
- Real asset service integration

This test suite validates that asset-related queries work correctly
through the entire pipeline and select the right tools.
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone

# Import pipeline stages
from pipeline.stages.stage_a.classifier import StageAClassifier
from pipeline.stages.stage_b.selector import StageBSelector
from pipeline.stages.stage_c.planner import StageCPlanner
from llm.ollama_client import OllamaClient

# Import schemas
from pipeline.schemas.decision_v1 import DecisionV1


async def create_full_pipeline():
    """Create the full pipeline with real components"""
    llm_config = {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
        "timeout": 120
    }
    llm_client = OllamaClient(llm_config)
    await llm_client.connect()
    
    # Create all stages with real LLM
    stage_a = StageAClassifier(llm_client=llm_client)
    stage_b = StageBSelector(llm_client=llm_client)
    stage_c = StageCPlanner(llm_client=llm_client)
    
    return stage_a, stage_b, stage_c, llm_client


@pytest.mark.asyncio
class TestE2EAssetQueriesIntensive:
    """Intensive end-to-end testing of asset queries through full pipeline"""
    
    async def test_e2e_show_all_assets(self):
        """E2E Test: 'Show me all assets' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Show me all assets"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A: Intent Classification
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        print(f"   Confidence: {decision.intent.confidence}")
        print(f"   Entities: {decision.entities}")
        
        # Verify Stage A classified correctly
        assert decision.intent.category == "asset_management", \
            f"Stage A failed: Expected category 'asset_management', got '{decision.intent.category}'"
        assert decision.intent.action in ["list_assets", "search_assets"], \
            f"Stage A failed: Expected action 'list_assets' or 'search_assets', got '{decision.intent.action}'"
        
        # Stage B: Tool Selection
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        print(f"   Selected Tools: {[t.tool_name for t in selection.selected_tools]}")
        print(f"   Primary Tool: {selection.selected_tools[0].tool_name}")
        print(f"   Justification: {selection.selected_tools[0].justification}")
        print(f"   Inputs Needed: {selection.selected_tools[0].inputs_needed}")
        
        # Verify Stage B selected asset tool (NOT prometheus)
        primary_tool = selection.selected_tools[0].tool_name
        assert "prometheus" not in primary_tool.lower(), \
            f"❌ CRITICAL BUG: Stage B selected prometheus instead of asset tool!\n" \
            f"   Tool: {primary_tool}\n" \
            f"   This is the bug we're trying to fix!"
        
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"Stage B failed: Selected tool '{primary_tool}' is not an asset tool"
        
        # Stage C: Execution Planning
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Steps: {len(plan.plan.steps)}")
        for i, step in enumerate(plan.plan.steps, 1):
            print(f"   Step {i}: {step.tool} - {step.description}")
        
        # Verify Stage C created a valid plan
        assert plan is not None
        assert len(plan.plan.steps) > 0
        assert plan.plan.steps[0].tool == primary_tool
        
        print(f"\n✅ E2E TEST PASSED: Full pipeline correctly handled '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_list_linux_servers(self):
        """E2E Test: 'Show me all Linux servers' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Show me all Linux servers"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        print(f"   Entities: {[(e.type, e.value) for e in decision.entities]}")
        
        assert decision.intent.category == "asset_management"
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        # Stage C
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Plan created with {len(plan.plan.steps)} steps")
        
        assert len(plan.plan.steps) > 0
        
        print(f"\n✅ E2E TEST PASSED: '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_count_assets(self):
        """E2E Test: 'How many assets do we have?' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "How many assets do we have?"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        
        assert decision.intent.category == "asset_management"
        assert decision.intent.action in ["count_assets", "list_assets"]
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        # Stage C
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Plan created with {len(plan.plan.steps)} steps")
        
        assert len(plan.plan.steps) > 0
        
        print(f"\n✅ E2E TEST PASSED: '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_find_windows_servers(self):
        """E2E Test: 'Find all Windows servers' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Find all Windows servers"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        print(f"   Entities: {[(e.type, e.value) for e in decision.entities]}")
        
        assert decision.intent.category == "asset_management"
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        # Stage C
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Plan created with {len(plan.plan.steps)} steps")
        
        assert len(plan.plan.steps) > 0
        
        print(f"\n✅ E2E TEST PASSED: '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_list_database_servers(self):
        """E2E Test: 'List all database servers' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "List all database servers"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        
        assert decision.intent.category == "asset_management"
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        # Stage C
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Plan created with {len(plan.plan.steps)} steps")
        
        assert len(plan.plan.steps) > 0
        
        print(f"\n✅ E2E TEST PASSED: '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_get_asset_by_hostname(self):
        """E2E Test: 'Get asset info for server web-01' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Get asset info for server web-01"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        print(f"   Entities: {[(e.type, e.value) for e in decision.entities]}")
        
        assert decision.intent.category == "asset_management"
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        # Stage C
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Plan created with {len(plan.plan.steps)} steps")
        
        assert len(plan.plan.steps) > 0
        
        print(f"\n✅ E2E TEST PASSED: '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_search_assets_by_ip(self):
        """E2E Test: 'Search for assets with IP 10.0.1.5' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Search for assets with IP 10.0.1.5"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        print(f"   Entities: {[(e.type, e.value) for e in decision.entities]}")
        
        assert decision.intent.category == "asset_management"
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        # Stage C
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Plan created with {len(plan.plan.steps)} steps")
        
        assert len(plan.plan.steps) > 0
        
        print(f"\n✅ E2E TEST PASSED: '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_list_production_assets(self):
        """E2E Test: 'Show me all production assets' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Show me all production assets"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        print(f"   Entities: {[(e.type, e.value) for e in decision.entities]}")
        
        assert decision.intent.category == "asset_management"
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        # Stage C
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Plan created with {len(plan.plan.steps)} steps")
        
        assert len(plan.plan.steps) > 0
        
        print(f"\n✅ E2E TEST PASSED: '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_count_linux_servers(self):
        """E2E Test: 'How many Linux servers are there?' through full pipeline"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "How many Linux servers are there?"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST: {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        print(f"   Entities: {[(e.type, e.value) for e in decision.entities]}")
        
        assert decision.intent.category == "asset_management"
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        # Stage C
        print("\n📍 STAGE C: Execution Planning")
        plan = stage_c.create_plan(decision, selection)
        print(f"   Plan created with {len(plan.plan.steps)} steps")
        
        assert len(plan.plan.steps) > 0
        
        print(f"\n✅ E2E TEST PASSED: '{user_request}'")
        print(f"{'='*80}\n")
    
    
    async def test_e2e_metrics_should_not_use_asset_tools(self):
        """E2E Test: 'Show me CPU usage' should NOT select asset tools"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Show me CPU usage"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST (Negative): {user_request}")
        print(f"{'='*80}")
        
        # Stage A
        print("\n📍 STAGE A: Intent Classification")
        decision = await stage_a.classify(user_request)
        print(f"   Category: {decision.intent.category}")
        print(f"   Action: {decision.intent.action}")
        
        # Should be monitoring, not asset_management
        assert decision.intent.category != "asset_management", \
            f"Stage A incorrectly classified metrics query as asset_management"
        
        # Stage B
        print("\n📍 STAGE B: Tool Selection")
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Selected Tool: {primary_tool}")
        
        # Should select prometheus/metrics tool, NOT asset tool
        assert not any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"]), \
            f"Stage B incorrectly selected asset tool for metrics query"
        
        print(f"\n✅ E2E TEST PASSED: Metrics query correctly avoided asset tools")
        print(f"{'='*80}\n")


@pytest.mark.asyncio
class TestE2EAssetQueriesEdgeCases:
    """Test edge cases and variations in asset queries"""
    
    async def test_e2e_ambiguous_query_what_servers(self):
        """E2E Test: 'What servers do we have?' - ambiguous phrasing"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "What servers do we have?"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST (Edge Case): {user_request}")
        print(f"{'='*80}")
        
        decision = await stage_a.classify(user_request)
        print(f"   Stage A: {decision.intent.category} / {decision.intent.action}")
        
        assert decision.intent.category == "asset_management"
        
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Stage B: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        print(f"✅ PASSED\n")
    
    
    async def test_e2e_informal_query_gimme_assets(self):
        """E2E Test: 'Gimme all the assets' - informal phrasing"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Gimme all the assets"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST (Edge Case): {user_request}")
        print(f"{'='*80}")
        
        decision = await stage_a.classify(user_request)
        print(f"   Stage A: {decision.intent.category} / {decision.intent.action}")
        
        assert decision.intent.category == "asset_management"
        
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Stage B: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        print(f"✅ PASSED\n")
    
    
    async def test_e2e_complex_query_multiple_filters(self):
        """E2E Test: 'Show me all Linux servers in production with more than 16GB RAM'"""
        stage_a, stage_b, stage_c, llm_client = await create_full_pipeline()
        
        user_request = "Show me all Linux servers in production with more than 16GB RAM"
        print(f"\n{'='*80}")
        print(f"🧪 E2E TEST (Complex): {user_request}")
        print(f"{'='*80}")
        
        decision = await stage_a.classify(user_request)
        print(f"   Stage A: {decision.intent.category} / {decision.intent.action}")
        print(f"   Entities: {[(e.type, e.value) for e in decision.entities]}")
        
        assert decision.intent.category == "asset_management"
        
        selection = await stage_b.select_tools(decision)
        primary_tool = selection.selected_tools[0].tool_name
        print(f"   Stage B: {primary_tool}")
        
        assert "prometheus" not in primary_tool.lower()
        assert any(keyword in primary_tool.lower() for keyword in ["asset", "inventory", "cmdb"])
        
        print(f"✅ PASSED\n")