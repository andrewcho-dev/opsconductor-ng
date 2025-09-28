"""
OUIOE Phase 6: Deductive Analysis & Intelligent Insights - Analysis Models
===========================================================================

This module provides comprehensive data models for the deductive analysis system,
supporting pattern recognition, root cause analysis, trend identification, and
intelligent recommendation generation.

Key Features:
- Pattern recognition and correlation models
- Root cause analysis structures
- Trend identification and forecasting
- Recommendation generation and scoring
- Analysis result tracking and learning
- Performance metrics and confidence scoring

Author: OUIOE Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid


class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    PATTERN_RECOGNITION = "pattern_recognition"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    TREND_IDENTIFICATION = "trend_identification"
    CORRELATION_ANALYSIS = "correlation_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SECURITY_ANALYSIS = "security_analysis"


class PatternType(Enum):
    """Types of patterns that can be recognized."""
    TEMPORAL = "temporal"
    BEHAVIORAL = "behavioral"
    STRUCTURAL = "structural"
    PERFORMANCE = "performance"
    ERROR = "error"
    USAGE = "usage"
    SECURITY = "security"
    RESOURCE = "resource"


class TrendDirection(Enum):
    """Direction of identified trends."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    CYCLICAL = "cyclical"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"


class RecommendationType(Enum):
    """Types of recommendations that can be generated."""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    OPTIMIZATION = "optimization"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"
    SCALING = "scaling"
    BEST_PRACTICE = "best_practice"


class ConfidenceLevel(Enum):
    """Confidence levels for analysis results."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class DataPoint:
    """Represents a single data point for analysis."""
    timestamp: datetime
    value: Union[float, int, str, bool]
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'source': self.source,
            'metadata': self.metadata,
            'tags': self.tags
        }


@dataclass
class Pattern:
    """Represents a recognized pattern in the data."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: PatternType = PatternType.BEHAVIORAL
    name: str = ""
    description: str = ""
    confidence: float = 0.0
    frequency: int = 0
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None
    data_points: List[DataPoint] = field(default_factory=list)
    characteristics: Dict[str, Any] = field(default_factory=dict)
    related_patterns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'pattern_type': self.pattern_type.value,
            'name': self.name,
            'description': self.description,
            'confidence': self.confidence,
            'frequency': self.frequency,
            'first_occurrence': self.first_occurrence.isoformat() if self.first_occurrence else None,
            'last_occurrence': self.last_occurrence.isoformat() if self.last_occurrence else None,
            'data_points': [dp.to_dict() for dp in self.data_points],
            'characteristics': self.characteristics,
            'related_patterns': self.related_patterns
        }


@dataclass
class Correlation:
    """Represents a correlation between two or more variables."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    variables: List[str] = field(default_factory=list)
    correlation_coefficient: float = 0.0
    p_value: float = 1.0
    confidence: float = 0.0
    correlation_type: str = "linear"
    description: str = ""
    time_range: Tuple[datetime, datetime] = field(default_factory=lambda: (datetime.now(), datetime.now()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'variables': self.variables,
            'correlation_coefficient': self.correlation_coefficient,
            'p_value': self.p_value,
            'confidence': self.confidence,
            'correlation_type': self.correlation_type,
            'description': self.description,
            'time_range': [self.time_range[0].isoformat(), self.time_range[1].isoformat()]
        }


@dataclass
class RootCause:
    """Represents a potential root cause identified through analysis."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)
    impact_assessment: Dict[str, Any] = field(default_factory=dict)
    likelihood: float = 0.0
    severity: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'contributing_factors': self.contributing_factors,
            'impact_assessment': self.impact_assessment,
            'likelihood': self.likelihood,
            'severity': self.severity
        }


