"""
Multi-Brain Coordination System

This module implements the coordination layer that orchestrates communication
and collaboration between different brain components in the multi-brain architecture.
"""

from .multi_brain_coordinator import MultiBrainCoordinator
from .brain_registry import BrainRegistry
from .confidence_aggregator import ConfidenceAggregator

__all__ = ['MultiBrainCoordinator', 'BrainRegistry', 'ConfidenceAggregator']