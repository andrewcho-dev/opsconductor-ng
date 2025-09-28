"""
OUIOE Phase 3: Intelligent Progress Communication
Contextual progress intelligence with adaptive messaging and operation analysis.
"""

from .progress_intelligence import (
    ProgressIntelligenceEngine,
    OperationType,
    ComplexityLevel,
    ProgressPhase,
    OperationContext,
    ProgressMilestone,
    ProgressIntelligence,
    create_progress_intelligence_engine
)

from .operation_analyzer import (
    OperationAnalyzer,
    OperationMetrics,
    OperationPattern,
    create_operation_analyzer
)

from .progress_messaging import (
    SmartProgressMessaging,
    MessageTone,
    MessageContext,
    MessageTemplate,
    AdaptiveMessage,
    create_smart_progress_messaging
)

__all__ = [
    # Progress Intelligence
    "ProgressIntelligenceEngine",
    "OperationType",
    "ComplexityLevel", 
    "ProgressPhase",
    "OperationContext",
    "ProgressMilestone",
    "ProgressIntelligence",
    "create_progress_intelligence_engine",
    
    # Operation Analysis
    "OperationAnalyzer",
    "OperationMetrics",
    "OperationPattern",
    "create_operation_analyzer",
    
    # Progress Messaging
    "SmartProgressMessaging",
    "MessageTone",
    "MessageContext",
    "MessageTemplate",
    "AdaptiveMessage",
    "create_smart_progress_messaging"
]

# Version info
__version__ = "3.0.0"
__phase__ = "Phase 3: Intelligent Progress Communication"