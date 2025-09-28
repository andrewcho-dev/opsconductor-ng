#!/usr/bin/env python3
"""
OUIOE Phase 4: Comprehensive Decision Engine Test Suite

Advanced test suite for Phase 4 Core Decision Engine Integration
with comprehensive coverage of all decision engine components and
integration scenarios.

This test suite validates the complete decision engine ecosystem:
- Decision Engine Core with all decision types
- Model Coordinator with advanced selection algorithms
- Decision Visualizer with all layout modes
- Collaborative Reasoner with multi-agent scenarios
- Enhanced Thinking Client with decision capabilities
- End-to-end integration workflows
"""

import pytest
import asyncio
import time
import sys
import os
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

# Add the ai-brain directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Phase 4 decision engine components
from decision import (
    DecisionEngine,
    ModelCoordinator,
    DecisionVisualizer,
    CollaborativeReasoner,
    DecisionRequest,
    DecisionResult,
    DecisionType,
    DecisionPriority,
    DecisionContext,
    AgentRole,
    ModelCapability,
    VisualizationMode,
    NodeType,
    ReasoningAgent,
    ModelRequest
)

class TestDecisionEngineCore:
    """Test suite for Decision Engine Core functionality"""
    
    @pytest.fixture
    async def decision_engine(self):
        """Create decision engine instance"""
        return DecisionEngine()
    
    @pytest.mark.asyncio
    async def test_basic_decision_making(self, decision_engine):
        """Test basic decision making functionality"""
        # Create decision context
        context = DecisionContext(
            user_id="test_user",
            session_id="test_session",
            quality_threshold=0.8
        )
        
        # Create decision request
        request = DecisionRequest(
            question="Should we implement feature X?",
            decision_type=DecisionType.SIMPLE,
            priority=DecisionPriority.NORMAL,
            context=context,
            options=["Yes", "No", "Maybe"],
            criteria=["Cost", "Time", "Impact"]
        )
        
        # Execute decision
        result = await decision_engine.make_decision(request)
        
        # Validate result
        assert isinstance(result, DecisionResult)
        assert result.request_id == request.id
        assert result.confidence > 0
        assert len(result.steps) > 0
        assert result.processing_time > 0
        assert result.decision != ""
    
    @pytest.mark.asyncio
    async def test_complex_decision_types(self, decision_engine):
        """Test all decision types"""
        decision_types = [
            DecisionType.SIMPLE,
            DecisionType.COMPLEX,
            DecisionType.COLLABORATIVE,
            DecisionType.STRATEGIC,
            DecisionType.CREATIVE,
            DecisionType.ANALYTICAL,
            DecisionType.ETHICAL,
            DecisionType.TECHNICAL
        ]
        
        results = []
        for decision_type in decision_types:
            context = DecisionContext(user_id="test", session_id="test")
            request = DecisionRequest(
                question=f"Test {decision_type.value} decision",
                decision_type=decision_type,
                context=context
            )
            
            result = await decision_engine.make_decision(request)
            results.append(result)
            
            assert result.status.value == "completed"
            assert result.confidence > 0
        
        assert len(results) == len(decision_types)
    
    @pytest.mark.asyncio
    async def test_decision_performance_metrics(self, decision_engine):
        """Test decision performance tracking"""
        # Make several decisions
        for i in range(3):
            context = DecisionContext(user_id="test", session_id=f"test_{i}")
            request = DecisionRequest(
                question=f"Test decision {i}",
                decision_type=DecisionType.SIMPLE,
                context=context
            )
            await decision_engine.make_decision(request)
        
        # Check metrics
        metrics = decision_engine.get_performance_metrics()
        
        assert 'total_decisions' in metrics
        assert 'average_confidence' in metrics
        assert 'success_rate' in metrics
        assert metrics['total_decisions'] >= 3
        assert 0 <= metrics['average_confidence'] <= 1
        assert 0 <= metrics['success_rate'] <= 1

