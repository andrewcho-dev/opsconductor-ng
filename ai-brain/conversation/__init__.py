"""
OUIOE Phase 7: Conversational Intelligence

This module provides advanced conversational intelligence capabilities including:
- Conversation memory with semantic search
- Context awareness and correlation
- User preference learning and personalization
- Clarification intelligence
- Conversation analytics and insights

Components:
- ConversationMemoryEngine: Advanced conversation history management
- ContextAwarenessSystem: Multi-dimensional context tracking
- UserPreferenceLearning: Adaptive user behavior analysis
- ClarificationIntelligence: Smart question generation
- ConversationAnalytics: Deep conversation pattern analysis
"""

from conversation.conversation_models import *
from conversation.conversation_memory_engine import ConversationMemoryEngine
from conversation.context_awareness_system import ContextAwarenessSystem
from conversation.user_preference_learning import UserPreferenceLearning
from conversation.clarification_intelligence import ClarificationIntelligence
from conversation.conversation_analytics import ConversationAnalytics

__all__ = [
    # Models
    'ConversationMessage',
    'ConversationContext',
    'UserPreference',
    'ClarificationRequest',
    'ConversationInsight',
    'ContextDimension',
    'PreferenceType',
    'ClarificationType',
    'InsightType',
    
    # Engines
    'ConversationMemoryEngine',
    'ContextAwarenessSystem', 
    'UserPreferenceLearning',
    'ClarificationIntelligence',
    'ConversationAnalytics'
]