@dataclass
class Trend:
    """Represents an identified trend in the data."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    direction: TrendDirection = TrendDirection.STABLE
    strength: float = 0.0
    confidence: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    slope: float = 0.0
    r_squared: float = 0.0
    forecast: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'direction': self.direction.value,
            'strength': self.strength,
            'confidence': self.confidence,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'slope': self.slope,
            'r_squared': self.r_squared,
            'forecast': self.forecast
        }


@dataclass
class Recommendation:
    """Represents an actionable recommendation generated from analysis."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    recommendation_type: RecommendationType = RecommendationType.BEST_PRACTICE
    priority: int = 1  # 1-5, where 5 is highest priority
    confidence: float = 0.0
    impact_score: float = 0.0
    effort_estimate: str = "medium"
    implementation_steps: List[str] = field(default_factory=list)
    expected_benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    related_analysis: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'recommendation_type': self.recommendation_type.value,
            'priority': self.priority,
            'confidence': self.confidence,
            'impact_score': self.impact_score,
            'effort_estimate': self.effort_estimate,
            'implementation_steps': self.implementation_steps,
            'expected_benefits': self.expected_benefits,
            'risks': self.risks,
            'prerequisites': self.prerequisites,
            'related_analysis': self.related_analysis
        }


@dataclass
class AnalysisResult:
    """Comprehensive result of a deductive analysis operation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_type: AnalysisType = AnalysisType.PATTERN_RECOGNITION
    timestamp: datetime = field(default_factory=datetime.now)
    duration: timedelta = field(default_factory=lambda: timedelta(seconds=0))
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    
    # Analysis components
    patterns: List[Pattern] = field(default_factory=list)
    correlations: List[Correlation] = field(default_factory=list)
    root_causes: List[RootCause] = field(default_factory=list)
    trends: List[Trend] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    
    # Metadata
    data_sources: List[str] = field(default_factory=list)
    analysis_parameters: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Summary
    summary: str = ""
    key_insights: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'analysis_type': self.analysis_type.value,
            'timestamp': self.timestamp.isoformat(),
            'duration': str(self.duration),
            'confidence_level': self.confidence_level.value,
            'patterns': [p.to_dict() for p in self.patterns],
            'correlations': [c.to_dict() for c in self.correlations],
            'root_causes': [rc.to_dict() for rc in self.root_causes],
            'trends': [t.to_dict() for t in self.trends],
            'recommendations': [r.to_dict() for r in self.recommendations],
            'data_sources': self.data_sources,
            'analysis_parameters': self.analysis_parameters,
            'quality_metrics': self.quality_metrics,
            'summary': self.summary,
            'key_insights': self.key_insights,
            'action_items': self.action_items
        }


@dataclass
class AnalysisContext:
    """Context information for analysis operations."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    analysis_goals: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    time_range: Optional[Tuple[datetime, datetime]] = None
    data_filters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'analysis_goals': self.analysis_goals,
            'constraints': self.constraints,
            'preferences': self.preferences,
            'time_range': [self.time_range[0].isoformat(), self.time_range[1].isoformat()] if self.time_range else None,
            'data_filters': self.data_filters
        }


@dataclass
class AnalysisMetrics:
    """Performance and quality metrics for analysis operations."""
    analysis_id: str = ""
    execution_time: float = 0.0
    data_points_processed: int = 0
    patterns_found: int = 0
    correlations_found: int = 0
    recommendations_generated: int = 0
    confidence_score: float = 0.0
    quality_score: float = 0.0
    completeness_score: float = 0.0
    accuracy_estimate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'analysis_id': self.analysis_id,
            'execution_time': self.execution_time,
            'data_points_processed': self.data_points_processed,
            'patterns_found': self.patterns_found,
            'correlations_found': self.correlations_found,
            'recommendations_generated': self.recommendations_generated,
            'confidence_score': self.confidence_score,
            'quality_score': self.quality_score,
            'completeness_score': self.completeness_score,
            'accuracy_estimate': self.accuracy_estimate
        }


@dataclass
class LearningData:
    """Data structure for continuous learning and improvement."""
    analysis_id: str = ""
    feedback_score: Optional[float] = None
    user_feedback: str = ""
    implementation_success: Optional[bool] = None
    actual_outcomes: Dict[str, Any] = field(default_factory=dict)
    lessons_learned: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'analysis_id': self.analysis_id,
            'feedback_score': self.feedback_score,
            'user_feedback': self.user_feedback,
            'implementation_success': self.implementation_success,
            'actual_outcomes': self.actual_outcomes,
            'lessons_learned': self.lessons_learned,
            'improvement_suggestions': self.improvement_suggestions,
            'timestamp': self.timestamp.isoformat()
        }