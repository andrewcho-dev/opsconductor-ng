"""
Streaming Infrastructure for OUIOE (Ollama Universal Intelligent Operations Engine)
Real-time thinking visualization and progress updates
"""

from .stream_manager import CentralStreamManager
from .redis_thinking_stream import RedisThinkingStreamManager
from .thinking_data_models import (
    ThinkingStep, ProgressUpdate, StreamConfig, ThinkingContext,
    StreamingSession, ThinkingType, ProgressType
)

# Alias for backward compatibility
StreamManager = CentralStreamManager

__all__ = [
    'CentralStreamManager',
    'StreamManager',
    'RedisThinkingStreamManager',
    'ThinkingStep',
    'ProgressUpdate',
    'StreamConfig',
    'ThinkingContext',
    'StreamingSession',
    'ThinkingType',
    'ProgressType'
]

__version__ = "1.0.0"
__author__ = "OpsConductor AI Brain Team"