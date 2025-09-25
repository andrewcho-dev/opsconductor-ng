"""
OpsConductor AI Brain - Modern API Module

This module contains the modern API routers that replace legacy functionality
with improved architecture and capabilities.
"""

# from .knowledge_router import knowledge_router  # Temporarily disabled - missing knowledge_engine
from .learning_router import learning_router

__all__ = ["learning_router"]  # "knowledge_router" temporarily removed