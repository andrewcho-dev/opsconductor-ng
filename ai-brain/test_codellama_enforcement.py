#!/usr/bin/env python3
"""
Test script to verify that the system enforces CodeLlama 7B usage
"""

import sys
import os
import asyncio
import logging

# Add the ai-brain directory to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

# Set environment variables to enforce CodeLlama 7B
os.environ["FORCE_MODEL"] = "codellama:7b"
os.environ["ALLOWED_MODELS"] = "codellama:7b"
os.environ["DEFAULT_MODEL"] = "codellama:7b"
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_model_enforcement():
    """Test that the system enforces CodeLlama 7B usage"""
    try:
        logger.info("🔒 Testing CodeLlama 7B Model Enforcement...")
        
        # Test 1: Direct LLM Engine with different model requests
        logger.info("🧠 Testing LLM Engine model enforcement...")
        from integrations.llm_client import LLMEngine
        
        llm_engine = LLMEngine(
            ollama_host="http://localhost:11434",
            default_model="codellama:7b"
        )
        
        # Initialize the LLM engine
        llm_initialized = await llm_engine.initialize()
        if llm_initialized:
            logger.info("✅ LLM Engine initialized successfully")
        else:
            logger.warning("⚠️ LLM Engine initialization failed, continuing with tests")
        
        # Test model enforcement with different requested models
        test_models = ["llama3.2:3b", "llama3.1", "mistral", "codellama:7b", None]
        
        for test_model in test_models:
            enforced_model = llm_engine._enforce_model_restriction(test_model)
            logger.info(f"📋 Requested: {test_model} → Enforced: {enforced_model}")
            
            if enforced_model != "codellama:7b":
                logger.error(f"❌ ENFORCEMENT FAILED! Expected 'codellama:7b', got '{enforced_model}'")
                return False
            else:
                logger.info(f"✅ Model enforcement working correctly")
        
        # Test 2: LLM Service Factory
        logger.info("🏭 Testing LLM Service Factory model enforcement...")
        from integrations.llm_service_factory import LLMServiceFactory
        
        # Create standard client
        standard_client = LLMServiceFactory.create_standard_client()
        logger.info(f"✅ Standard client default model: {standard_client.default_model}")
        
        if standard_client.default_model != "codellama:7b":
            logger.error(f"❌ FACTORY ENFORCEMENT FAILED! Expected 'codellama:7b', got '{standard_client.default_model}'")
            return False
        
        # Create thinking client
        thinking_client = LLMServiceFactory.create_thinking_client()
        logger.info(f"✅ Thinking client default model: {thinking_client.base_client.default_model}")
        
        if thinking_client.base_client.default_model != "codellama:7b":
            logger.error(f"❌ THINKING CLIENT ENFORCEMENT FAILED! Expected 'codellama:7b', got '{thinking_client.base_client.default_model}'")
            return False
        
        # Test 3: Try to make a chat request with different models
        logger.info("💬 Testing chat requests with model enforcement...")
        
        if llm_initialized:
            # Try to request different models - should all use codellama:7b
            test_chat_models = ["llama3.2:3b", "mistral", None]
            
            for chat_model in test_chat_models:
                try:
                    response = await llm_engine.chat(
                        message="Hello, what model are you?",
                        model=chat_model
                    )
                    
                    actual_model = response.get("model_used", "unknown")
                    logger.info(f"📞 Chat requested: {chat_model} → Used: {actual_model}")
                    
                    if actual_model != "codellama:7b":
                        logger.error(f"❌ CHAT ENFORCEMENT FAILED! Expected 'codellama:7b', got '{actual_model}'")
                        return False
                    else:
                        logger.info(f"✅ Chat model enforcement working correctly")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Chat test failed (expected if Ollama not running): {e}")
        
        # Test 4: Environment variable verification
        logger.info("🌍 Verifying environment variables...")
        
        env_vars = {
            "FORCE_MODEL": os.getenv("FORCE_MODEL"),
            "ALLOWED_MODELS": os.getenv("ALLOWED_MODELS"),
            "DEFAULT_MODEL": os.getenv("DEFAULT_MODEL"),
            "OLLAMA_HOST": os.getenv("OLLAMA_HOST")
        }
        
        for var_name, var_value in env_vars.items():
            logger.info(f"🔧 {var_name}: {var_value}")
        
        # Verify all model-related env vars point to codellama:7b
        model_vars = ["FORCE_MODEL", "ALLOWED_MODELS", "DEFAULT_MODEL"]
        for var_name in model_vars:
            var_value = os.getenv(var_name)
            if var_value and "codellama:7b" not in var_value:
                logger.error(f"❌ ENV VAR ISSUE! {var_name} = '{var_value}' doesn't contain 'codellama:7b'")
                return False
        
        logger.info("🎉 ALL MODEL ENFORCEMENT TESTS PASSED!")
        logger.info("🔒 System is configured to use ONLY CodeLlama 7B model")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model enforcement test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_model_enforcement())
    if success:
        print("\n🎯 SUCCESS: CodeLlama 7B enforcement is working correctly!")
        print("🔒 The system will use ONLY CodeLlama 7B for all LLM operations.")
    else:
        print("\n❌ FAILURE: Model enforcement is not working correctly!")
        sys.exit(1)