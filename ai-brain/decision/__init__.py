"""
OUIOE Phase 4: Core Decision Engine Integration

Revolutionary collaborative AI decision platform providing:
- Multi-model decision coordination
- Real-time decision visualization  
- Collaborative reasoning framework
- Advanced decision analytics

This module transforms AI decision-making with unprecedented transparency
and intelligence through collaborative multi-agent reasoning.
"""

from .decision_engine import (
    DecisionEngine, DecisionRequest, DecisionResult, DecisionType, 
    DecisionPriority, DecisionContext, DecisionStatus, DecisionStep
)
from .model_coordinator import (
    ModelCoordinator, ModelSelection, ModelPerformance, ModelType,
    ModelCapability, ModelStatus, ModelInfo, ModelRequest
)
from .decision_visualizer import (
    DecisionVisualizer, DecisionTree, DecisionNode, DecisionEdge,
    NodeType, NodeStatus, VisualizationMode
)
from .collaborative_reasoner import (
    CollaborativeReasoner, ReasoningAgent, ReasoningResult, ReasoningSession,
    ReasoningArgument, AgentRole, ReasoningPhase, ArgumentType
)

__all__ = [
    # Decision Engine
    'DecisionEngine',
    'DecisionRequest', 
    'DecisionResult',
    'DecisionType',
    'DecisionPriority',
    'DecisionContext',
    'DecisionStatus',
    'DecisionStep',
    
    # Model Coordinator
    'ModelCoordinator',
    'ModelSelection',
    'ModelPerformance',
    'ModelType',
    'ModelCapability',
    'ModelStatus',
    'ModelInfo',
    'ModelRequest',
    
    # Decision Visualizer
    'DecisionVisualizer',
    'DecisionTree',
    'DecisionNode',
    'DecisionEdge',
    'NodeType',
    'NodeStatus',
    'VisualizationMode',
    
    # Collaborative Reasoner
    'CollaborativeReasoner',
    'ReasoningAgent',
    'ReasoningResult',
    'ReasoningSession',
    'ReasoningArgument',
    'AgentRole',
    'ReasoningPhase',
    'ArgumentType'
]

__version__ = "4.0.0"
__phase__ = "Phase 4: Core Decision Engine Integration"