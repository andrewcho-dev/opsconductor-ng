#!/usr/bin/env python3
"""
Test the new Hybrid Decision System
- Qwen2.5:7b for decision-making
- CodeLlama:7b for code generation
- Emergency override for system operations
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

async def test_hybrid_decision_system():
    """Test the hybrid decision system with real system operations"""
    
    logger.info("🚀 Testing Hybrid Decision System...")
    logger.info("📋 Architecture:")
    logger.info("   - Qwen2.5:7b for decision-making")
    logger.info("   - CodeLlama:7b for code generation")
    logger.info("   - Emergency override for system operations")
    
    try:
        # Initialize the Direct Executor
        logger.info("🧠 Initializing Direct Executor...")
        llm_engine = LLMEngine(ollama_host="http://localhost:11434", default_model="codellama:7b")
        await llm_engine.initialize()
        executor = DirectExecutor(llm_engine)
        
        # Test system operation request
        test_message = "connect to 192.168.50.211 and get the complete system status"
        user_context = {"user_id": "test_user", "session_id": "test_session"}
        
        logger.info(f"📤 Testing request: '{test_message}'")
        logger.info("🔍 This should trigger:")
        logger.info("   1. Emergency override detection (192.168 keyword)")
        logger.info("   2. OR Qwen2.5 decision-making")
        logger.info("   3. Direct service execution")
        
        # Execute the request
        result = await executor.execute_user_request_with_full_control(
            message=test_message,
            user_context=user_context,
            available_services={}
        )
        
        logger.info("📊 RESULT:")
        logger.info(f"   - Execution started: {result.get('execution_started', False)}")
        logger.info(f"   - Response type: {type(result.get('response', 'Unknown'))}")
        logger.info(f"   - Response preview: {str(result.get('response', 'No response'))[:200]}...")
        
        # Check if execution actually started
        if result.get('execution_started', False):
            logger.info("✅ SUCCESS: System actually executed the request!")
            return True
        else:
            logger.error("❌ FAILURE: System did not execute the request")
            logger.error(f"   Full result: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_decision_models():
    """Test the different models for decision-making"""
    
    logger.info("🧪 Testing different models for decision-making...")
    
    models_to_test = [
        "qwen2.5:7b",
        "mistral:7b", 
        "gemma2:9b",
        "llama2:7b"
    ]
    
    decision_prompt = """
You are the AI Brain. Analyze this request and decide how to handle it:

USER REQUEST: "connect to 192.168.50.211 and get the complete system status"

AVAILABLE OPTIONS:
- USE_DIRECT_SERVICES: For actual system operations, IP connections, status queries
- USE_CONVERSATION: For general chat that doesn't require real data

RULES:
- "connect to [IP]" = USE_DIRECT_SERVICES
- "system status" = USE_DIRECT_SERVICES
- IP addresses = USE_DIRECT_SERVICES

Respond with: DECISION: [YOUR_CHOICE]
"""
    
    for model in models_to_test:
        try:
            logger.info(f"🤖 Testing {model}...")
            llm = LLMEngine(ollama_host="http://localhost:11434", default_model=model)
            await llm.initialize()
            
            response = await llm.chat(
                message=decision_prompt,
                system_prompt="You are an AI Brain making decisions about service usage. Be direct and clear."
            )
            
            if isinstance(response, dict) and "response" in response:
                decision_text = response["response"]
            else:
                decision_text = str(response)
                
            logger.info(f"   Decision: {decision_text[:100]}...")
            
            # Check if it chose the right option
            if "USE_DIRECT_SERVICES" in decision_text:
                logger.info(f"   ✅ {model}: Correctly chose USE_DIRECT_SERVICES")
            else:
                logger.info(f"   ❌ {model}: Did not choose USE_DIRECT_SERVICES")
                
        except Exception as e:
            logger.error(f"   ❌ {model}: Failed with error: {e}")

async def main():
    """Main test function"""
    
    logger.info("🔥 HYBRID DECISION SYSTEM TEST")
    logger.info("=" * 50)
    
    # Test 1: Decision model comparison
    await test_decision_models()
    
    logger.info("\n" + "=" * 50)
    
    # Test 2: Full hybrid system test
    success = await test_hybrid_decision_system()
    
    logger.info("\n" + "=" * 50)
    
    if success:
        logger.info("🎉 HYBRID DECISION SYSTEM: SUCCESS!")
    else:
        logger.info("💥 HYBRID DECISION SYSTEM: FAILED!")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)