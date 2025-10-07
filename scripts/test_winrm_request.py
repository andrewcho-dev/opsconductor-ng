#!/usr/bin/env python3
"""
Test WinRM execution through Pipeline V2
Simulates a user request to connect to a Windows machine and execute a command
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.orchestrator_v2 import PipelineOrchestratorV2

async def test_winrm_request():
    """Test WinRM execution through Pipeline V2"""
    
    # Load environment variables
    load_dotenv()
    
    print("=" * 80)
    print("Testing WinRM Request through Pipeline V2")
    print("=" * 80)
    
    # Verify configuration
    print("\n📋 Configuration:")
    print(f"  LLM Provider: {os.getenv('LLM_PROVIDER', 'not set')}")
    print(f"  LLM Base URL: {os.getenv('LLM_BASE_URL', 'not set')}")
    print(f"  Database URL: {os.getenv('DATABASE_URL', 'not set')}")
    
    # Create orchestrator
    print("\n🔧 Initializing Pipeline Orchestrator V2...")
    orchestrator = PipelineOrchestratorV2()
    
    # Initialize and connect to LLM
    print("🔌 Connecting to LLM...")
    await orchestrator.initialize()
    print("✅ LLM connected")
    
    # User request - WinRM command execution
    user_request = (
        "Connect to 192.168.50.210 with username stationadmin and password Enabled123! "
        "and get the directory of c:\\ using WinRM"
    )
    
    print(f"\n📝 User Request:")
    print(f"  {user_request}")
    
    # Process request through pipeline
    print("\n🚀 Processing request through Pipeline V2...")
    print("-" * 80)
    
    try:
        result = await orchestrator.process_request(user_request)
        
        print("\n" + "=" * 80)
        print("PIPELINE RESULTS")
        print("=" * 80)
        
        # Overall status
        print(f"\n✅ Success: {result.success}")
        print(f"📊 Pipeline Status: {result.metrics.status}")
        print(f"⏱️  Total Duration: {result.metrics.total_duration_ms}ms ({result.metrics.total_duration_ms/1000:.2f}s)")
        
        # Stage durations
        print(f"\n⏱️  Stage Durations:")
        for stage_name, duration_ms in result.metrics.stage_durations.items():
            print(f"  {stage_name}: {duration_ms}ms ({duration_ms/1000:.2f}s)")
        
        # Response details
        if result.response:
            print(f"\n📄 Response Type: {result.response.response_type}")
            print(f"🎯 Confidence: {result.response.confidence}")
            print(f"\n💬 Message:")
            print(f"  {result.response.message}")
            
            # Selected tools
            if hasattr(result.response, 'selected_tools') and result.response.selected_tools:
                print(f"\n🔧 Selected Tools ({len(result.response.selected_tools)}):")
                for i, tool in enumerate(result.response.selected_tools, 1):
                    print(f"  {i}. {tool.tool_name}")
                    if hasattr(tool, 'reasoning') and tool.reasoning:
                        print(f"     Reasoning: {tool.reasoning}")
            
            # Execution summary
            if hasattr(result.response, 'execution_summary') and result.response.execution_summary:
                summary = result.response.execution_summary
                print(f"\n📊 Execution Summary:")
                print(f"  Total Steps: {summary.total_steps}")
                print(f"  Estimated Duration: {summary.estimated_duration}s")
                print(f"  Risk Level: {summary.risk_level}")
                print(f"  Tools Involved: {', '.join(summary.tools_involved)}")
                print(f"  Safety Checks: {summary.safety_checks}")
                print(f"  Approval Points: {summary.approval_points}")
            
            # Warnings
            if hasattr(result.response, 'warnings') and result.response.warnings:
                print(f"\n⚠️  Warnings:")
                for warning in result.response.warnings:
                    print(f"  - {warning}")
        
        # Intermediate results
        if result.intermediate_results:
            print(f"\n🔍 Intermediate Results:")
            for stage, data in result.intermediate_results.items():
                print(f"  {stage}: {type(data).__name__}")
                
                # Show Stage AB selection details
                if stage == "stage_ab" and hasattr(data, 'selected_tools'):
                    print(f"\n  Stage AB Selected Tools:")
                    if data.selected_tools:
                        for i, tool in enumerate(data.selected_tools, 1):
                            print(f"    {i}. {tool.tool_name}")
                            if hasattr(tool, 'reasoning'):
                                print(f"       Reasoning: {tool.reasoning}")
                    else:
                        print(f"    No tools selected")
                    
                    if hasattr(data, 'intent'):
                        print(f"\n  Detected Intent: {data.intent}")
                    if hasattr(data, 'confidence'):
                        print(f"  Selection Confidence: {data.confidence}")
                    if hasattr(data, 'next_stage'):
                        print(f"  Next Stage: {data.next_stage}")
                    if hasattr(data, 'execution_policy'):
                        policy = data.execution_policy
                        print(f"\n  Execution Policy:")
                        print(f"    Risk Level: {policy.risk_level}")
                        print(f"    Requires Approval: {policy.requires_approval}")
                        print(f"    Auto Execute: {policy.auto_execute}")
                
                # Show Stage E execution details
                if stage == "stage_e":
                    print(f"\n  Stage E Execution Details:")
                    if hasattr(data, 'execution_id'):
                        print(f"    Execution ID: {data.execution_id}")
                    if hasattr(data, 'status'):
                        print(f"    Status: {data.status}")
                    if hasattr(data, 'completed_steps'):
                        print(f"    Steps Completed: {data.completed_steps}/{data.total_steps}")
                    if hasattr(data, 'failed_steps'):
                        print(f"    Steps Failed: {data.failed_steps}")
                    if hasattr(data, 'progress_percentage'):
                        print(f"    Progress: {data.progress_percentage}%")
                    if hasattr(data, 'result') and data.result:
                        print(f"\n    Execution Result:")
                        import json
                        print(f"      {json.dumps(data.result, indent=6)}")
                    if hasattr(data, 'error_message') and data.error_message:
                        print(f"\n    Error: {data.error_message}")
        
        # Error message if failed
        if not result.success and result.error_message:
            print(f"\n❌ Error: {result.error_message}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error processing request: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return result.success

if __name__ == "__main__":
    success = asyncio.run(test_winrm_request())
    sys.exit(0 if success else 1)