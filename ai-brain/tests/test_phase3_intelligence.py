"""
OUIOE Phase 3 Integration Tests
Tests for intelligent progress communication, contextual messaging, and operation analysis.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Import Phase 3 intelligence systems
from intelligence import (
    ProgressIntelligenceEngine,
    OperationAnalyzer,
    SmartProgressMessaging,
    OperationType,
    ComplexityLevel,
    ProgressPhase,
    MessageContext,
    MessageTone,
    create_progress_intelligence_engine,
    create_operation_analyzer,
    create_smart_progress_messaging
)

# Import enhanced thinking client
from integrations.thinking_llm_client import ThinkingLLMClient, ThinkingConfig


class TestProgressIntelligenceEngine:
    """Test the Progress Intelligence Engine"""
    
    @pytest.fixture
    def engine(self):
        return create_progress_intelligence_engine()
    
    @pytest.mark.asyncio
    async def test_operation_analysis(self, engine):
        """Test operation context analysis"""
        message = "Analyze this complex Python code for performance issues and suggest optimizations"
        
        context = await engine.analyze_operation(message)
        
        assert context.operation_type == OperationType.CODE_ANALYSIS
        assert context.complexity_level in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED]
        assert context.estimated_duration > 0
        assert len(context.key_concepts) > 0
        assert context.requires_code == True
        assert context.requires_analysis == True
        assert "python" in context.key_concepts or "code" in context.key_concepts
    
    @pytest.mark.asyncio
    async def test_dynamic_milestone_generation(self, engine):
        """Test dynamic milestone generation"""
        message = "Help me solve this complex algorithm problem step by step"
        
        context = await engine.analyze_operation(message)
        milestones = await engine.generate_dynamic_milestones(context)
        
        assert len(milestones) > 0
        assert all(milestone.estimated_completion >= 0.0 and milestone.estimated_completion <= 1.0 
                  for milestone in milestones)
        assert all(milestone.context_message for milestone in milestones)
        assert all(milestone.user_benefit for milestone in milestones)
    
    @pytest.mark.asyncio
    async def test_progress_intelligence_calculation(self, engine):
        """Test progress intelligence calculation"""
        message = "Create a creative story about AI"
        
        context = await engine.analyze_operation(message)
        milestones = await engine.generate_dynamic_milestones(context)
        
        progress_intel = await engine.calculate_progress_intelligence(
            operation_context=context,
            milestones=milestones,
            current_step=3,
            total_steps=5,
            elapsed_time=2.5
        )
        
        assert progress_intel.completion_percentage >= 0.0
        assert progress_intel.completion_percentage <= 1.0
        assert progress_intel.eta_seconds >= 0.0
        assert progress_intel.confidence_score >= 0.0
        assert progress_intel.confidence_score <= 1.0
        assert progress_intel.contextual_message
        assert progress_intel.current_phase in ProgressPhase


class TestOperationAnalyzer:
    """Test the Operation Analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return create_operation_analyzer()
    
    @pytest.mark.asyncio
    async def test_operation_depth_analysis(self, analyzer):
        """Test deep operation analysis"""
        message = "Perform comprehensive analysis of this multi-layered system architecture"
        
        # Create mock operation context
        from intelligence.progress_intelligence import OperationContext
        context = OperationContext(
            operation_type=OperationType.TECHNICAL_EXPLANATION,
            complexity_level=ComplexityLevel.ADVANCED,
            estimated_duration=15.0,
            key_concepts=["system", "architecture", "analysis"],
            user_intent="analyze",
            technical_domain="system_architecture",
            requires_analysis=True
        )
        
        thinking_steps = [
            "Understanding system components",
            "Analyzing interconnections",
            "Evaluating performance characteristics"
        ]
        
        metrics = await analyzer.analyze_operation_depth(message, context, thinking_steps)
        
        assert metrics.thinking_steps_count == 3
        assert len(metrics.complexity_indicators) > 0
        assert metrics.performance_score > 0.0
        assert "high_technical_vocabulary" in metrics.complexity_indicators or \
               "complex_relationships" in metrics.complexity_indicators
    
    @pytest.mark.asyncio
    async def test_trajectory_prediction(self, analyzer):
        """Test operation trajectory prediction"""
        from intelligence.progress_intelligence import OperationContext
        from intelligence.operation_analyzer import OperationMetrics
        
        context = OperationContext(
            operation_type=OperationType.PROBLEM_SOLVING,
            complexity_level=ComplexityLevel.COMPLEX,
            estimated_duration=10.0,
            key_concepts=["algorithm", "optimization"],
            user_intent="solve"
        )
        
        metrics = OperationMetrics(
            thinking_steps_count=5,
            complexity_indicators=["high_reasoning_complexity", "multi_step_process"],
            performance_score=0.8
        )
        
        trajectory = await analyzer.predict_operation_trajectory(context, metrics, 3.0)
        
        assert "predicted_total_steps" in trajectory
        assert "predicted_remaining_time" in trajectory
        assert "trajectory_type" in trajectory
        assert trajectory["predicted_total_steps"] > 0


