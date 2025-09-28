"""
OUIOE Phase 2: Thinking-Aware LLM Client Tests

Comprehensive test suite for the thinking-aware LLM client and related components.
Tests both functionality and integration with the streaming infrastructure.

Key Test Areas:
- Thinking LLM client functionality
- Session management
- Streaming integration
- API endpoints
- Performance and reliability
- Error handling and recovery
"""

import asyncio
import pytest
import time
import uuid
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

# Import components to test
from integrations.thinking_llm_client import ThinkingLLMClient, ThinkingConfig
from integrations.llm_service_factory import LLMServiceFactory, LLMClientType
from integrations.llm_client import LLMEngine

class ThinkingLLMTester:
    """Comprehensive test harness for thinking-aware LLM functionality"""
    
    def __init__(self):
        self.test_results = []
        self.mock_ollama_host = "http://test-ollama:11434"
        self.mock_model = "test-model:7b"
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all thinking LLM tests"""
        print("🧪 Starting Thinking LLM Test Suite...")
        
        test_methods = [
            self.test_thinking_config,
            self.test_llm_service_factory,
            self.test_thinking_client_creation,
            self.test_session_management,
            self.test_thinking_operations,
            self.test_streaming_integration,
            self.test_error_handling,
            self.test_performance_characteristics,
            self.test_backward_compatibility
        ]
        
        for test_method in test_methods:
            try:
                result = await test_method()
                self.test_results.append(result)
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"{status} {result['test_name']}")
                if not result["success"]:
                    print(f"   Error: {result.get('error', 'Unknown error')}")
            except Exception as e:
                self.test_results.append({
                    "test_name": test_method.__name__,
                    "success": False,
                    "error": str(e),
                    "duration": 0
                })
                print(f"❌ FAIL {test_method.__name__} - Exception: {str(e)}")
        
        return self._generate_test_summary()
    
    async def test_thinking_config(self) -> Dict[str, Any]:
        """Test thinking configuration functionality"""
        start_time = time.time()
        
        try:
            # Test default configuration
            default_config = ThinkingConfig()
            assert default_config.enable_thinking_stream == True
            assert default_config.enable_progress_stream == True
            assert default_config.thinking_detail_level == "detailed"
            assert default_config.auto_create_session == True
            
            # Test custom configuration
            custom_config = ThinkingConfig(
                enable_thinking_stream=False,
                thinking_detail_level="minimal",
                progress_update_frequency=1.0,
                max_thinking_steps=25
            )
            assert custom_config.enable_thinking_stream == False
            assert custom_config.thinking_detail_level == "minimal"
            assert custom_config.progress_update_frequency == 1.0
            assert custom_config.max_thinking_steps == 25
            
            return {
                "test_name": "test_thinking_config",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Configuration creation and validation successful"
            }
            
        except Exception as e:
            return {
                "test_name": "test_thinking_config",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_llm_service_factory(self) -> Dict[str, Any]:
        """Test LLM service factory functionality"""
        start_time = time.time()
        
        try:
            # Test factory creation with different client types
            with patch('integrations.thinking_llm_client.ThinkingLLMClient') as mock_thinking:
                with patch('integrations.llm_client.LLMEngine') as mock_standard:
                    
                    # Test standard client creation
                    standard_client = LLMServiceFactory.create_client(
                        client_type=LLMClientType.STANDARD,
                        ollama_host=self.mock_ollama_host,
                        default_model=self.mock_model
                    )
                    mock_standard.assert_called_once()
                    
                    # Test thinking client creation
                    thinking_client = LLMServiceFactory.create_client(
                        client_type=LLMClientType.THINKING,
                        ollama_host=self.mock_ollama_host,
                        default_model=self.mock_model
                    )
                    mock_thinking.assert_called_once()
                    
                    # Test auto-detection (should default to thinking in test environment)
                    with patch.dict('os.environ', {'ENVIRONMENT': 'development'}):
                        auto_client = LLMServiceFactory.create_client(
                            client_type=LLMClientType.AUTO,
                            ollama_host=self.mock_ollama_host,
                            default_model=self.mock_model
                        )
                        # Should create thinking client in development
                        assert mock_thinking.call_count == 2
            
            return {
                "test_name": "test_llm_service_factory",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Factory pattern working correctly"
            }
            
        except Exception as e:
            return {
                "test_name": "test_llm_service_factory",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_thinking_client_creation(self) -> Dict[str, Any]:
        """Test thinking client creation and initialization"""
        start_time = time.time()
        
        try:
            # Mock the base LLM client
            with patch('integrations.thinking_llm_client.LLMEngine') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm_instance.initialize = AsyncMock(return_value=True)
                mock_llm.return_value = mock_llm_instance
                
                # Create thinking client
                thinking_config = ThinkingConfig(thinking_detail_level="standard")
                client = ThinkingLLMClient(
                    ollama_host=self.mock_ollama_host,
                    default_model=self.mock_model,
                    thinking_config=thinking_config
                )
                
                # Test initialization
                init_result = await client.initialize()
                assert init_result == True
                mock_llm_instance.initialize.assert_called_once()
                
                # Test configuration
                assert client.thinking_config.thinking_detail_level == "standard"
                assert len(client.thinking_patterns) > 0
                assert "chat" in client.thinking_patterns
                assert "generate" in client.thinking_patterns
            
            return {
                "test_name": "test_thinking_client_creation",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Thinking client creation and initialization successful"
            }
            
        except Exception as e:
            return {
                "test_name": "test_thinking_client_creation",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_session_management(self) -> Dict[str, Any]:
        """Test thinking session management"""
        start_time = time.time()
        
        try:
            # Mock streaming functions
            with patch('integrations.thinking_llm_client.create_session') as mock_create:
                with patch('integrations.thinking_llm_client.close_session') as mock_close:
                    with patch('integrations.thinking_llm_client.get_session_stats') as mock_stats:
                        
                        # Setup mocks
                        test_session_id = "test-session-123"
                        mock_create.return_value = {"session_id": test_session_id}
                        mock_stats.return_value = {"messages": 5, "duration": 10.5}
                        mock_close.return_value = True
                        
                        # Create thinking client
                        with patch('integrations.thinking_llm_client.LLMEngine'):
                            client = ThinkingLLMClient(
                                ollama_host=self.mock_ollama_host,
                                default_model=self.mock_model
                            )
                            
                            # Test session creation
                            session_id = await client.create_thinking_session(
                                user_id="test-user",
                                operation_type="chat",
                                user_request="Test request",
                                debug_mode=True
                            )
                            
                            assert session_id.startswith("ouioe-test-user-")
                            assert session_id in client.active_sessions
                            
                            # Test session stats
                            stats = await client.get_thinking_session_stats(session_id)
                            assert "session_duration" in stats
                            assert stats["operation_type"] == "chat"
                            
                            # Test session closure
                            close_stats = await client.close_thinking_session(session_id)
                            assert session_id not in client.active_sessions
            
            return {
                "test_name": "test_session_management",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Session management working correctly"
            }
            
        except Exception as e:
            return {
                "test_name": "test_session_management",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_thinking_operations(self) -> Dict[str, Any]:
        """Test thinking-aware LLM operations"""
        start_time = time.time()
        
        try:
            # Mock all dependencies
            with patch('integrations.thinking_llm_client.LLMEngine') as mock_llm:
                with patch('integrations.thinking_llm_client.create_session') as mock_create:
                    with patch('integrations.thinking_llm_client.stream_thinking') as mock_stream_thinking:
                        with patch('integrations.thinking_llm_client.stream_progress') as mock_stream_progress:
                            with patch('integrations.thinking_llm_client.close_session') as mock_close:
                                
                                # Setup mocks
                                mock_llm_instance = Mock()
                                mock_llm_instance.chat = AsyncMock(return_value={
                                    "response": "Test response",
                                    "confidence": 0.8,
                                    "processing_time": 1.5
                                })
                                mock_llm.return_value = mock_llm_instance
                                mock_create.return_value = {"session_id": "test-session"}
                                
                                # Create client
                                client = ThinkingLLMClient(
                                    ollama_host=self.mock_ollama_host,
                                    default_model=self.mock_model
                                )
                                
                                # Test chat with thinking
                                result = await client.chat_with_thinking(
                                    message="Test message",
                                    user_id="test-user",
                                    debug_mode=True
                                )
                                
                                # Verify result
                                assert "response" in result
                                assert "session_id" in result
                                assert result["thinking_enabled"] == True
                                
                                # Verify streaming calls were made
                                assert mock_stream_thinking.called
                                assert mock_stream_progress.called
                                assert mock_close.called
            
            return {
                "test_name": "test_thinking_operations",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Thinking operations working correctly"
            }
            
        except Exception as e:
            return {
                "test_name": "test_thinking_operations",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_streaming_integration(self) -> Dict[str, Any]:
        """Test integration with streaming infrastructure"""
        start_time = time.time()
        
        try:
            # Mock streaming functions to verify they're called correctly
            with patch('integrations.thinking_llm_client.stream_thinking') as mock_stream_thinking:
                with patch('integrations.thinking_llm_client.stream_progress') as mock_stream_progress:
                    
                    # Create client with mocked base LLM
                    with patch('integrations.thinking_llm_client.LLMEngine'):
                        client = ThinkingLLMClient(
                            ollama_host=self.mock_ollama_host,
                            default_model=self.mock_model
                        )
                        
                        # Test streaming thinking step
                        await client._stream_thinking_step(
                            session_id="test-session",
                            thinking_type="analysis",
                            content="Analyzing request",
                            reasoning_chain=["Step 1", "Step 2"],
                            confidence=0.9
                        )
                        
                        # Verify streaming call
                        mock_stream_thinking.assert_called_once_with(
                            session_id="test-session",
                            thinking_type="analysis",
                            content="Analyzing request",
                            reasoning_chain=["Step 1", "Step 2"],
                            confidence=0.9,
                            metadata={}
                        )
                        
                        # Test streaming progress update
                        await client._stream_progress_update(
                            session_id="test-session",
                            progress_type="progress",
                            message="Processing...",
                            progress_percentage=50.0,
                            current_step="Step 2"
                        )
                        
                        # Verify progress call
                        mock_stream_progress.assert_called_once_with(
                            session_id="test-session",
                            progress_type="progress",
                            message="Processing...",
                            progress_percentage=50.0,
                            current_step="Step 2",
                            metadata={}
                        )
            
            return {
                "test_name": "test_streaming_integration",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Streaming integration working correctly"
            }
            
        except Exception as e:
            return {
                "test_name": "test_streaming_integration",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and recovery"""
        start_time = time.time()
        
        try:
            # Test with failing base LLM client
            with patch('integrations.thinking_llm_client.LLMEngine') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm_instance.chat = AsyncMock(side_effect=Exception("LLM Error"))
                mock_llm.return_value = mock_llm_instance
                
                with patch('integrations.thinking_llm_client.stream_thinking'):
                    with patch('integrations.thinking_llm_client.stream_progress'):
                        with patch('integrations.thinking_llm_client.create_session') as mock_create:
                            with patch('integrations.thinking_llm_client.close_session'):
                                
                                mock_create.return_value = {"session_id": "test-session"}
                                
                                client = ThinkingLLMClient(
                                    ollama_host=self.mock_ollama_host,
                                    default_model=self.mock_model
                                )
                                
                                # Test that error is properly propagated
                                try:
                                    await client.chat_with_thinking(
                                        message="Test message",
                                        user_id="test-user"
                                    )
                                    assert False, "Expected exception was not raised"
                                except Exception as e:
                                    assert "LLM Error" in str(e)
            
            # Test graceful degradation to legacy methods
            with patch('integrations.thinking_llm_client.LLMEngine') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm_instance.chat = AsyncMock(return_value={"response": "Legacy response"})
                mock_llm.return_value = mock_llm_instance
                
                client = ThinkingLLMClient(
                    ollama_host=self.mock_ollama_host,
                    default_model=self.mock_model
                )
                
                # Test legacy method still works
                result = await client.chat(message="Test message")
                assert result["response"] == "Legacy response"
            
            return {
                "test_name": "test_error_handling",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Error handling and recovery working correctly"
            }
            
        except Exception as e:
            return {
                "test_name": "test_error_handling",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_performance_characteristics(self) -> Dict[str, Any]:
        """Test performance characteristics"""
        start_time = time.time()
        
        try:
            # Test thinking patterns are reasonable
            with patch('integrations.thinking_llm_client.LLMEngine'):
                client = ThinkingLLMClient(
                    ollama_host=self.mock_ollama_host,
                    default_model=self.mock_model
                )
                
                # Check thinking patterns exist and are reasonable
                for operation_type, patterns in client.thinking_patterns.items():
                    assert len(patterns) >= 3, f"Too few thinking patterns for {operation_type}"
                    assert len(patterns) <= 10, f"Too many thinking patterns for {operation_type}"
                    
                    for pattern in patterns:
                        assert len(pattern) > 10, f"Thinking pattern too short: {pattern}"
                        assert len(pattern) < 200, f"Thinking pattern too long: {pattern}"
            
            # Test configuration limits are reasonable
            config = ThinkingConfig()
            assert config.progress_update_frequency >= 0.5, "Progress updates too frequent"
            assert config.progress_update_frequency <= 10.0, "Progress updates too infrequent"
            assert config.max_thinking_steps >= 5, "Too few thinking steps allowed"
            assert config.max_thinking_steps <= 100, "Too many thinking steps allowed"
            assert config.thinking_timeout >= 30.0, "Thinking timeout too short"
            assert config.thinking_timeout <= 600.0, "Thinking timeout too long"
            
            return {
                "test_name": "test_performance_characteristics",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Performance characteristics are reasonable"
            }
            
        except Exception as e:
            return {
                "test_name": "test_performance_characteristics",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_backward_compatibility(self) -> Dict[str, Any]:
        """Test backward compatibility with existing LLM client"""
        start_time = time.time()
        
        try:
            # Test that thinking client implements all base client methods
            with patch('integrations.thinking_llm_client.LLMEngine') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm_instance.chat = AsyncMock(return_value={"response": "Test"})
                mock_llm_instance.generate = AsyncMock(return_value={"generated_text": "Test"})
                mock_llm_instance.summarize = AsyncMock(return_value={"summary": "Test"})
                mock_llm_instance.analyze = AsyncMock(return_value={"result": "Test"})
                mock_llm_instance.get_available_models = AsyncMock(return_value=["model1", "model2"])
                mock_llm_instance.pull_model = AsyncMock(return_value=True)
                mock_llm_instance.get_gpu_status = Mock(return_value={"gpu_available": False})
                mock_llm.return_value = mock_llm_instance
                
                client = ThinkingLLMClient(
                    ollama_host=self.mock_ollama_host,
                    default_model=self.mock_model
                )
                
                # Test all legacy methods work
                chat_result = await client.chat(message="Test")
                assert "response" in chat_result
                
                generate_result = await client.generate(prompt="Test")
                assert "generated_text" in generate_result
                
                summarize_result = await client.summarize(text="Test text")
                assert "summary" in summarize_result
                
                analyze_result = await client.analyze(text="Test text")
                assert "result" in analyze_result
                
                models = await client.get_available_models()
                assert len(models) == 2
                
                pull_result = await client.pull_model("test-model")
                assert pull_result == True
                
                gpu_status = client.get_gpu_status()
                assert "gpu_available" in gpu_status
            
            return {
                "test_name": "test_backward_compatibility",
                "success": True,
                "duration": time.time() - start_time,
                "details": "Backward compatibility maintained"
            }
            
        except Exception as e:
            return {
                "test_name": "test_backward_compatibility",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(result["duration"] for result in self.test_results)
        
        summary = {
            "test_suite": "Thinking LLM Client Tests",
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "total_duration": total_duration,
            "average_test_duration": total_duration / total_tests if total_tests > 0 else 0,
            "results": self.test_results
        }
        
        return summary

# Main test execution
async def run_thinking_llm_tests():
    """Run the thinking LLM test suite"""
    tester = ThinkingLLMTester()
    results = await tester.run_all_tests()
    
    print("\n" + "="*60)
    print("🧪 THINKING LLM TEST SUITE RESULTS")
    print("="*60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Total Duration: {results['total_duration']:.2f}s")
    print(f"Average Test Duration: {results['average_test_duration']:.2f}s")
    
    if results['failed'] > 0:
        print("\n❌ FAILED TESTS:")
        for result in results['results']:
            if not result['success']:
                print(f"  - {result['test_name']}: {result.get('error', 'Unknown error')}")
    
    print("\n✅ Test suite completed!")
    return results

if __name__ == "__main__":
    # Run tests if executed directly
    asyncio.run(run_thinking_llm_tests())