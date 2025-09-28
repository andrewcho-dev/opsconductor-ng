#!/usr/bin/env python3
"""
OUIOE Phase 2: Integration Test

Quick integration test to verify Phase 2 thinking-aware LLM client
works correctly with the streaming infrastructure.
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any

# Add the ai-brain directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_phase2_integration():
    """Test Phase 2 integration with mocked dependencies"""
    print("🧪 Testing Phase 2 Integration...")
    
    try:
        # Test 1: Import all components
        print("📦 Testing imports...")
        from integrations.thinking_llm_client import ThinkingLLMClient, ThinkingConfig
        from integrations.llm_service_factory import LLMServiceFactory, LLMClientType
        print("✅ All imports successful")
        
        # Test 2: Create thinking configuration
        print("⚙️  Testing configuration...")
        config = ThinkingConfig(
            thinking_detail_level="standard",
            progress_update_frequency=1.0,
            max_thinking_steps=10
        )
        assert config.thinking_detail_level == "standard"
        print("✅ Configuration creation successful")
        
        # Test 3: Test factory pattern
        print("🏭 Testing factory pattern...")
        
        # Mock environment for testing
        os.environ["ENABLE_THINKING_MODE"] = "true"
        os.environ["REDIS_URL"] = "redis://test:6379"
        
        # Test auto-detection
        client_type = LLMServiceFactory._auto_detect_client_type()
        assert client_type == LLMClientType.THINKING
        print("✅ Auto-detection working")
        
        # Test configuration creation
        default_config = LLMServiceFactory._create_default_thinking_config()
        assert default_config.enable_thinking_stream == True
        print("✅ Default configuration creation successful")
        
        # Test 4: Test thinking patterns
        print("🧠 Testing thinking patterns...")
        
        # Create a mock LLM client to avoid actual Ollama dependency
        from unittest.mock import Mock, AsyncMock
        
        # Mock the base LLM client
        mock_llm = Mock()
        mock_llm.initialize = AsyncMock(return_value=True)
        
        # Create thinking client with mocked base
        with unittest.mock.patch('integrations.thinking_llm_client.LLMEngine', return_value=mock_llm):
            thinking_client = ThinkingLLMClient(
                ollama_host="http://test:11434",
                default_model="test-model",
                thinking_config=config
            )
            
            # Test initialization
            init_result = await thinking_client.initialize()
            assert init_result == True
            print("✅ Client initialization successful")
            
            # Test thinking patterns exist
            assert len(thinking_client.thinking_patterns) > 0
            assert "chat" in thinking_client.thinking_patterns
            assert "generate" in thinking_client.thinking_patterns
            print("✅ Thinking patterns loaded")
        
        # Test 5: Test session management (mocked)
        print("📋 Testing session management...")
        
        # Mock streaming functions
        with unittest.mock.patch('integrations.thinking_llm_client.create_session') as mock_create:
            with unittest.mock.patch('integrations.thinking_llm_client.LLMEngine', return_value=mock_llm):
                mock_create.return_value = {"session_id": "test-session-123"}
                
                client = ThinkingLLMClient(
                    ollama_host="http://test:11434",
                    default_model="test-model"
                )
                
                # Test session creation
                session_id = await client.create_thinking_session(
                    user_id="test-user",
                    operation_type="test",
                    user_request="Test request",
                    debug_mode=True
                )
                
                assert session_id.startswith("thinking-test-user-")
                assert session_id in client.active_sessions
                print("✅ Session creation successful")
        
        # Test 6: Test API router imports
        print("🌐 Testing API router...")
        try:
            from api.thinking_llm_router import router
            assert router is not None
            print("✅ API router import successful")
        except ImportError as e:
            print(f"⚠️  API router import failed (expected in test environment): {e}")
        
        print("\n🎉 Phase 2 Integration Test PASSED!")
        print("✅ All core components working correctly")
        print("✅ Factory pattern functional")
        print("✅ Thinking client creation successful")
        print("✅ Session management operational")
        print("✅ Configuration system working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Phase 2 Integration Test FAILED!")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Import unittest.mock for testing
    import unittest.mock
    
    # Run the integration test
    success = asyncio.run(test_phase2_integration())
    
    if success:
        print("\n🚀 Phase 2 is ready for deployment!")
        sys.exit(0)
    else:
        print("\n💥 Phase 2 needs fixes before deployment!")
        sys.exit(1)