class TestSmartProgressMessaging:
    """Test the Smart Progress Messaging system"""
    
    @pytest.fixture
    def messaging(self):
        return create_smart_progress_messaging()
    
    @pytest.mark.asyncio
    async def test_adaptive_message_generation(self, messaging):
        """Test adaptive message generation"""
        from intelligence.progress_intelligence import OperationContext, ProgressIntelligence, ProgressMilestone
        from intelligence.operation_analyzer import OperationMetrics
        
        # Create mock progress intelligence
        context = OperationContext(
            operation_type=OperationType.CODE_ANALYSIS,
            complexity_level=ComplexityLevel.COMPLEX,
            estimated_duration=8.0,
            key_concepts=["code", "analysis"],
            user_intent="analyze"
        )
        
        milestone = ProgressMilestone(
            phase=ProgressPhase.SOLUTION_GENERATION,
            name="Code Analysis",
            description="Analyzing code patterns",
            estimated_completion=0.6,
            context_message="Analyzing code structure...",
            user_benefit="Identifying improvements"
        )
        
        progress_intel = ProgressIntelligence(
            operation_context=context,
            milestones=[milestone],
            current_phase=ProgressPhase.SOLUTION_GENERATION,
            completion_percentage=0.6,
            eta_seconds=3.2,
            confidence_score=0.85,
            contextual_message="Analyzing code patterns...",
            next_milestone=None
        )
        
        metrics = OperationMetrics(
            thinking_steps_count=4,
            complexity_indicators=["high_technical_vocabulary"],
            performance_score=0.8
        )
        
        # Test different message contexts
        for context_type in [MessageContext.STARTUP, MessageContext.PROGRESS, MessageContext.COMPLETION]:
            message = await messaging.generate_adaptive_message(
                progress_intelligence=progress_intel,
                operation_metrics=metrics,
                message_context=context_type,
                user_id="test_user"
            )
            
            assert message.content
            assert message.tone in MessageTone
            assert message.context == context_type
            assert message.confidence >= 0.0
    
    def test_tone_preference_setting(self, messaging):
        """Test user tone preference setting"""
        user_id = "test_user"
        tone = MessageTone.TECHNICAL
        
        messaging.set_user_tone_preference(user_id, tone)
        
        assert messaging.tone_preferences[user_id] == tone
    
    def test_messaging_insights(self, messaging):
        """Test messaging insights generation"""
        insights = messaging.get_messaging_insights()
        
        assert "total_templates" in insights
        assert "supported_tones" in insights
        assert "supported_contexts" in insights
        assert insights["total_templates"] > 0


