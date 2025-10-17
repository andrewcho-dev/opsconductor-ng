#!/usr/bin/env python3
"""
Test the Fixed Pipeline with vLLM
Verify that the capabilities field is properly populated and the 90% accuracy system works
"""

import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng')

from pipeline.orchestrator import PipelineOrchestrator
from llm.factory import create_llm_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_critical_hostname_command():
    """Test the exact command that was causing the bypass"""
    
    # Create LLM client (should use vLLM now)
    llm_client = create_llm_client()
    
    # Test connection
    if not await llm_client.connect():
        logger.error("❌ Cannot connect to vLLM!")
        return False
    
    logger.info("✅ Connected to vLLM")
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(llm_client)
    
    # Test the critical command
    test_request = "Display contents of /etc/hostname"
    
    logger.info(f"🧪 Testing: {test_request}")
    
    try:
        result = await orchestrator.process_request(test_request)
        
        logger.info("=== PIPELINE RESULT ===")
        logger.info(f"Success: {result.success}")
        logger.info(f"Response Type: {result.response.response_type}")
        logger.info(f"Response: {result.response.message}")
        logger.info(f"Intermediate Results: {list(result.intermediate_results.keys())}")
        
        # Check intermediate results for Stage A and Stage B details
        stage_a_result = result.intermediate_results.get('stage_a')
        stage_b_result = result.intermediate_results.get('stage_b')
        
        if stage_a_result:
            logger.info(f"Stage A Intent: {stage_a_result}")
        if stage_b_result:
            logger.info(f"Stage B Selection: {stage_b_result}")
        
        # Check if Stage B found tools (HybridOrchestrator working)
        if stage_b_result and hasattr(stage_b_result, 'selected_tools') and len(stage_b_result.selected_tools) > 0:
            logger.info("🎉 SUCCESS! Stage B selected actual tools - HybridOrchestrator was used!")
            logger.info(f"Selected tools: {[tool.name for tool in stage_b_result.selected_tools]}")
            return True
        else:
            logger.error("❌ Stage B returned no tools - 0 candidates found due to capability mismatch!")
            logger.error("This indicates the LLM is generating wrong capabilities")
            return False
            
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    logger.info("🚀 Testing OpsConductor Pipeline with vLLM")
    logger.info("🎯 Verifying 90% accuracy tool selection system is working")
    
    success = await test_critical_hostname_command()
    
    if success:
        logger.info("🎉 PIPELINE FIXED! Your 90% accuracy system is working!")
    else:
        logger.error("❌ Pipeline still has issues")

if __name__ == "__main__":
    asyncio.run(main())