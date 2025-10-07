#!/usr/bin/env python3
"""
Pipeline Performance Test Script

This script tests the pipeline with a sample request and logs detailed timing information.
Run this to see real-world performance metrics for each stage.
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.orchestrator import PipelineOrchestrator

# Configure logging to show all INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def test_pipeline_performance():
    """Test pipeline with a sample request and measure performance."""
    
    logger.info("=" * 80)
    logger.info("PIPELINE PERFORMANCE TEST")
    logger.info("=" * 80)
    
    # Initialize orchestrator
    logger.info("\n📦 Initializing pipeline orchestrator...")
    orchestrator = PipelineOrchestrator()
    
    try:
        await orchestrator.initialize()
        logger.info("✅ Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestrator: {e}")
        return
    
    # Test requests
    test_requests = [
        "List all servers in production",
        "What is the status of the database?",
        "Show me the CPU usage for web-server-01",
    ]
    
    for i, request in enumerate(test_requests, 1):
        logger.info("\n" + "=" * 80)
        logger.info(f"TEST {i}/{len(test_requests)}")
        logger.info("=" * 80)
        logger.info(f"Request: {request}")
        logger.info("-" * 80)
        
        try:
            result = await orchestrator.process_request(
                user_request=request,
                request_id=f"test-{i}"
            )
            
            logger.info("\n" + "=" * 80)
            logger.info(f"TEST {i} RESULTS")
            logger.info("=" * 80)
            logger.info(f"Success: {result.success}")
            logger.info(f"Response Type: {result.response.response_type}")
            logger.info(f"Message Preview: {result.response.message[:200]}...")
            logger.info("")
            logger.info("Performance Metrics:")
            logger.info(f"  Total Duration: {result.metrics.total_duration_ms:.2f}ms ({result.metrics.total_duration_ms/1000:.2f}s)")
            logger.info(f"  Stage A: {result.metrics.stage_durations.get('stage_a', 0):.2f}ms")
            logger.info(f"  Stage B: {result.metrics.stage_durations.get('stage_b', 0):.2f}ms")
            logger.info(f"  Stage C: {result.metrics.stage_durations.get('stage_c', 0):.2f}ms")
            logger.info(f"  Stage D: {result.metrics.stage_durations.get('stage_d', 0):.2f}ms")
            logger.info(f"  Stage E: {result.metrics.stage_durations.get('stage_e', 0):.2f}ms")
            logger.info(f"  Memory: {result.metrics.memory_usage_mb:.2f}MB")
            
        except Exception as e:
            logger.error(f"❌ Test {i} failed: {e}", exc_info=True)
        
        # Wait a bit between requests
        if i < len(test_requests):
            logger.info("\n⏳ Waiting 2 seconds before next test...")
            await asyncio.sleep(2)
    
    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_pipeline_performance())
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"\n\n❌ Test failed with error: {e}", exc_info=True)
        sys.exit(1)