class TestModelCoordinator:
    """Test suite for Model Coordinator functionality"""
    
    @pytest.fixture
    def model_coordinator(self):
        """Create model coordinator instance"""
        return ModelCoordinator()
    
    def test_model_registration(self, model_coordinator):
        """Test model registration and availability"""
        available_models = model_coordinator.get_available_models()
        assert len(available_models) > 0
        
        # Check that default models are registered
        model_ids = [model.id for model in available_models]
        assert any("general" in model_id for model_id in model_ids)
        assert any("analytical" in model_id for model_id in model_ids)
    
    @pytest.mark.asyncio
    async def test_model_selection(self, model_coordinator):
        """Test intelligent model selection"""
        request = ModelRequest(
            task_type="analytical_task",
            required_capabilities={ModelCapability.ANALYSIS, ModelCapability.REASONING},
            max_models=2,
            min_models=1,
            quality_threshold=0.5
        )
        
        selection = await model_coordinator.select_models(request)
        
        assert len(selection.selected_models) >= 1
        assert len(selection.selected_models) <= 2
        assert selection.confidence > 0
        assert selection.selection_reasoning != ""
        assert len(selection.fallback_models) >= 0
    
    def test_capability_filtering(self, model_coordinator):
        """Test model filtering by capabilities"""
        analytical_models = model_coordinator.get_models_by_capability(ModelCapability.ANALYSIS)
        reasoning_models = model_coordinator.get_models_by_capability(ModelCapability.REASONING)
        creative_models = model_coordinator.get_models_by_capability(ModelCapability.CREATIVITY)
        
        assert len(analytical_models) > 0
        assert len(reasoning_models) > 0
        assert len(creative_models) > 0
        
        # Verify capabilities
        for model in analytical_models:
            assert ModelCapability.ANALYSIS in model.capabilities
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, model_coordinator):
        """Test model performance tracking"""
        available_models = model_coordinator.get_available_models()
        if available_models:
            model = available_models[0]
            
            # Update performance
            await model_coordinator.update_model_performance(
                model.id, response_time=1.5, success=True, confidence=0.9
            )
            
            # Check updated performance
            updated_model = model_coordinator.get_model_info(model.id)
            assert updated_model.performance.total_requests > 0
            assert updated_model.performance.reliability > 0

