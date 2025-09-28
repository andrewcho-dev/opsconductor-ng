"""
OUIOE Phase 7: Conversational Intelligence - Data Models

Comprehensive data models for advanced conversational intelligence including
conversation memory, context awareness, user preferences, and analytics.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Set
from datetime import datetime
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    THINKING = "thinking"


class ContextDimension(str, Enum):
    """Dimensions of conversation context"""
    TEMPORAL = "temporal"          # Time-based context
    TOPICAL = "topical"           # Subject matter context
    EMOTIONAL = "emotional"        # Emotional state context
    TECHNICAL = "technical"        # Technical complexity context
    OPERATIONAL = "operational"    # Operations-specific context
    PREFERENCE = "preference"      # User preference context
    HISTORICAL = "historical"      # Past conversation context
    ENVIRONMENTAL = "environmental" # System/environment context


class PreferenceType(str, Enum):
    """Types of user preferences"""
    COMMUNICATION_STYLE = "communication_style"
    TECHNICAL_LEVEL = "technical_level"
    RESPONSE_FORMAT = "response_format"
    OPERATION_APPROACH = "operation_approach"
    RISK_TOLERANCE = "risk_tolerance"
    AUTOMATION_LEVEL = "automation_level"
    NOTIFICATION_FREQUENCY = "notification_frequency"
    DETAIL_LEVEL = "detail_level"


class ClarificationType(str, Enum):
    """Types of clarification requests"""
    AMBIGUITY_RESOLUTION = "ambiguity_resolution"
    CONTEXT_GATHERING = "context_gathering"
    PREFERENCE_CONFIRMATION = "preference_confirmation"
    TECHNICAL_SPECIFICATION = "technical_specification"
    SCOPE_DEFINITION = "scope_definition"
    RISK_ACKNOWLEDGMENT = "risk_acknowledgment"
    OPTION_SELECTION = "option_selection"
    VALIDATION_REQUEST = "validation_request"


class InsightType(str, Enum):
    """Types of conversation insights"""
    PATTERN_RECOGNITION = "pattern_recognition"
    PREFERENCE_EVOLUTION = "preference_evolution"
    COMMUNICATION_EFFECTIVENESS = "communication_effectiveness"
    TOPIC_CLUSTERING = "topic_clustering"
    EMOTIONAL_ANALYSIS = "emotional_analysis"
    TECHNICAL_PROGRESSION = "technical_progression"
    OPERATIONAL_TRENDS = "operational_trends"
    SATISFACTION_ANALYSIS = "satisfaction_analysis"


class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = Field(..., description="Conversation identifier")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Context and metadata
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)
    thinking_steps: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Semantic and analysis data
    semantic_embedding: Optional[List[float]] = Field(default=None)
    topics: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    
    # Response metadata
    response_time: Optional[float] = Field(default=None)
    tokens_used: Optional[int] = Field(default=None)
    model_used: Optional[str] = Field(default=None)
    
    # User feedback
    user_rating: Optional[int] = Field(default=None, ge=1, le=5)
    user_feedback: Optional[str] = Field(default=None)


class ConversationContext(BaseModel):
    """Multi-dimensional conversation context"""
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Context dimensions
    temporal_context: Dict[str, Any] = Field(default_factory=dict)
    topical_context: Dict[str, Any] = Field(default_factory=dict)
    emotional_context: Dict[str, Any] = Field(default_factory=dict)
    technical_context: Dict[str, Any] = Field(default_factory=dict)
    operational_context: Dict[str, Any] = Field(default_factory=dict)
    preference_context: Dict[str, Any] = Field(default_factory=dict)
    historical_context: Dict[str, Any] = Field(default_factory=dict)
    environmental_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Context metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    context_version: int = Field(default=1)
    active_topics: Set[str] = Field(default_factory=set)
    context_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Context relationships
    related_conversations: List[str] = Field(default_factory=list)
    context_inheritance: Dict[str, float] = Field(default_factory=dict)


class UserPreference(BaseModel):
    """Individual user preference"""
    preference_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User identifier")
    preference_type: PreferenceType = Field(..., description="Type of preference")
    
    # Preference data
    preference_value: Any = Field(..., description="Preference value")
    preference_weight: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Learning metadata
    learned_from_interactions: int = Field(default=0)
    last_reinforced: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Context and conditions
    context_conditions: Dict[str, Any] = Field(default_factory=dict)
    applicable_scenarios: List[str] = Field(default_factory=list)
    
    # Validation and feedback
    user_confirmed: bool = Field(default=False)
    effectiveness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    adaptation_history: List[Dict[str, Any]] = Field(default_factory=list)


class ClarificationRequest(BaseModel):
    """Request for clarification from user"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = Field(..., description="Conversation identifier")
    clarification_type: ClarificationType = Field(..., description="Type of clarification")
    
    # Request content
    question: str = Field(..., description="Clarification question")
    context: str = Field(..., description="Context for the question")
    options: List[str] = Field(default_factory=list)
    
    # Priority and urgency
    priority_score: float = Field(default=0.5, ge=0.0, le=1.0)
    urgency_level: int = Field(default=3, ge=1, le=5)
    blocking_operation: bool = Field(default=False)
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    reasoning: List[str] = Field(default_factory=list)
    confidence_in_need: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Response tracking
    response_received: bool = Field(default=False)
    response_content: Optional[str] = Field(default=None)
    response_timestamp: Optional[datetime] = Field(default=None)
    satisfaction_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ConversationInsight(BaseModel):
    """Analytical insight from conversation analysis"""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: InsightType = Field(..., description="Type of insight")
    
    # Insight content
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight description")
    key_findings: List[str] = Field(default_factory=list)
    
    # Data and evidence
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    statistical_significance: Optional[float] = Field(default=None)
    
    # Scope and context
    conversation_ids: List[str] = Field(default_factory=list)
    user_ids: List[str] = Field(default_factory=list)
    time_period: Dict[str, datetime] = Field(default_factory=dict)
    
    # Actionability
    actionable_recommendations: List[str] = Field(default_factory=list)
    impact_assessment: Dict[str, float] = Field(default_factory=dict)
    implementation_complexity: int = Field(default=3, ge=1, le=5)
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    analyst_notes: Optional[str] = Field(default=None)
    validation_status: str = Field(default="pending")


