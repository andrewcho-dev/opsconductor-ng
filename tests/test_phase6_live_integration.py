"""
Phase 6: Live Asset-Service Integration Testing

Tests the complete asset-service integration with the live API to identify
why queries like "how many assets do we have?" are failing in production.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.orchestrator import PipelineOrchestrator
from llm.ollama_client import OllamaClient


class TestPhase6LiveIntegration:
    """Live integration tests with real asset-service API"""
    
    @pytest_asyncio.fixture
    async def orchestrator(self):
        """Create orchestrator with real LLM client"""
        config = {
            "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "default_model": os.getenv("DEFAULT_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
            "timeout": int(os.getenv("OLLAMA_TIMEOUT", "30"))
        }
        llm_client = OllamaClient(config)
        orchestrator = PipelineOrchestrator(llm_client)
        await orchestrator.initialize()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_asset_count_query(self, orchestrator):
        """Test: 'how many assets do we have?' - The failing query"""
        query = "how many assets do we have?"
        
        print(f"\n{'='*80}")
        print(f"TESTING QUERY: {query}")
        print(f"{'='*80}\n")
        
        result = await orchestrator.process_request(query)
        
        # Print detailed results
        print(f"\n{'='*80}")
        print(f"PIPELINE RESULT")
        print(f"{'='*80}")
        print(f"Success: {result.success}")
        print(f"Needs Clarification: {result.needs_clarification}")
        print(f"Total Duration: {result.metrics.total_duration_ms:.2f}ms")
        print(f"\nStage Durations:")
        for stage, duration in result.metrics.stage_durations.items():
            print(f"  {stage}: {duration:.2f}ms")
        
        print(f"\n{'='*80}")
        print(f"STAGE A (CLASSIFICATION)")
        print(f"{'='*80}")
        if "stage_a" in result.intermediate_results:
            stage_a = result.intermediate_results["stage_a"]
            print(f"Intent Category: {stage_a.intent.category}")
            print(f"Intent Action: {stage_a.intent.action}")
            print(f"Intent Confidence: {stage_a.intent.confidence}")
            print(f"Overall Confidence: {stage_a.overall_confidence}")
            print(f"Confidence Level: {stage_a.confidence_level}")
            print(f"Entities: {stage_a.entities}")
            print(f"Decision Type: {stage_a.decision_type}")
            print(f"Risk Level: {stage_a.risk_level}")
            if hasattr(stage_a, 'next_stage'):
                print(f"Next Stage: {stage_a.next_stage}")
        
        print(f"\n{'='*80}")
        print(f"STAGE B (TOOL SELECTION)")
        print(f"{'='*80}")
        if "stage_b" in result.intermediate_results:
            stage_b = result.intermediate_results["stage_b"]
            print(f"Selected Tools: {[tool.tool_name for tool in stage_b.selected_tools]}")
            print(f"Tool Count: {len(stage_b.selected_tools)}")
            for tool in stage_b.selected_tools:
                print(f"\n  Tool: {tool.tool_name}")
                print(f"    Justification: {tool.justification}")
                print(f"    Execution Order: {tool.execution_order}")
                print(f"    Inputs Needed: {tool.inputs_needed}")
        
        print(f"\n{'='*80}")
        print(f"STAGE C (PLANNING)")
        print(f"{'='*80}")
        if "stage_c" in result.intermediate_results:
            stage_c = result.intermediate_results["stage_c"]
            print(f"Plan Steps: {len(stage_c.plan.steps)}")
            for i, step in enumerate(stage_c.plan.steps, 1):
                print(f"\n  Step {i}: {step.description}")
                print(f"    Tool: {step.tool}")
                print(f"    Inputs: {step.inputs}")
                print(f"    Execution Order: {step.execution_order}")
        
        print(f"\n{'='*80}")
        print(f"STAGE D (RESPONSE)")
        print(f"{'='*80}")
        print(f"Response Type: {result.response.response_type}")
        print(f"Message: {result.response.message}")
        print(f"Confidence: {result.response.confidence}")
        if result.response.technical_details:
            print(f"Technical Details: {result.response.technical_details}")
        if result.response.warnings:
            print(f"Warnings: {result.response.warnings}")
        if result.response.execution_summary:
            print(f"Execution Summary: {result.response.execution_summary}")
        
        print(f"\n{'='*80}\n")
        
        # Assertions
        assert result.success, f"Pipeline failed: {result.error_message}"
        assert "stage_a" in result.intermediate_results, "Stage A did not execute"
        
        # Check if asset-service tools were selected
        if "stage_b" in result.intermediate_results:
            stage_b = result.intermediate_results["stage_b"]
            tool_names = [tool.tool_name for tool in stage_b.selected_tools]
            print(f"\n🔍 DIAGNOSTIC: Selected tools = {tool_names}")
            
            # Check if asset-service tools are in the selection
            asset_tools = [name for name in tool_names if 'asset' in name.lower()]
            if not asset_tools:
                print(f"\n❌ PROBLEM IDENTIFIED: No asset-service tools selected!")
                print(f"   Query: '{query}'")
                stage_a = result.intermediate_results['stage_a']
                print(f"   Intent: {stage_a.intent.category}/{stage_a.intent.action}")
                print(f"   Selected: {tool_names}")
            else:
                print(f"\n✅ Asset-service tools selected: {asset_tools}")
    
    @pytest.mark.asyncio
    async def test_list_servers_query(self, orchestrator):
        """Test: 'list all servers' - Another common query"""
        query = "list all servers"
        
        print(f"\n{'='*80}")
        print(f"TESTING QUERY: {query}")
        print(f"{'='*80}\n")
        
        result = await orchestrator.process_request(query)
        
        # Print summary
        print(f"\nSuccess: {result.success}")
        print(f"Duration: {result.metrics.total_duration_ms:.2f}ms")
        
        if "stage_a" in result.intermediate_results:
            stage_a = result.intermediate_results["stage_a"]
            print(f"Intent: {stage_a.intent.category}/{stage_a.intent.action}")
        
        if "stage_b" in result.intermediate_results:
            stage_b = result.intermediate_results["stage_b"]
            tool_names = [tool.tool_name for tool in stage_b.selected_tools]
            print(f"Tools: {tool_names}")
            
            asset_tools = [name for name in tool_names if 'asset' in name.lower()]
            if asset_tools:
                print(f"✅ Asset-service tools selected: {asset_tools}")
            else:
                print(f"❌ No asset-service tools selected!")
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_specific_server_query(self, orchestrator):
        """Test: 'show me server 192.168.50.215' - Specific asset query"""
        query = "show me server 192.168.50.215"
        
        print(f"\n{'='*80}")
        print(f"TESTING QUERY: {query}")
        print(f"{'='*80}\n")
        
        result = await orchestrator.process_request(query)
        
        # Print summary
        print(f"\nSuccess: {result.success}")
        print(f"Duration: {result.metrics.total_duration_ms:.2f}ms")
        
        if "stage_a" in result.intermediate_results:
            stage_a = result.intermediate_results["stage_a"]
            print(f"Intent: {stage_a.intent.category}/{stage_a.intent.action}")
            print(f"Entities: {stage_a.entities}")
        
        if "stage_b" in result.intermediate_results:
            stage_b = result.intermediate_results["stage_b"]
            tool_names = [tool.tool_name for tool in stage_b.selected_tools]
            print(f"Tools: {tool_names}")
            
            asset_tools = [name for name in tool_names if 'asset' in name.lower()]
            if asset_tools:
                print(f"✅ Asset-service tools selected: {asset_tools}")
            else:
                print(f"❌ No asset-service tools selected!")
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_tool_registry_has_asset_tools(self, orchestrator):
        """Test: Verify asset-service tools are registered"""
        print(f"\n{'='*80}")
        print(f"TOOL REGISTRY INSPECTION")
        print(f"{'='*80}\n")
        
        all_tools = orchestrator.tool_registry.get_all_tools()
        print(f"Total tools registered: {len(all_tools)}")
        
        asset_tools = [tool for tool in all_tools if 'asset' in tool.name.lower()]
        print(f"\nAsset-service tools found: {len(asset_tools)}")
        
        for tool in asset_tools:
            print(f"\n  Tool: {tool.name}")
            print(f"    Description: {tool.description}")
            print(f"    Capabilities:")
            for cap in tool.capabilities:
                print(f"      - {cap.name}: {cap.description}")
        
        # Check capability index
        print(f"\n{'='*80}")
        print(f"CAPABILITY INDEX")
        print(f"{'='*80}\n")
        
        asset_capabilities = ['asset_query', 'infrastructure_info', 'resource_listing']
        for cap in asset_capabilities:
            tools = orchestrator.tool_registry.get_tools_by_capability(cap)
            print(f"Capability '{cap}': {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool.name}")
        
        # Check intent mappings
        print(f"\n{'='*80}")
        print(f"INTENT MAPPINGS")
        print(f"{'='*80}\n")
        
        test_intents = [
            ("information", "list_resources"),
            ("information", "query_infrastructure"),
            ("information", "get_asset_info"),
            ("monitoring", "check_status"),
        ]
        
        for category, action in test_intents:
            tools = orchestrator.tool_registry.get_tools_by_intent(category, action)
            print(f"Intent '{category}/{action}': {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool.name}")
        
        assert len(asset_tools) >= 2, "Expected at least 2 asset-service tools"
        assert any('query' in tool.name.lower() for tool in asset_tools), "Expected asset-service-query tool"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])