class TestDecisionVisualizer:
    """Test suite for Decision Visualizer functionality"""
    
    @pytest.fixture
    def decision_visualizer(self):
        """Create decision visualizer instance"""
        return DecisionVisualizer()
    
    @pytest.mark.asyncio
    async def test_decision_tree_creation(self, decision_visualizer):
        """Test decision tree creation and management"""
        tree = await decision_visualizer.create_decision_tree(
            decision_id="test_tree_123",
            title="Test Decision Tree",
            description="Testing decision visualization"
        )
        
        assert tree.id == "test_tree_123"
        assert tree.title == "Test Decision Tree"
        assert tree.description == "Testing decision visualization"
        assert len(tree.nodes) == 0
        assert len(tree.edges) == 0
    
    @pytest.mark.asyncio
    async def test_node_management(self, decision_visualizer):
        """Test decision tree node addition and management"""
        # Create tree
        tree = await decision_visualizer.create_decision_tree(
            decision_id="test_nodes",
            title="Node Test Tree"
        )
        
        # Add root node
        root_id = await decision_visualizer.add_decision_node(
            tree_id=tree.id,
            node_type=NodeType.ROOT,
            label="Root Decision",
            description="Starting point",
            confidence=0.9
        )
        
        assert root_id is not None
        assert len(tree.nodes) == 1
        
        # Add child node
        child_id = await decision_visualizer.add_decision_node(
            tree_id=tree.id,
            node_type=NodeType.ANALYSIS,
            label="Analysis Step",
            description="Analyzing options",
            parent_id=root_id,
            confidence=0.8
        )
        
        assert child_id is not None
        assert len(tree.nodes) == 2
        assert len(tree.edges) == 1
        
        # Verify parent-child relationship
        root_node = tree.get_node(root_id)
        child_node = tree.get_node(child_id)
        
        assert child_id in root_node.children_ids
        assert child_node.parent_id == root_id
    
    @pytest.mark.asyncio
    async def test_layout_algorithms(self, decision_visualizer):
        """Test different layout algorithms"""
        # Create tree with nodes
        tree = await decision_visualizer.create_decision_tree(
            decision_id="layout_test",
            title="Layout Test Tree"
        )
        
        # Add some nodes
        root_id = await decision_visualizer.add_decision_node(
            tree_id=tree.id,
            node_type=NodeType.ROOT,
            label="Root"
        )
        
        for i in range(3):
            await decision_visualizer.add_decision_node(
                tree_id=tree.id,
                node_type=NodeType.OPTION,
                label=f"Option {i+1}",
                parent_id=root_id
            )
        
        # Test different layout modes
        layout_modes = [
            VisualizationMode.TREE,
            VisualizationMode.RADIAL,
            VisualizationMode.FORCE_DIRECTED,
            VisualizationMode.HIERARCHICAL,
            VisualizationMode.TIMELINE
        ]
        
        for mode in layout_modes:
            await decision_visualizer.set_tree_layout(tree.id, mode)
            assert tree.layout_mode == mode
    
    @pytest.mark.asyncio
    async def test_tree_analytics(self, decision_visualizer):
        """Test decision tree analytics"""
        # Create tree with nodes
        tree = await decision_visualizer.create_decision_tree(
            decision_id="analytics_test",
            title="Analytics Test Tree"
        )
        
        # Add nodes
        root_id = await decision_visualizer.add_decision_node(
            tree_id=tree.id,
            node_type=NodeType.ROOT,
            label="Root",
            confidence=0.9
        )
        
        await decision_visualizer.add_decision_node(
            tree_id=tree.id,
            node_type=NodeType.ANALYSIS,
            label="Analysis",
            parent_id=root_id,
            confidence=0.8
        )
        
        # Get analytics
        analytics = decision_visualizer.get_tree_analytics(tree.id)
        
        assert analytics is not None
        assert 'total_nodes' in analytics
        assert 'total_edges' in analytics
        assert 'average_confidence' in analytics
        assert 'completion_percentage' in analytics
        assert analytics['total_nodes'] == 2
        assert analytics['total_edges'] == 1
        assert analytics['average_confidence'] > 0

class TestCollaborativeReasoner:
    """Test suite for Collaborative Reasoner functionality"""
    
    @pytest.fixture
    def collaborative_reasoner(self):
        """Create collaborative reasoner instance"""
        return CollaborativeReasoner()
    
    def test_agent_management(self, collaborative_reasoner):
        """Test reasoning agent management"""
        available_agents = collaborative_reasoner.get_available_agents()
        
        assert len(available_agents) > 0
        
        # Check for essential agent roles
        agent_roles = {agent.role for agent in available_agents}
        essential_roles = {AgentRole.ANALYST, AgentRole.CRITIC, AgentRole.SYNTHESIZER}
        
        assert essential_roles.issubset(agent_roles)
        
        # Test role-specific filtering
        analysts = collaborative_reasoner.get_agents_by_role(AgentRole.ANALYST)
        critics = collaborative_reasoner.get_agents_by_role(AgentRole.CRITIC)
        
        assert len(analysts) > 0
        assert len(critics) > 0
        
        for agent in analysts:
            assert agent.role == AgentRole.ANALYST
    
    @pytest.mark.asyncio
    async def test_reasoning_session_lifecycle(self, collaborative_reasoner):
        """Test complete reasoning session lifecycle"""
        # Start reasoning session
        session_id = await collaborative_reasoner.start_reasoning_session(
            topic="Test Decision",
            question="Should we proceed with the test?",
            context={"test_mode": True},
            required_roles=[AgentRole.ANALYST, AgentRole.CRITIC],
            max_iterations=3
        )
        
        assert session_id is not None
        
        # Check session exists
        session = collaborative_reasoner.get_reasoning_session(session_id)
        assert session is not None
        assert session.topic == "Test Decision"
        assert session.question == "Should we proceed with the test?"
        
        # Conduct reasoning
        result = await collaborative_reasoner.conduct_reasoning(session_id)
        
        assert result.recommendation != ""
        assert result.confidence > 0
        assert result.total_arguments > 0
        assert len(result.agent_participation) > 0
        assert result.reasoning_quality > 0
    
    @pytest.mark.asyncio
    async def test_agent_specialization(self, collaborative_reasoner):
        """Test agent specialization and behavior"""
        # Test different agent roles
        roles_to_test = [AgentRole.ANALYST, AgentRole.CRITIC, AgentRole.STRATEGIST]
        
        for role in roles_to_test:
            agents = collaborative_reasoner.get_agents_by_role(role)
            if agents:
                agent = agents[0]
                
                # Verify agent properties match role
                assert agent.role == role
                assert agent.specialization != ""
                assert agent.reasoning_style != ""
                assert 0 <= agent.confidence_threshold <= 1
                assert 0 <= agent.collaboration <= 1