class TestThinkingLLMClientIntelligence:
    """Test the enhanced Thinking LLM Client with intelligence"""
    
    @pytest.fixture
    def mock_base_client(self):
        """Create a mock base LLM client"""
        client = AsyncMock()
        client.initialize.return_value = True
        client.chat.return_value = {
            "response": "This is a test response",
            "model": "test-model",
            "processing_time": 1.5
        }
        return client
    
    @pytest.fixture
    def intelligent_config(self):
        """Create intelligent thinking configuration"""
        return ThinkingConfig(
            enable_intelligence=True,
            enable_contextual_messaging=True,
            enable_dynamic_milestones=True,
            enable_complexity_analysis=True,
            enable_adaptive_communication=True,
            message_tone=MessageTone.FRIENDLY
        )
    
    @pytest.fixture
    def thinking_client(self, mock_base_client, intelligent_config):
        """Create thinking client with mocked dependencies"""
        with patch('integrations.thinking_llm_client.LLMEngine', return_value=mock_base_client):
            with patch('integrations.thinking_llm_client.create_session') as mock_create:
                with patch('integrations.thinking_llm_client.stream_thinking') as mock_stream_thinking:
                    with patch('integrations.thinking_llm_client.stream_progress') as mock_stream_progress:
                        with patch('integrations.thinking_llm_client.close_session') as mock_close:
                            # Mock session creation
                            mock_create.return_value = {"session_id": "test-session"}
                            mock_stream_thinking.return_value = None
                            mock_stream_progress.return_value = None
                            mock_close.return_value = None
                            
                            client = ThinkingLLMClient(
                                ollama_host="http://localhost:11434",
                                default_model="test-model",
                                thinking_config=intelligent_config
                            )
                            return client
    
    @pytest.mark.asyncio
    async def test_intelligence_initialization(self, thinking_client):
        """Test that intelligence systems are properly initialized"""
        assert thinking_client.progress_intelligence is not None
        assert thinking_client.operation_analyzer is not None
        assert thinking_client.smart_messaging is not None
        
        capabilities = thinking_client.get_intelligence_capabilities()
        assert capabilities["intelligence_enabled"] == True
        assert capabilities["contextual_messaging"] == True
        assert capabilities["dynamic_milestones"] == True
        assert capabilities["intelligence_systems"]["progress_intelligence"] == True
    
    @pytest.mark.asyncio
    async def test_intelligent_chat_execution(self, thinking_client):
        """Test chat execution with intelligence"""
        await thinking_client.initialize()
        
        result = await thinking_client.chat_with_thinking(
            message="Analyze this complex algorithm for optimization opportunities",
            user_id="test_user",
            debug_mode=True
        )
        
        assert "response" in result
        assert "session_id" in result
        assert result["thinking_enabled"] == True
    
    @pytest.mark.asyncio
    async def test_message_complexity_analysis(self, thinking_client):
        """Test message complexity analysis"""
        complexity = await thinking_client.analyze_message_complexity(
            "Perform comprehensive analysis of this multi-threaded application architecture"
        )
        
        assert "operation_type" in complexity
        assert "complexity_level" in complexity
        assert "estimated_duration" in complexity
        assert "key_concepts" in complexity
        assert complexity["estimated_duration"] > 0
    
    @pytest.mark.asyncio
    async def test_operation_trajectory_prediction(self, thinking_client):
        """Test operation trajectory prediction"""
        trajectory = await thinking_client.predict_operation_trajectory(
            "Create a detailed technical specification for a microservices architecture"
        )
        
        assert "operation_context" in trajectory
        assert "trajectory_prediction" in trajectory
        assert trajectory["operation_context"]["type"]
        assert trajectory["operation_context"]["complexity"]
    
    @pytest.mark.asyncio
    async def test_user_tone_preference(self, thinking_client):
        """Test user tone preference setting"""
        await thinking_client.set_user_message_tone("test_user", MessageTone.TECHNICAL)
        
        # Verify the preference was set
        insights = await thinking_client.get_messaging_insights("test_user")
        assert "preferred_tone" in insights
    
    def test_intelligence_configuration(self, thinking_client):
        """Test intelligence configuration updates"""
        thinking_client.configure_intelligence(
            enable_contextual_messaging=False,
            message_tone=MessageTone.PROFESSIONAL
        )
        
        assert thinking_client.thinking_config.enable_contextual_messaging == False
        assert thinking_client.thinking_config.message_tone == MessageTone.PROFESSIONAL
    
    def test_intelligence_status(self, thinking_client):
        """Test intelligence status reporting"""
        status = thinking_client.get_intelligence_status()
        
        assert status["intelligence_enabled"] == True
        assert status["systems_initialized"]["progress_intelligence"] == True
        assert status["systems_initialized"]["operation_analyzer"] == True
        assert status["systems_initialized"]["smart_messaging"] == True
        assert "configuration" in status