class ConversationSummary(BaseModel):
    """Summary of a conversation or conversation segment"""
    summary_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = Field(..., description="Conversation identifier")
    
    # Summary content
    title: str = Field(..., description="Summary title")
    abstract: str = Field(..., description="Brief abstract")
    key_points: List[str] = Field(default_factory=list)
    decisions_made: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    
    # Scope and metadata
    message_range: Dict[str, str] = Field(default_factory=dict)
    time_range: Dict[str, datetime] = Field(default_factory=dict)
    participant_count: int = Field(default=0)
    
    # Quality metrics
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    coherence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    generation_method: str = Field(default="ai_summarization")
    human_reviewed: bool = Field(default=False)


class ConversationMetrics(BaseModel):
    """Metrics for conversation analysis"""
    conversation_id: str = Field(..., description="Conversation identifier")
    
    # Basic metrics
    message_count: int = Field(default=0)
    total_duration: float = Field(default=0.0)
    average_response_time: float = Field(default=0.0)
    
    # Engagement metrics
    user_engagement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    conversation_depth: int = Field(default=0)
    topic_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Quality metrics
    average_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    clarification_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    satisfaction_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # Technical metrics
    total_tokens: int = Field(default=0)
    average_complexity: float = Field(default=0.0, ge=0.0, le=1.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Temporal metrics
    peak_activity_periods: List[Dict[str, Any]] = Field(default_factory=list)
    response_time_distribution: Dict[str, float] = Field(default_factory=dict)
    
    # Computed at
    computed_at: datetime = Field(default_factory=datetime.now)


# Utility models for complex operations

class ContextCorrelation(BaseModel):
    """Correlation between different context dimensions"""
    dimension_a: ContextDimension
    dimension_b: ContextDimension
    correlation_strength: float = Field(ge=-1.0, le=1.0)
    correlation_type: str  # "positive", "negative", "complex"
    confidence: float = Field(ge=0.0, le=1.0)
    sample_size: int
    statistical_significance: Optional[float] = Field(default=None)


class PreferenceCluster(BaseModel):
    """Cluster of related user preferences"""
    cluster_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cluster_name: str
    preference_ids: List[str]
    cluster_centroid: Dict[str, Any]
    coherence_score: float = Field(ge=0.0, le=1.0)
    user_count: int
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationPattern(BaseModel):
    """Identified pattern in conversations"""
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_name: str
    pattern_description: str
    pattern_type: str  # "sequential", "cyclical", "branching", "convergent"
    
    # Pattern characteristics
    trigger_conditions: List[str]
    typical_flow: List[str]
    success_indicators: List[str]
    failure_indicators: List[str]
    
    # Statistics
    occurrence_frequency: float
    success_rate: float = Field(ge=0.0, le=1.0)
    average_duration: float
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Context
    applicable_contexts: List[ContextDimension]
    user_segments: List[str]
    
    discovered_at: datetime = Field(default_factory=datetime.now)