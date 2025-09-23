"""
Continuous Learning System for Multi-Brain AI Architecture

This module implements the continuous learning capabilities that enable
all brains to learn from execution results, cross-brain knowledge sharing,
and external knowledge sources.
"""

from .continuous_learning_engine import ContinuousLearningEngine
from .execution_feedback_processor import ExecutionFeedbackProcessor
from .cross_brain_learner import CrossBrainLearner
from .external_knowledge_integrator import ExternalKnowledgeIntegrator

__all__ = [
    'ContinuousLearningEngine',
    'ExecutionFeedbackProcessor', 
    'CrossBrainLearner',
    'ExternalKnowledgeIntegrator'
]