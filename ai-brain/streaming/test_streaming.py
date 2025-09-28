"""
Basic test infrastructure for streaming components
"""

import asyncio
import json
import structlog
from datetime import datetime
from typing import Dict, Any

from .stream_manager import CentralStreamManager
from .thinking_data_models import ThinkingType, ProgressType

logger = structlog.get_logger()


class StreamingTester:
    """Test harness for streaming infrastructure"""
    
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.stream_manager = CentralStreamManager(redis_url)
        self.test_session_id = f"test-{datetime.now().timestamp()}"
        
    async def initialize(self) -> bool:
        """Initialize the test environment"""
        try:
            success = await self.stream_manager.initialize()
            if success:
                logger.info("✅ Streaming tester initialized")
            return success
            
        except Exception as e:
            logger.error("❌ Failed to initialize streaming tester", error=str(e))
            return False
    
    async def test_basic_streaming(self) -> bool:
        """Test basic streaming functionality"""
        try:
            logger.info("🧪 Testing basic streaming functionality...")
            
            # Create test session
            session = await self.stream_manager.create_thinking_session(
                session_id=self.test_session_id,
                user_id="test-user",
                debug_mode=True,
                user_request="Test streaming functionality"
            )
            
            if not session:
                logger.error("Failed to create test session")
                return False
            
            logger.info("✅ Test session created", session_id=self.test_session_id)
            
            # Test thinking steps
            thinking_tests = [
                {
                    "type": ThinkingType.INITIALIZATION,
                    "content": "Starting test sequence...",
                    "reasoning": ["Initialize test environment", "Prepare test data"],
                    "confidence": 0.9
                },
                {
                    "type": ThinkingType.ANALYSIS,
                    "content": "Analyzing test requirements...",
                    "reasoning": ["Review test objectives", "Identify test scenarios"],
                    "confidence": 0.8
                },
                {
                    "type": ThinkingType.DECISION,
                    "content": "Deciding on test approach...",
                    "reasoning": ["Evaluate options", "Select best approach"],
                    "confidence": 0.85,
                    "alternatives": ["Approach A", "Approach B"],
                    "decision_factors": ["Speed", "Reliability", "Coverage"]
                }
            ]
            
            for i, test in enumerate(thinking_tests):
                success = await self.stream_manager.stream_thinking(
                    session_id=self.test_session_id,
                    thinking_type=test["type"],
                    content=test["content"],
                    reasoning_chain=test["reasoning"],
                    confidence=test["confidence"],
                    alternatives=test.get("alternatives"),
                    decision_factors=test.get("decision_factors")
                )
                
                if success:
                    logger.info(f"✅ Thinking step {i+1} streamed successfully")
                else:
                    logger.error(f"❌ Failed to stream thinking step {i+1}")
                    return False
                
                await asyncio.sleep(0.1)  # Small delay between steps
            
            # Test progress updates
            progress_tests = [
                {
                    "type": ProgressType.PROGRESS,
                    "message": "Starting test execution...",
                    "progress": 10.0,
                    "current_step": "Initialization"
                },
                {
                    "type": ProgressType.THINKING_ALOUD,
                    "message": "I'm analyzing the test data and it looks promising...",
                    "progress": 30.0,
                    "current_step": "Analysis"
                },
                {
                    "type": ProgressType.INTERMEDIATE_RESULT,
                    "message": "Found interesting pattern in the data",
                    "progress": 60.0,
                    "current_step": "Processing",
                    "findings": [{"pattern": "test_pattern", "confidence": 0.8}]
                },
                {
                    "type": ProgressType.COMPLETION,
                    "message": "Test completed successfully!",
                    "progress": 100.0,
                    "current_step": "Complete"
                }
            ]
            
            for i, test in enumerate(progress_tests):
                success = await self.stream_manager.stream_progress(
                    session_id=self.test_session_id,
                    progress_type=test["type"],
                    message=test["message"],
                    progress_percentage=test.get("progress"),
                    current_step=test.get("current_step"),
                    intermediate_findings=test.get("findings")
                )
                
                if success:
                    logger.info(f"✅ Progress update {i+1} streamed successfully")
                else:
                    logger.error(f"❌ Failed to stream progress update {i+1}")
                    return False
                
                await asyncio.sleep(0.2)  # Small delay between updates
            
            # Get session stats
            stats = await self.stream_manager.get_session_stats(self.test_session_id)
            if stats:
                logger.info("📊 Session stats", 
                           thinking_steps=stats.total_thinking_steps,
                           progress_updates=stats.total_progress_updates,
                           duration=stats.session_duration)
            
            # Close session
            await self.stream_manager.close_session(self.test_session_id)
            logger.info("✅ Test session closed")
            
            logger.info("🎉 Basic streaming test completed successfully!")
            return True
            
        except Exception as e:
            logger.error("❌ Basic streaming test failed", error=str(e))
            return False
    
    async def test_concurrent_sessions(self, num_sessions: int = 3) -> bool:
        """Test concurrent streaming sessions"""
        try:
            logger.info(f"🧪 Testing {num_sessions} concurrent sessions...")
            
            # Create multiple sessions
            sessions = []
            for i in range(num_sessions):
                session_id = f"concurrent-test-{i}-{datetime.now().timestamp()}"
                session = await self.stream_manager.create_thinking_session(
                    session_id=session_id,
                    user_id=f"test-user-{i}",
                    debug_mode=True,
                    user_request=f"Concurrent test session {i}"
                )
                sessions.append(session_id)
            
            logger.info(f"✅ Created {len(sessions)} concurrent sessions")
            
            # Stream to all sessions concurrently
            async def stream_to_session(session_id: str, session_num: int):
                for step in range(3):
                    await self.stream_manager.stream_thinking(
                        session_id=session_id,
                        thinking_type=ThinkingType.ANALYSIS,
                        content=f"Session {session_num} - Step {step + 1}",
                        reasoning_chain=[f"Reasoning for session {session_num}, step {step + 1}"],
                        confidence=0.8
                    )
                    
                    await self.stream_manager.stream_progress(
                        session_id=session_id,
                        progress_type=ProgressType.PROGRESS,
                        message=f"Session {session_num} progress: {(step + 1) * 33}%",
                        progress_percentage=(step + 1) * 33.0
                    )
                    
                    await asyncio.sleep(0.1)
            
            # Run all sessions concurrently
            tasks = [
                stream_to_session(session_id, i) 
                for i, session_id in enumerate(sessions)
            ]
            
            await asyncio.gather(*tasks)
            
            # Close all sessions
            for session_id in sessions:
                await self.stream_manager.close_session(session_id)
            
            logger.info("🎉 Concurrent sessions test completed successfully!")
            return True
            
        except Exception as e:
            logger.error("❌ Concurrent sessions test failed", error=str(e))
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all streaming tests"""
        try:
            logger.info("🚀 Starting comprehensive streaming tests...")
            
            # Initialize
            if not await self.initialize():
                return False
            
            # Run tests
            tests = [
                ("Basic Streaming", self.test_basic_streaming()),
                ("Concurrent Sessions", self.test_concurrent_sessions(3))
            ]
            
            results = []
            for test_name, test_coro in tests:
                logger.info(f"🧪 Running {test_name} test...")
                result = await test_coro
                results.append((test_name, result))
                
                if result:
                    logger.info(f"✅ {test_name} test PASSED")
                else:
                    logger.error(f"❌ {test_name} test FAILED")
            
            # Summary
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            logger.info(f"📊 Test Summary: {passed}/{total} tests passed")
            
            if passed == total:
                logger.info("🎉 ALL TESTS PASSED!")
                return True
            else:
                logger.error("❌ Some tests failed")
                return False
            
        except Exception as e:
            logger.error("❌ Test suite failed", error=str(e))
            return False
        
        finally:
            # Cleanup
            await self.stream_manager.shutdown()


async def run_streaming_tests():
    """Run streaming infrastructure tests"""
    tester = StreamingTester()
    return await tester.run_all_tests()


if __name__ == "__main__":
    # Run tests if executed directly
    asyncio.run(run_streaming_tests())