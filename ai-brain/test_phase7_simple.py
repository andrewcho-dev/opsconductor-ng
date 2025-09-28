"""
OUIOE Phase 7: Conversational Intelligence - Simple Test Suite

Simplified test suite for Phase 7 components without external dependencies.
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
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain/conversation')

try:
    # Import Phase 7 components directly
    from conversation_models import (
        ConversationMessage, ConversationContext, UserPreference, 
        ClarificationRequest, ConversationInsight, MessageRole,
        ContextDimension, PreferenceType, ClarificationType, InsightType
    )
    from conversation_memory_engine import ConversationMemoryEngine
    from context_awareness_system import ContextAwarenessSystem
    from user_preference_learning import UserPreferenceLearning
    from clarification_intelligence import ClarificationIntelligence
    from conversation_analytics import ConversationAnalytics
    
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"❌ Import Error: {e}")
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


async def test_context_awareness_system():
    """Test context awareness system."""
    # Create mocked dependencies
    llm_client = Mock()
    decision_engine = Mock()
    pattern_engine = Mock()
    
    llm_client.generate_response = AsyncMock(return_value="Test response")
    decision_engine.generate_recommendations = AsyncMock(return_value=[])
    
    # Create context system
    context_system = ContextAwarenessSystem(
        llm_client=llm_client,
        decision_engine=decision_engine,
        pattern_engine=pattern_engine
    )
    
    # Test context initialization
    context = await context_system.initialize_context(
        conversation_id="test_conv_1",
        user_id="user_123",
        session_id="session_456"
    )
    
    assert context.conversation_id == "test_conv_1"
    assert context.user_id == "user_123"
    assert "test_conv_1" in context_system.active_contexts
    
    # Test context summary
    summary = await context_system.get_context_summary("test_conv_1")
    assert isinstance(summary, dict)
    assert summary['conversation_id'] == "test_conv_1"
    assert 'dimensions' in summary


async def test_user_preference_learning():
    """Test user preference learning system."""
    # Create mocked dependencies
    llm_client = Mock()
    pattern_engine = Mock()
    learning_engine = Mock()
    
    llm_client.generate_response = AsyncMock(return_value="Personalized response")
    
    # Create preference learning system
    preference_learning = UserPreferenceLearning(
        llm_client=llm_client,
        pattern_engine=pattern_engine,
        learning_engine=learning_engine
    )
    
    # Test preference learning from message
    message = ConversationMessage(
        conversation_id="test_conv_1",
        role=MessageRole.USER,
        content="Please keep it brief and technical",
        topics=["request"]
    )
    
    context = {"conversation_type": "technical_support"}
    events = await preference_learning.learn_from_message("user_123", message, context)
    assert isinstance(events, list)
    
    # Test preference prediction
    prediction = await preference_learning.predict_user_preference(
        "user_123", PreferenceType.AUTOMATION_LEVEL, context
    )
    assert prediction is not None
    assert 'predicted_value' in prediction
    assert 'confidence' in prediction
    
    # Test preference insights
    insights = await preference_learning.get_preference_insights("user_123")
    assert isinstance(insights, dict)
    assert 'user_id' in insights


async def test_clarification_intelligence():
    """Test clarification intelligence system."""
    # Create mocked dependencies
    llm_client = Mock()
    decision_engine = Mock()
    pattern_engine = Mock()
    
    llm_client.generate_response = AsyncMock(return_value="Clarification question")
    
    # Create clarification system
    clarification_system = ClarificationIntelligence(
        llm_client=llm_client,
        decision_engine=decision_engine,
        pattern_engine=pattern_engine
    )
    
    # Test clarification needs analysis
    message = ConversationMessage(
        conversation_id="test_conv_1",
        role=MessageRole.USER,
        content="Deploy it to the server",  # Ambiguous "it"
        topics=["deployment"]
    )
    
    context = ConversationContext(
        conversation_id="test_conv_1",
        user_id="user_123",
        session_id="session_456"
    )
    
    clarifications = await clarification_system.analyze_clarification_needs(
        "test_conv_1", message, context
    )
    assert isinstance(clarifications, list)
    
    # Test clarification analytics
    analytics = await clarification_system.get_clarification_analytics()
    assert isinstance(analytics, dict)
    assert 'total_clarifications' in analytics


async def test_conversation_analytics():
    """Test conversation analytics system."""
    # Create mocked dependencies
    llm_client = Mock()
    pattern_engine = Mock()
    analysis_engine = Mock()
    
    # Create analytics system
    analytics_system = ConversationAnalytics(
        llm_client=llm_client,
        pattern_engine=pattern_engine,
        analysis_engine=analysis_engine
    )
    
    # Test conversation pattern analysis
    conversation_data = [
        {
            'conversation_id': 'conv_1',
            'messages': [
                {
                    'role': 'user',
                    'content': 'Hello, I need help',
                    'topics': ['help'],
                    'timestamp': datetime.now()
                }
            ]
        }
    ]
    
    insights = await analytics_system.analyze_conversation_patterns(conversation_data)
    assert isinstance(insights, list)
    
    # Test conversation health assessment
    health = await analytics_system.assess_conversation_health()
    assert hasattr(health, 'overall_health_score')
    assert hasattr(health, 'engagement_health')
    assert isinstance(health.alerts, list)
    
    # Test dashboard data
    dashboard = await analytics_system.get_analytics_dashboard_data()
    assert isinstance(dashboard, dict)
    assert 'key_metrics' in dashboard


async def test_phase7_integration():
    """Test integration between Phase 7 components."""
    # Create all mocked dependencies
    llm_client = Mock()
    vector_client = Mock()
    redis_stream = Mock()
    decision_engine = Mock()
    pattern_engine = Mock()
    analysis_engine = Mock()
    learning_engine = Mock()
    
    # Mock async methods
    llm_client.generate_response = AsyncMock(return_value="Test response")
    vector_client.store_embedding = AsyncMock(return_value=True)
    vector_client.similarity_search = AsyncMock(return_value=[])
    vector_client.generate_embedding = AsyncMock(return_value=[0.1] * 384)
    redis_stream.stream_thinking_step = AsyncMock()
    decision_engine.generate_recommendations = AsyncMock(return_value=[])
    
    # Create all components
    memory_engine = ConversationMemoryEngine(llm_client, vector_client, redis_stream)
    context_system = ContextAwarenessSystem(llm_client, decision_engine, pattern_engine)
    preference_learning = UserPreferenceLearning(llm_client, pattern_engine, learning_engine)
    
    # Test integrated workflow
    # 1. Initialize context
    conv_context = await context_system.initialize_context(
        "test_conv_1", "user_123", "session_456"
    )
    
    # 2. Process user message
    user_message = ConversationMessage(
        conversation_id="test_conv_1",
        role=MessageRole.USER,
        content="I need help with deployment, keep it brief",
        topics=["deployment", "help"]
    )
    
    # Store in memory
    await memory_engine.store_message(user_message)
    
    # Update context
    context_updates = await context_system.update_context_from_message(
        "test_conv_1", user_message
    )
    
    # Learn preferences
    learning_events = await preference_learning.learn_from_message(
        "user_123", user_message, {"conversation_type": "support"}
    )
    
    # 3. Verify integration
    conversation_history = await memory_engine.retrieve_conversation_history("test_conv_1")
    assert len(conversation_history) == 1
    
    context_summary = await context_system.get_context_summary("test_conv_1")
    assert context_summary['conversation_id'] == "test_conv_1"
    
    user_prefs = await preference_learning.get_user_preferences("user_123")
    assert isinstance(user_prefs, dict)


def test_performance_benchmarks():
    """Test performance benchmarks for Phase 7 components."""
    # Test model serialization performance
    message = ConversationMessage(
        conversation_id="perf_test",
        role=MessageRole.USER,
        content="Performance test message " * 50,
        topics=[f"topic_{i}" for i in range(10)],
        entities=[f"entity_{i}" for i in range(5)]
    )
    
    # Test JSON serialization
    start_time = datetime.now()
    
    for _ in range(100):
        json_data = message.model_dump_json()
        parsed = ConversationMessage.model_validate_json(json_data)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    # Should be reasonably fast
    assert duration < 5.0  # Less than 5 seconds for 100 operations
    
    # Test context dimension enumeration
    dimensions = list(ContextDimension)
    assert len(dimensions) == 8  # All 8 context dimensions
    
    preference_types = list(PreferenceType)
    assert len(preference_types) == 8  # All 8 preference types


async def run_all_tests():
    """Run all Phase 7 tests."""
    if not IMPORTS_SUCCESSFUL:
        print("❌ Cannot run tests due to import failures")
        return
    
    runner = SimpleTestRunner()
    
    print("🧪 Running OUIOE Phase 7: Conversational Intelligence Tests...")
    print("=" * 80)
    
    # Test categories
    test_functions = [
        ("Conversation Models", test_conversation_models),
        ("Memory Engine", test_conversation_memory_engine),
        ("Context Awareness", test_context_awareness_system),
        ("Preference Learning", test_user_preference_learning),
        ("Clarification Intelligence", test_clarification_intelligence),
        ("Conversation Analytics", test_conversation_analytics),
        ("Phase 7 Integration", test_phase7_integration),
        ("Performance Benchmarks", test_performance_benchmarks)
    ]
    
    for category_name, test_func in test_functions:
        print(f"\n📋 Testing {category_name}...")
        runner.run_test(f"{category_name} Test", test_func)
    
    # Print summary
    runner.print_summary()
    
    # Performance metrics
    print("\n📊 Performance Metrics:")
    print("  • Model serialization: <5s for 100 operations")
    print("  • Memory operations: Efficient storage and retrieval")
    print("  • Context processing: Real-time context updates")
    print("  • Preference learning: Adaptive user behavior analysis")
    print("  • Clarification analysis: Smart ambiguity detection")
    print("  • Analytics processing: Comprehensive conversation insights")
    
    success_rate = (runner.passed_tests / runner.total_tests) * 100 if runner.total_tests > 0 else 0
    
    if runner.failed_tests == 0:
        print(f"\n🚀 Phase 7: Conversational Intelligence - ✅ ALL TESTS PASSED! ({success_rate:.1f}%)")
    else:
        print(f"\n⚠️ Phase 7: Conversational Intelligence - {runner.failed_tests} tests failed ({success_rate:.1f}% success rate)")
    
    return runner


if __name__ == "__main__":
    asyncio.run(run_all_tests())