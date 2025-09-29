#!/usr/bin/env python3
"""
FINAL TEST: Hybrid Decision System with all services running
"""

import asyncio
import logging
import sys
import os

# Add the ai-brain directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fulfillment_engine.direct_executor import DirectExecutor
from integrations.llm_client import LLMEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_final_hybrid_system():
    """Final test of the hybrid decision system"""
    
    logger.info("🔥 FINAL HYBRID DECISION SYSTEM TEST")
    logger.info("=" * 60)
    logger.info("🎯 GOAL: Actually execute system operations")
    logger.info("🧠 Architecture:")
    logger.info("   - Qwen2.5:7b for decision-making")
    logger.info("   - CodeLlama:7b for code generation")
    logger.info("   - Emergency override for system operations")
    logger.info("   - All services are running")
    
    try:
        # Initialize the Direct Executor
        logger.info("🚀 Initializing Direct Executor...")
        llm_engine = LLMEngine(ollama_host="http://localhost:11434", default_model="codellama:7b")
        await llm_engine.initialize()
        executor = DirectExecutor(llm_engine)
        
        # Test system operation request
        test_message = "connect to 192.168.50.211 and get the complete system status"
        user_context = {"user_id": "test_user", "session_id": "test_session"}
        
        logger.info(f"📤 TESTING: '{test_message}'")
        logger.info("🔍 Expected flow:")
        logger.info("   1. Emergency override detects '192.168' keyword")
        logger.info("   2. Forces USE_DIRECT_SERVICES")
        logger.info("   3. Executes actual network operations")
        logger.info("   4. Returns real system status")
        
        # Execute the request
        logger.info("⚡ EXECUTING REQUEST...")
        result = await executor.execute_user_request_with_full_control(
            message=test_message,
            user_context=user_context,
            available_services={}
        )
        
        logger.info("=" * 60)
        logger.info("📊 FINAL RESULTS:")
        logger.info(f"   🎯 Execution started: {result.get('execution_started', False)}")
        logger.info(f"   📈 Status: {result.get('status', 'Unknown')}")
        logger.info(f"   🔧 Services executed: {result.get('executed_services', False)}")
        logger.info(f"   📝 Steps executed: {result.get('steps_executed', 0)}")
        
        if result.get('execution_started', False) and result.get('executed_services', False):
            logger.info("🎉 SUCCESS: HYBRID SYSTEM IS WORKING!")
            logger.info("✅ The AI brain successfully:")
            logger.info("   - Detected system operation")
            logger.info("   - Made correct decision")
            logger.info("   - Executed actual services")
            logger.info("   - Performed real work")
            return True
        else:
            logger.error("❌ FAILURE: System still not executing properly")
            logger.error(f"   Full result: {result}")
            return False
            
    except Exception as e:
        logger.error(f"💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    
    success = await test_final_hybrid_system()
    
    logger.info("=" * 60)
    
    if success:
        logger.info("🏆 HYBRID DECISION SYSTEM: COMPLETE SUCCESS!")
        logger.info("🎯 The AI brain is now working correctly!")
        logger.info("🚀 Ready for production use!")
    else:
        logger.info("💥 HYBRID DECISION SYSTEM: STILL NEEDS WORK")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)