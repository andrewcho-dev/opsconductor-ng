#!/usr/bin/env python3
"""
Single Request Performance Test

Quick test to see where time is being spent in the pipeline.
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.orchestrator import PipelineOrchestrator

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def main():
    """Test a single request with detailed timing."""
    
    print("\n" + "=" * 80)
    print("SINGLE REQUEST PERFORMANCE TEST")
    print("=" * 80 + "\n")
    
    # Get request from command line or use default
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        request = "List all servers in production"
    
    print(f"Testing request: {request}\n")
    print("-" * 80 + "\n")
    
    # Initialize and run
    orchestrator = PipelineOrchestrator()
    
    try:
        print("Initializing orchestrator...")
        await orchestrator.initialize()
        print("✅ Connected to LLM\n")
        
        print("Processing request...\n")
        result = await orchestrator.process_request(
            user_request=request,
            request_id="test-single"
        )
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"\n✅ Success: {result.success}")
        print(f"📊 Total Time: {result.metrics.total_duration_ms/1000:.2f} seconds")
        print(f"\nStage Breakdown:")
        print(f"  Stage A (Classification): {result.metrics.stage_durations.get('stage_a', 0)/1000:.2f}s")
        print(f"  Stage B (Tool Selection): {result.metrics.stage_durations.get('stage_b', 0)/1000:.2f}s")
        print(f"  Stage C (Planning):       {result.metrics.stage_durations.get('stage_c', 0)/1000:.2f}s")
        print(f"  Stage D (Response):       {result.metrics.stage_durations.get('stage_d', 0)/1000:.2f}s")
        print(f"  Stage E (Execution):      {result.metrics.stage_durations.get('stage_e', 0)/1000:.2f}s")
        print(f"\n💬 Response Preview:")
        print(f"  {result.response.message[:300]}...")
        print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())