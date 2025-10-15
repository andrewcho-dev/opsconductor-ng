"""
Debug script to test multi-IP request handling
"""
import asyncio
import logging
import sys
import os

# Set environment to use vLLM
os.environ['LLM_PROVIDER'] = 'vllm'
os.environ['LLM_BASE_URL'] = 'http://localhost:8000/v1'
os.environ['LLM_MODEL'] = 'Qwen/Qwen2.5-14B-Instruct-AWQ'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_multi_ip_request():
    """Test the multi-IP request flow"""
    from pipeline.orchestrator import PipelineOrchestrator
    from llm.factory import get_default_llm_client
    
    # Initialize
    llm_client = get_default_llm_client()
    orchestrator = PipelineOrchestrator(llm_client)
    await orchestrator.initialize()
    
    # Test request (slightly modified to bypass cache)
    user_request = "list files on the c drive for 192.168.50.213 and 192.168.50.214"
    
    logger.info(f"Testing request: {user_request}")
    logger.info("=" * 80)
    
    try:
        result = await orchestrator.process_request(user_request)
        
        logger.info("=" * 80)
        logger.info("RESULT:")
        logger.info(f"Success: {result.success}")
        logger.info(f"Response Type: {result.response.response_type}")
        logger.info(f"Message: {result.response.message}")
        logger.info(f"Needs Clarification: {result.needs_clarification}")
        
        if result.intermediate_results.get("stage_a"):
            stage_a = result.intermediate_results["stage_a"]
            logger.info(f"\nStage A Intent: {stage_a.intent.category}/{stage_a.intent.action}")
            logger.info(f"Stage A Entities: {[e.value for e in stage_a.entities]}")
        
        if result.intermediate_results.get("stage_b"):
            stage_b = result.intermediate_results["stage_b"]
            logger.info(f"\nStage B Selected Tools: {[t.tool_name for t in stage_b.selected_tools]}")
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    asyncio.run(test_multi_ip_request())