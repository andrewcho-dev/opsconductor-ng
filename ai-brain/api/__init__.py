"""
OpsConductor AI Brain - Modern API Module

This module contains the modern API routers that replace legacy functionality
with improved architecture and capabilities.
"""

from .knowledge_router import knowledge_router
from .learning_router import learning_router

__all__ = ["knowledge_router", "learning_router"]