class TestPhase3Integration:
    """Integration tests for complete Phase 3 functionality"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_intelligent_operation(self):
        """Test complete end-to-end intelligent operation"""
        # Create intelligence systems
        progress_engine = create_progress_intelligence_engine()
        operation_analyzer = create_operation_analyzer()
        smart_messaging = create_smart_progress_messaging()
        
        # Test message
        message = "Help me design and implement a scalable microservices architecture with proper monitoring"
        
        # Step 1: Analyze operation
        context = await progress_engine.analyze_operation(message)
        assert context.operation_type in [OperationType.TECHNICAL_EXPLANATION, OperationType.PROBLEM_SOLVING]
        assert context.complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED]
        
        # Step 2: Generate dynamic milestones
        milestones = await progress_engine.generate_dynamic_milestones(context)
        assert len(milestones) >= 3
        
        # Step 3: Simulate operation progress
        for step in range(1, 6):
            elapsed_time = step * 2.0
            
            # Calculate progress intelligence
            progress_intel = await progress_engine.calculate_progress_intelligence(
                operation_context=context,
                milestones=milestones,
                current_step=step,
                total_steps=5,
                elapsed_time=elapsed_time
            )
            
            # Analyze operation metrics
            thinking_steps = [f"Step {i}: Processing..." for i in range(1, step + 1)]
            metrics = await operation_analyzer.analyze_operation_depth(
                message, context, thinking_steps
            )
            
            # Generate adaptive message
            adaptive_msg = await smart_messaging.generate_adaptive_message(
                progress_intelligence=progress_intel,
                operation_metrics=metrics,
                message_context=MessageContext.PROGRESS,
                user_id="integration_test",
                elapsed_time=elapsed_time
            )
            
            # Verify message quality
            assert adaptive_msg.content
            assert adaptive_msg.confidence > 0.0
            assert progress_intel.completion_percentage >= 0.0
            assert progress_intel.eta_seconds >= 0.0
        
        print("✅ End-to-end intelligent operation test completed successfully!")
    
    @pytest.mark.asyncio
    async def test_performance_characteristics(self):
        """Test performance characteristics of intelligence systems"""
        progress_engine = create_progress_intelligence_engine()
        
        # Test multiple operation types for performance
        test_messages = [
            "Simple chat question",
            "Analyze this code for bugs",
            "Create a comprehensive technical architecture document",
            "Help me solve this complex algorithm optimization problem"
        ]
        
        total_analysis_time = 0
        
        for message in test_messages:
            start_time = time.time()
            
            context = await progress_engine.analyze_operation(message)
            milestones = await progress_engine.generate_dynamic_milestones(context)
            
            analysis_time = time.time() - start_time
            total_analysis_time += analysis_time
            
            # Verify reasonable performance (should be under 1 second per analysis)
            assert analysis_time < 1.0, f"Analysis took too long: {analysis_time:.2f}s"
            assert len(milestones) > 0
        
        avg_analysis_time = total_analysis_time / len(test_messages)
        print(f"✅ Average analysis time: {avg_analysis_time:.3f}s per operation")
        assert avg_analysis_time < 0.5, "Average analysis time should be under 500ms"


if __name__ == "__main__":
    # Run a quick integration test
    async def quick_test():
        print("🧠 Running Phase 3 Intelligence Quick Test...")
        
        # Test progress intelligence
        engine = create_progress_intelligence_engine()
        context = await engine.analyze_operation("Analyze complex Python code for performance issues")
        print(f"✅ Operation Type: {context.operation_type.value}")
        print(f"✅ Complexity: {context.complexity_level.value}")
        print(f"✅ Estimated Duration: {context.estimated_duration:.1f}s")
        
        # Test smart messaging
        messaging = create_smart_progress_messaging()
        insights = messaging.get_messaging_insights()
        print(f"✅ Message Templates: {insights['total_templates']}")
        print(f"✅ Supported Tones: {len(insights['supported_tones'])}")
        
        print("🎉 Phase 3 Intelligence Systems Working Correctly!")
    
    asyncio.run(quick_test())