class TestIntegratedWorkflows:
    """Test suite for integrated decision workflows"""
    
    @pytest.fixture
    async def integrated_system(self):
        """Create integrated decision system"""
        model_coordinator = ModelCoordinator()
        decision_visualizer = DecisionVisualizer()
        collaborative_reasoner = CollaborativeReasoner()
        decision_engine = DecisionEngine(
            model_coordinator=model_coordinator,
            decision_visualizer=decision_visualizer,
            collaborative_reasoner=collaborative_reasoner
        )
        
        return {
            'decision_engine': decision_engine,
            'model_coordinator': model_coordinator,
            'decision_visualizer': decision_visualizer,
            'collaborative_reasoner': collaborative_reasoner
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_decision_workflow(self, integrated_system):
        """Test complete end-to-end decision workflow"""
        decision_engine = integrated_system['decision_engine']
        
        # Create complex decision request
        context = DecisionContext(
            user_id="integration_test",
            session_id="integration_session",
            quality_threshold=0.8,
            require_consensus=True
        )
        
        request = DecisionRequest(
            question="Should we implement a new AI feature with collaborative reasoning?",
            decision_type=DecisionType.COLLABORATIVE,
            priority=DecisionPriority.HIGH,
            context=context,
            options=[
                "Implement with full collaboration",
                "Implement with limited collaboration",
                "Postpone implementation",
                "Cancel the feature"
            ],
            criteria=[
                "Technical feasibility",
                "Resource requirements",
                "User impact",
                "Risk assessment",
                "Strategic alignment"
            ]
        )
        
        # Execute integrated decision
        start_time = time.time()
        result = await decision_engine.make_decision(request)
        processing_time = time.time() - start_time
        
        # Validate comprehensive result
        assert result.decision != ""
        assert result.confidence > 0.5
        assert result.consensus_score > 0.5
        assert len(result.steps) >= 5
        assert len(result.models_used) > 0
        assert processing_time < 15.0  # Reasonable time limit
        assert result.quality_score > 0.5
    
    @pytest.mark.asyncio
    async def test_system_coordination(self, integrated_system):
        """Test coordination between all system components"""
        decision_engine = integrated_system['decision_engine']
        model_coordinator = integrated_system['model_coordinator']
        decision_visualizer = integrated_system['decision_visualizer']
        collaborative_reasoner = integrated_system['collaborative_reasoner']
        
        # Verify all systems are active
        assert decision_engine is not None
        assert model_coordinator is not None
        assert decision_visualizer is not None
        assert collaborative_reasoner is not None
        
        # Test model coordinator
        available_models = model_coordinator.get_available_models()
        assert len(available_models) > 0
        
        # Test decision visualizer
        tree = await decision_visualizer.create_decision_tree(
            decision_id="coordination_test",
            title="Coordination Test"
        )
        assert tree is not None
        
        # Test collaborative reasoner
        available_agents = collaborative_reasoner.get_available_agents()
        assert len(available_agents) > 0
        
        # Test decision engine with all components
        context = DecisionContext(user_id="coord_test", session_id="coord_session")
        request = DecisionRequest(
            question="Test system coordination",
            decision_type=DecisionType.COMPLEX,
            context=context
        )
        
        result = await decision_engine.make_decision(request)
        assert result.status.value == "completed"

class TestThinkingClientIntegration:
    """Test suite for enhanced thinking client integration"""
    
    def test_decision_engine_configuration(self):
        """Test decision engine configuration options"""
        from integrations.thinking_llm_client import ThinkingConfig
        
        config = ThinkingConfig(
            enable_decision_engine=True,
            enable_collaborative_reasoning=True,
            enable_decision_visualization=True,
            enable_multi_model_coordination=True,
            enable_real_time_decision_trees=True,
            decision_visualization_mode=VisualizationMode.RADIAL,
            max_reasoning_agents=8,
            consensus_threshold=0.85,
            decision_timeout=180.0,
            require_consensus_for_complex=True
        )
        
        assert config.enable_decision_engine
        assert config.enable_collaborative_reasoning
        assert config.enable_decision_visualization
        assert config.enable_multi_model_coordination
        assert config.enable_real_time_decision_trees
        assert config.decision_visualization_mode == VisualizationMode.RADIAL
        assert config.max_reasoning_agents == 8
        assert config.consensus_threshold == 0.85
        assert config.decision_timeout == 180.0
        assert config.require_consensus_for_complex
    
    def test_decision_capabilities_structure(self):
        """Test decision capabilities structure"""
        from integrations.thinking_llm_client import ThinkingConfig
        
        config = ThinkingConfig(enable_decision_engine=True)
        
        # Test capability structure
        capabilities = {
            "decision_engine_enabled": config.enable_decision_engine,
            "collaborative_reasoning": config.enable_collaborative_reasoning,
            "decision_visualization": config.enable_decision_visualization,
            "multi_model_coordination": config.enable_multi_model_coordination,
            "visualization_mode": config.decision_visualization_mode.value,
            "consensus_threshold": config.consensus_threshold
        }
        
        assert capabilities["decision_engine_enabled"]
        assert isinstance(capabilities["visualization_mode"], str)
        assert 0 <= capabilities["consensus_threshold"] <= 1

# Performance and stress tests
class TestPerformanceAndStress:
    """Performance and stress test suite"""
    
    @pytest.mark.asyncio
    async def test_concurrent_decisions(self):
        """Test concurrent decision processing"""
        decision_engine = DecisionEngine()
        
        # Create multiple concurrent decisions
        tasks = []
        for i in range(5):
            context = DecisionContext(user_id=f"user_{i}", session_id=f"session_{i}")
            request = DecisionRequest(
                question=f"Concurrent decision {i}",
                decision_type=DecisionType.SIMPLE,
                context=context
            )
            tasks.append(decision_engine.make_decision(request))
        
        # Execute concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Validate results
        assert len(results) == 5
        for result in results:
            assert result.status.value == "completed"
            assert result.confidence > 0
        
        # Performance check
        assert total_time < 30.0  # Should complete within reasonable time
    
    @pytest.mark.asyncio
    async def test_decision_engine_performance(self):
        """Test decision engine performance characteristics"""
        decision_engine = DecisionEngine()
        
        # Test simple decision performance
        context = DecisionContext(user_id="perf_test", session_id="perf_session")
        request = DecisionRequest(
            question="Performance test decision",
            decision_type=DecisionType.SIMPLE,
            context=context
        )
        
        start_time = time.time()
        result = await decision_engine.make_decision(request)
        processing_time = time.time() - start_time
        
        # Performance assertions
        assert processing_time < 5.0  # Simple decisions should be fast
        assert result.processing_time > 0
        assert result.processing_time < 10.0

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])