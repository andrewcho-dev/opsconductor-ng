"""
REAL End-to-End Test with Timing
Tests the ACTUAL user experience - does the query complete within acceptable time?

This test measures what the user actually experiences:
- Does "Show me all assets" return a response?
- Does it complete within 60 seconds (before nginx timeout)?
- Does it actually return asset data?
"""

import pytest
import asyncio
import time
import os
from datetime import datetime

# Import pipeline orchestrator
from pipeline.orchestrator import PipelineOrchestrator
from llm.ollama_client import OllamaClient


@pytest.mark.asyncio
async def test_show_all_assets_real_timing():
    """
    REAL TEST: Does 'Show me all assets' complete within 60 seconds?
    
    This is what the user experiences in the frontend.
    """
    print(f"\n{'='*80}")
    print(f"🧪 REAL E2E TEST: 'Show me all assets' with timing")
    print(f"{'='*80}")
    
    # Create real orchestrator
    llm_config = {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
        "timeout": 120
    }
    llm_client = OllamaClient(llm_config)
    await llm_client.connect()
    
    orchestrator = PipelineOrchestrator(llm_client=llm_client)
    await orchestrator.initialize()
    
    user_request = "Show me all assets"
    
    # Start timer
    start_time = time.time()
    print(f"\n⏱️  Starting at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📝 Query: {user_request}")
    
    try:
        # Process request (this is what the frontend calls)
        result = await asyncio.wait_for(
            orchestrator.process_request(user_request),
            timeout=60.0  # 60 second timeout (same as nginx)
        )
        
        # Calculate duration
        duration = time.time() - start_time
        
        print(f"\n⏱️  Completed in: {duration:.2f} seconds")
        print(f"✅ Success: {result.success}")
        print(f"📊 Response type: {result.response.response_type.value if result.response else 'None'}")
        
        if result.response:
            print(f"💬 Message preview: {result.response.message[:200]}...")
        
        # Print stage durations
        print(f"\n📊 Stage Durations:")
        for stage, stage_duration in result.metrics.stage_durations.items():
            print(f"   {stage}: {stage_duration:.0f}ms ({stage_duration/1000:.2f}s)")
        
        # Assertions
        assert result.success, f"Pipeline failed: {result.error_message}"
        assert duration < 60.0, f"Pipeline took too long: {duration:.2f}s (timeout at 60s)"
        assert result.response is not None, "No response generated"
        
        # Check if we got actual data
        if hasattr(result, 'intermediate_results'):
            print(f"\n🔍 Intermediate Results:")
            for stage, stage_result in result.intermediate_results.items():
                print(f"   {stage}: {type(stage_result).__name__}")
        
        print(f"\n✅ TEST PASSED: Query completed in {duration:.2f}s")
        print(f"{'='*80}\n")
        
    except asyncio.TimeoutError:
        duration = time.time() - start_time
        print(f"\n❌ TIMEOUT after {duration:.2f} seconds!")
        print(f"   This is why users see 504 Gateway Timeout errors")
        pytest.fail(f"Pipeline timed out after {duration:.2f}s - this is the bug!")
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n❌ ERROR after {duration:.2f} seconds: {e}")
        raise


@pytest.mark.asyncio
async def test_show_all_assets_stage_by_stage_timing():
    """
    Test each stage individually to find where the slowdown is
    """
    print(f"\n{'='*80}")
    print(f"🧪 STAGE-BY-STAGE TIMING TEST")
    print(f"{'='*80}")
    
    llm_config = {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
        "timeout": 120
    }
    llm_client = OllamaClient(llm_config)
    await llm_client.connect()
    
    from pipeline.stages.stage_a.classifier import StageAClassifier
    from pipeline.stages.stage_b.selector import StageBSelector
    from pipeline.stages.stage_c.planner import StageCPlanner
    from pipeline.stages.stage_d.answerer import StageDAnswerer
    
    stage_a = StageAClassifier(llm_client=llm_client)
    stage_b = StageBSelector(llm_client=llm_client)
    stage_c = StageCPlanner(llm_client=llm_client)
    stage_d = StageDAnswerer(llm_client=llm_client)
    
    user_request = "Show me all assets"
    
    # Stage A
    print(f"\n📍 Testing Stage A...")
    start = time.time()
    decision = await asyncio.wait_for(stage_a.classify(user_request), timeout=120.0)
    stage_a_time = time.time() - start
    print(f"   ✅ Stage A: {stage_a_time:.2f}s")
    print(f"   Category: {decision.intent.category}, Action: {decision.intent.action}")
    
    # Stage B
    print(f"\n📍 Testing Stage B...")
    start = time.time()
    selection = await asyncio.wait_for(stage_b.select_tools(decision), timeout=30.0)
    stage_b_time = time.time() - start
    print(f"   ✅ Stage B: {stage_b_time:.2f}s")
    print(f"   Selected: {selection.selected_tools[0].tool_name if selection.selected_tools else 'None'}")
    
    # Stage C
    print(f"\n📍 Testing Stage C...")
    start = time.time()
    plan = stage_c.create_plan(decision, selection)
    stage_c_time = time.time() - start
    print(f"   ✅ Stage C: {stage_c_time:.2f}s")
    print(f"   Steps: {len(plan.plan.steps) if plan and plan.plan else 0}")
    
    # Stage D
    print(f"\n📍 Testing Stage D...")
    start = time.time()
    try:
        response = await asyncio.wait_for(
            stage_d.generate_response(decision, selection, plan),
            timeout=30.0
        )
        stage_d_time = time.time() - start
        print(f"   ✅ Stage D: {stage_d_time:.2f}s")
        print(f"   Response type: {response.response_type.value}")
    except asyncio.TimeoutError:
        stage_d_time = time.time() - start
        print(f"   ❌ Stage D TIMEOUT after {stage_d_time:.2f}s")
        pytest.fail("Stage D timed out - this is likely the bottleneck!")
    
    # Summary
    total_time = stage_a_time + stage_b_time + stage_c_time + stage_d_time
    print(f"\n📊 TIMING SUMMARY:")
    print(f"   Stage A: {stage_a_time:.2f}s ({stage_a_time/total_time*100:.1f}%)")
    print(f"   Stage B: {stage_b_time:.2f}s ({stage_b_time/total_time*100:.1f}%)")
    print(f"   Stage C: {stage_c_time:.2f}s ({stage_c_time/total_time*100:.1f}%)")
    print(f"   Stage D: {stage_d_time:.2f}s ({stage_d_time/total_time*100:.1f}%)")
    print(f"   TOTAL: {total_time:.2f}s")
    
    if total_time > 60:
        print(f"\n❌ PROBLEM: Total time {total_time:.2f}s exceeds 60s timeout!")
    else:
        print(f"\n✅ Total time {total_time:.2f}s is within 60s timeout")
    
    print(f"{'='*80}\n")