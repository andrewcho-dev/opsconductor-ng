"""
Data models for real-time thinking visualization and progress updates
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ThinkingType(str, Enum):
    """Types of thinking steps"""
    INITIALIZATION = "initialization"
    ANALYSIS = "analysis"
    DECISION = "decision"
    PLANNING = "planning"
    EVALUATION = "evaluation"
    RISK_ASSESSMENT = "risk_assessment"
    SERVICE_SELECTION = "service_selection"
    WORKFLOW_GENERATION = "workflow_generation"
    EXECUTION_PLANNING = "execution_planning"
    RESULT_ANALYSIS = "result_analysis"


class ProgressType(str, Enum):
    """Types of progress updates"""
    PROGRESS = "progress"
    INTERMEDIATE_RESULT = "intermediate_result"
    THINKING_ALOUD = "thinking_aloud"
    DISCOVERY = "discovery"
    WARNING = "warning"
    COMPLETION = "completion"


class ThinkingStep(BaseModel):
    """Individual thinking step from Ollama"""
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this thinking step occurred")
    thinking_type: ThinkingType = Field(..., description="Type of thinking step")
    content: str = Field(..., description="Main thinking content")
    reasoning_chain: List[str] = Field(default_factory=list, description="Step-by-step reasoning")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in this thinking step")
    alternatives_considered: List[str] = Field(default_factory=list, description="Alternative approaches considered")
    decision_factors: List[str] = Field(default_factory=list, description="Factors that influenced the decision")
    context_used: Optional[Dict[str, Any]] = Field(default=None, description="Context information used")
    estimated_duration: Optional[float] = Field(default=None, description="Estimated time for this step in seconds")


class ProgressUpdate(BaseModel):
    """Progress update during operation execution"""
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this update occurred")
    update_type: ProgressType = Field(..., description="Type of progress update")
    message: str = Field(..., description="Human-readable progress message")
    progress_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Progress percentage")
    current_step: Optional[str] = Field(default=None, description="Current step description")
    total_steps: Optional[int] = Field(default=None, description="Total number of steps")
    estimated_remaining: Optional[str] = Field(default=None, description="Estimated remaining time")
    intermediate_findings: Optional[List[Dict[str, Any]]] = Field(default=None, description="Intermediate discoveries")
    current_activity: Optional[str] = Field(default=None, description="What the AI is currently doing")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence in current progress")


class StreamMessage(BaseModel):
    """Generic stream message wrapper"""
    message_id: str = Field(default_factory=lambda: f"msg-{datetime.now().timestamp()}")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    message_type: str = Field(..., description="Type of message (thinking/progress)")
    data: Union[ThinkingStep, ProgressUpdate] = Field(..., description="Message payload")


class StreamConfig(BaseModel):
    """Configuration for streaming"""
    session_id: str = Field(..., description="Session identifier")
    debug_mode: bool = Field(default=False, description="Enable debug mode with detailed thinking")
    progress_updates: bool = Field(default=True, description="Enable progress updates")
    thinking_stream_name: str = Field(default="thinking", description="Redis stream name for thinking")
    progress_stream_name: str = Field(default="progress", description="Redis stream name for progress")
    max_stream_length: int = Field(default=1000, description="Maximum messages to keep in stream")
    update_threshold_seconds: int = Field(default=5, description="Minimum seconds between progress updates")


class ThinkingContext(BaseModel):
    """Context for thinking operations"""
    user_request: str = Field(..., description="Original user request")
    system_context: Dict[str, Any] = Field(default_factory=dict, description="System context")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Previous conversation")
    available_services: Dict[str, bool] = Field(default_factory=dict, description="Available services")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    safety_constraints: List[str] = Field(default_factory=list, description="Safety constraints")
    operation_complexity: str = Field(default="medium", description="Estimated operation complexity")
    estimated_duration: Optional[float] = Field(default=None, description="Estimated total duration")


class StreamingSession(BaseModel):
    """Active streaming session"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    config: StreamConfig = Field(..., description="Session configuration")
    context: ThinkingContext = Field(..., description="Thinking context")
    is_active: bool = Field(default=True, description="Whether session is active")
    last_activity: datetime = Field(default_factory=datetime.now)
    thinking_steps_count: int = Field(default=0, description="Number of thinking steps")
    progress_updates_count: int = Field(default=0, description="Number of progress updates")


class StreamStats(BaseModel):
    """Statistics for streaming session"""
    session_id: str = Field(..., description="Session identifier")
    total_thinking_steps: int = Field(default=0)
    total_progress_updates: int = Field(default=0)
    average_confidence: float = Field(default=0.0)
    session_duration: float = Field(default=0.0, description="Session duration in seconds")
    thinking_types_used: Dict[str, int] = Field(default_factory=dict)
    progress_types_used: Dict[str, int] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)