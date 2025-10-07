#!/usr/bin/env python3
"""
Test Pipeline V2 with Active Directory query that matches existing tools.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Verify LLM provider
print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
print(f"LLM_BASE_URL: {os.getenv('LLM_BASE_URL')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print()

from pipeline.orchestrator_v2 import PipelineOrchestratorV2


async def test_ad_query():
    """Test with an Active Directory query that should match existing tools."""
    
    print("=" * 80)
    print("Testing Pipeline V2 with Active Directory Query")
    print("=" * 80)
    
    # Initialize orchestrator
    print("\n1. Initializing Orchestrator V2...")
    orchestrator = PipelineOrchestratorV2()
    await orchestrator.initialize()
    
    # Create a request that should match AD tools
    user_request = "Show me all Active Directory users in the domain"
    session_id = "test_session_ad"
    
    print(f"\n2. Processing request: '{user_request}'")
    print("\nExpected behavior:")
    print("  - Stage AB should select 'Get-ADUser' tool")
    print("  - Should route to Stage C (Planner)")
    print("  - Stage C should create execution plan")
    print("  - Should route to Stage E (Executor)")
    print("  - Stage E should execute the plan")
    
    print("\n3. Sending request to pipeline...")
    print("-" * 80)
    
    try:
        result = await orchestrator.process_request(
            user_request=user_request,
            session_id=session_id,
            context={}
        )
        
        print("\n" + "=" * 80)
        print("RESPONSE RECEIVED")
        print("=" * 80)
        
        print(f"\nSuccess: {result.success}")
        print(f"Pipeline Status: {result.metrics.status}")
        print(f"Total Duration: {result.metrics.total_duration_ms}ms")
        
        if result.error_message:
            print(f"\nError Message: {result.error_message}")
        
        print(f"\nResponse:")
        print(f"  Type: {result.response.response_type}")
        print(f"  Message: {result.response.message}")
        print(f"  Confidence: {result.response.confidence}")
        
        if result.response.execution_summary:
            print(f"\nExecution Summary:")
            print(f"  Total Steps: {result.response.execution_summary.total_steps}")
            print(f"  Estimated Duration: {result.response.execution_summary.estimated_duration}s")
            print(f"  Risk Level: {result.response.execution_summary.risk_level}")
            print(f"  Tools: {', '.join(result.response.execution_summary.tools_involved)}")
        
        if result.response.warnings:
            print(f"\nWarnings:")
            for warning in result.response.warnings:
                print(f"  - {warning}")
        
        if result.metrics.stage_durations:
            print(f"\nStage Durations:")
            for stage, duration in result.metrics.stage_durations.items():
                print(f"  {stage}: {duration}ms")
        
        if result.intermediate_results:
            print(f"\nIntermediate Results:")
            for stage, data in result.intermediate_results.items():
                print(f"  {stage}: {type(data).__name__}")
                if hasattr(data, 'selected_tools'):
                    print(f"    Selected tools: {len(data.selected_tools)}")
                    for tool in data.selected_tools:
                        tool_name = tool.tool_name if hasattr(tool, 'tool_name') else str(tool)
                        print(f"      - {tool_name}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETED SUCCESSFULLY" if result.success else "TEST FAILED")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("ERROR OCCURRED")
        print("=" * 80)
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        import traceback
        print("\nFull Traceback:")
        print("-" * 80)
        traceback.print_exc()
        
        return None


if __name__ == "__main__":
    result = asyncio.run(test_ad_query())
    sys.exit(0 if result else 1)