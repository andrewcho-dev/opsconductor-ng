"""
OUIOE Phase 6: Deductive Analysis & Intelligent Insights
========================================================

This module provides comprehensive deductive analysis capabilities for the OUIOE system,
including pattern recognition, root cause analysis, trend identification, correlation analysis,
and intelligent recommendation generation.

Key Components:
- DeductiveAnalysisEngine: Core analysis orchestration
- PatternRecognitionEngine: Advanced pattern detection
- RecommendationEngine: Intelligent recommendation generation
- Analysis Models: Comprehensive data structures

Features:
- Multi-dimensional pattern recognition
- Root cause analysis with evidence correlation
- Trend identification and forecasting
- Anomaly detection and classification
- Cross-pattern correlation analysis
- AI-driven insight generation
- Actionable recommendation generation
- Continuous learning and improvement

Author: OUIOE Development Team
Version: 1.0.0
"""

from .analysis_models import (
    # Core data structures
    DataPoint,
    Pattern,
    Correlation,
    RootCause,
    Trend,
    Recommendation,
    AnalysisResult,
    AnalysisContext,
    AnalysisMetrics,
    LearningData,
    
    # Enums
    AnalysisType,
    PatternType,
    TrendDirection,
    RecommendationType,
    ConfidenceLevel
)

from .pattern_recognition import PatternRecognitionEngine
from .deductive_analysis_engine import DeductiveAnalysisEngine
from .recommendation_engine import RecommendationEngine

# Version information
__version__ = "1.0.0"
__author__ = "OUIOE Development Team"

# Export main classes and functions
__all__ = [
    # Core engines
    "DeductiveAnalysisEngine",
    "PatternRecognitionEngine", 
    "RecommendationEngine",
    
    # Data models
    "DataPoint",
    "Pattern",
    "Correlation",
    "RootCause",
    "Trend",
    "Recommendation",
    "AnalysisResult",
    "AnalysisContext",
    "AnalysisMetrics",
    "LearningData",
    
    # Enums
    "AnalysisType",
    "PatternType",
    "TrendDirection",
    "RecommendationType",
    "ConfidenceLevel",
    
    # Utility functions
    "create_analysis_context",
    "create_data_point",
    "get_analysis_summary"
]

# Utility functions for easy usage
def create_analysis_context(
    user_id: str = None,
    session_id: str = None,
    analysis_goals: list = None,
    preferences: dict = None
) -> AnalysisContext:
    """
    Create an analysis context with common defaults.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        analysis_goals: List of analysis goals
        preferences: Analysis preferences
        
    Returns:
        Configured AnalysisContext
    """
    return AnalysisContext(
        user_id=user_id,
        session_id=session_id,
        analysis_goals=analysis_goals or [],
        preferences=preferences or {}
    )

def create_data_point(
    timestamp,
    value,
    source: str,
    tags: list = None,
    metadata: dict = None
) -> DataPoint:
    """
    Create a data point with common defaults.
    
    Args:
        timestamp: Data point timestamp
        value: Data point value
        source: Data source identifier
        tags: List of tags
        metadata: Additional metadata
        
    Returns:
        Configured DataPoint
    """
    return DataPoint(
        timestamp=timestamp,
        value=value,
        source=source,
        tags=tags or [],
        metadata=metadata or {}
    )

def get_analysis_summary(analysis_result: AnalysisResult) -> dict:
    """
    Get a summary of analysis results.
    
    Args:
        analysis_result: Analysis result to summarize
        
    Returns:
        Dictionary with analysis summary
    """
    return {
        'analysis_id': analysis_result.id,
        'analysis_type': analysis_result.analysis_type.value,
        'confidence_level': analysis_result.confidence_level.value,
        'patterns_found': len(analysis_result.patterns),
        'correlations_found': len(analysis_result.correlations),
        'root_causes_found': len(analysis_result.root_causes),
        'trends_found': len(analysis_result.trends),
        'recommendations_count': len(analysis_result.recommendations),
        'key_insights_count': len(analysis_result.key_insights),
        'action_items_count': len(analysis_result.action_items),
        'execution_time': str(analysis_result.duration),
        'summary': analysis_result.summary
    }

# Module-level configuration
DEFAULT_CONFIG = {
    'min_data_points': 5,
    'max_analysis_time': 300,  # 5 minutes
    'confidence_threshold': 0.6,
    'correlation_threshold': 0.7,
    'max_patterns': 50,
    'max_recommendations': 20,
    'enable_learning': True,
    'cache_results': True
}

def get_default_config() -> dict:
    """Get default configuration for analysis engines."""
    return DEFAULT_CONFIG.copy()

# Initialize logging for the module
import logging

logger = logging.getLogger(__name__)
logger.info("OUIOE Phase 6: Deductive Analysis & Intelligent Insights module initialized")

# Module metadata
MODULE_INFO = {
    'name': 'OUIOE Phase 6: Deductive Analysis & Intelligent Insights',
    'version': __version__,
    'description': 'Advanced deductive analysis and intelligent insights generation',
    'components': [
        'DeductiveAnalysisEngine',
        'PatternRecognitionEngine',
        'RecommendationEngine'
    ],
    'capabilities': [
        'Pattern Recognition',
        'Root Cause Analysis',
        'Trend Identification',
        'Correlation Analysis',
        'Anomaly Detection',
        'Recommendation Generation',
        'Continuous Learning'
    ],
    'performance_targets': {
        'analysis_time': '<60 seconds for standard datasets',
        'pattern_detection': '>90% accuracy for known patterns',
        'recommendation_relevance': '>85% user satisfaction',
        'memory_usage': '<50MB per analysis session'
    }
}

def get_module_info() -> dict:
    """Get module information and capabilities."""
    return MODULE_INFO.copy()