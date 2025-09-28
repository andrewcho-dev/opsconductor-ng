#!/usr/bin/env python3
"""
OUIOE Phase 7: Conversational Intelligence - Fixed Test Suite

Test suite that properly imports Phase 7 components using absolute imports.
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

# Add the ai-brain directory to Python path
import os
ai_brain_path = '/home/opsconductor/opsconductor-ng/ai-brain'
if ai_brain_path not in sys.path:
    sys.path.insert(0, ai_brain_path)

try:
    # Import Phase 7 components using direct imports
    from conversation.conversation_models import (
        ConversationMessage, ConversationContext, UserPreference, 
        ClarificationRequest, ConversationInsight, MessageRole,
        ContextDimension, PreferenceType, ClarificationType, InsightType
    )
    from conversation.conversation_memory_engine import ConversationMemoryEngine
    from conversation.context_awareness_system import ContextAwarenessSystem
    from conversation.user_preference_learning import UserPreferenceLearning
    from conversation.clarification_intelligence import ClarificationIntelligence
    from conversation.conversation_analytics import ConversationAnalytics
    
    IMPORTS_SUCCESSFUL = True
    print("✅ All Phase 7 imports successful!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print(f"❌ Traceback: {traceback.format_exc()}")
    IMPORTS_SUCCESSFUL = False


class SimpleTestRunner:
    """Simple test runner for Phase 7 components."""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        self.total_tests += 1
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                asyncio.run(test_func())
            else:
                test_func()
            
            self.passed_tests += 1
            self.test_results.append({'name': test_name, 'status': 'PASSED'})
            print(f"  ✅ {test_name}")
            
        except Exception as e:
            self.failed_tests += 1
            self.test_results.append({
                'name': test_name, 
                'status': 'FAILED', 
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            print(f"  ❌ {test_name}: {str(e)}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("🎯 PHASE 7 TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        
        if self.total_tests > 0:
            success_rate = (self.passed_tests / self.total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if result['status'] == 'FAILED':
                    print(f"  • {result['name']}: {result['error']}")


def test_conversation_models():
    """Test conversation data models."""
    # Test ConversationMessage
    message = ConversationMessage(
        conversation_id="test_conv_1",
        role=MessageRole.USER,
        content="Hello, I need help with deployment",
        topics=["deployment", "help"],
        entities=["deployment"],
        sentiment_score=0.2
    )
    
    assert message.conversation_id == "test_conv_1"
    assert message.role == MessageRole.USER
    assert "deployment" in message.topics
    assert message.message_id is not None
    
    # Test ConversationContext
    context = ConversationContext(
        conversation_id="test_conv_1",
        user_id="user_123",
        session_id="session_456"
    )
    
    assert context.conversation_id == "test_conv_1"
    assert context.user_id == "user_123"
    assert context.context_version == 1
    
    # Test UserPreference
    preference = UserPreference(
        user_id="user_123",
        preference_type=PreferenceType.COMMUNICATION_STYLE,
        preference_value="brief",
        confidence_score=0.8
    )
    
    assert preference.user_id == "user_123"
    assert preference.preference_type == PreferenceType.COMMUNICATION_STYLE
    assert preference.confidence_score == 0.8


async def test_conversation_memory_engine():
    """Test conversation memory engine."""
    # Create mocked dependencies
    llm_client = Mock()
    vector_client = Mock()
    redis_stream = Mock()
    
    # Mock async methods
    llm_client.generate_response = AsyncMock(return_value="Test response")
    vector_client.store_embedding = AsyncMock(return_value=True)
    vector_client.similarity_search = AsyncMock(return_value=[])
    vector_client.generate_embedding = AsyncMock(return_value=[0.1] * 384)
    redis_stream.stream_thinking_step = AsyncMock()
    
    # Create memory engine
    memory_engine = ConversationMemoryEngine(
        llm_client=llm_client,
        vector_client=vector_client,
        redis_stream=redis_stream
    )
    
    # Test message storage
    message = ConversationMessage(
        conversation_id="test_conv_1",
        role=MessageRole.USER,
        content="Test message content",
        topics=["test"]
    )
    
    result = await memory_engine.store_message(message)
    assert result is True
    assert "test_conv_1" in memory_engine.active_conversations
    
    # Test conversation history retrieval
    history = await memory_engine.retrieve_conversation_history("test_conv_1")
    assert len(history) == 1
    assert history[0].content == "Test message content"
    
    # Test memory statistics
    stats = await memory_engine.get_memory_statistics()
    assert isinstance(stats, dict)
    assert 'total_messages' in stats
    assert stats['total_messages'] == 1


def main():
    """Main test execution."""
    if not IMPORTS_SUCCESSFUL:
        print("❌ Cannot run tests due to import failures")
        return
    
    print("🚀 Starting OUIOE Phase 7: Conversational Intelligence Tests")
    print("=" * 80)
    
    runner = SimpleTestRunner()
    
    # Run tests
    print("\n📋 Testing Phase 7 Components:")
    runner.run_test("Conversation Models", test_conversation_models)
    runner.run_test("Conversation Memory Engine", test_conversation_memory_engine)
    
    # Print results
    runner.print_summary()
    
    if runner.failed_tests == 0:
        print("\n🎉 All Phase 7 tests passed! Conversational Intelligence is ready!")
    else:
        print(f"\n⚠️  {runner.failed_tests} tests failed. Please review the issues above.")


if __name__ == "__main__":
    main()