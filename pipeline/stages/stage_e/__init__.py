"""
Stage E - Executor

This module implements the execution stage of the OpsConductor pipeline,
responsible for safely executing plans on real infrastructure with 7 critical safety features.
"""

from .executor import StageEExecutor

__all__ = [
    "StageEExecutor",
]