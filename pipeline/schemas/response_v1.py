"""
Response v1 JSON Schema
Output from Stage D (Answerer)

This schema defines the standardized format for user-facing responses
in the NEWIDEA.MD pipeline architecture.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from datetime import datetime

class ResponseType(str, Enum):
    """Type of response being provided"""
    INFORMATION = "information"
    PLAN_SUMMARY = "plan_summary"
    APPROVAL_REQUEST = "approval_request"
    EXECUTION_READY = "execution_ready"
    ERROR = "error"
    CLARIFICATION = "clarification"

class ConfidenceLevel(str, Enum):
    """Confidence level in the response"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ActionSuggestion(BaseModel):
    """Suggested follow-up action"""
    action: str = Field(..., description="Suggested action to take")
    description: str = Field(..., description="Description of why this action is suggested")
    priority: Literal["high", "medium", "low"] = Field(..., description="Priority level of the suggestion")
    estimated_time: Optional[int] = Field(None, description="Estimated time to complete in seconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "Monitor system performance",
                "description": "Keep an eye on CPU and memory usage after the deployment",
                "priority": "medium",
                "estimated_time": 300
            }
        }
    )

class ApprovalPoint(BaseModel):
    """Point in the plan that requires approval"""
    step_id: str = Field(..., description="ID of the step requiring approval")
    reason: str = Field(..., description="Why approval is needed")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Risk level of the step")
    approver_role: str = Field(..., description="Role required to approve this step")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step_id": "step_003_restart_service",
                "reason": "Production service restart requires approval",
                "risk_level": "high",
                "approver_role": "operations_manager"
            }
        }
    )

class ExecutionSummary(BaseModel):
    """Summary of the execution plan"""
    total_steps: int = Field(..., description="Total number of execution steps")
    estimated_duration: int = Field(..., description="Total estimated execution time in seconds")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Overall risk level")
    tools_involved: List[str] = Field(..., description="List of tools that will be used")
    safety_checks: int = Field(..., description="Number of safety checks in place")
    approval_points: int = Field(..., description="Number of approval points required")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_steps": 5,
                "estimated_duration": 180,
                "risk_level": "medium",
                "tools_involved": ["systemctl", "journalctl", "ps"],
                "safety_checks": 12,
                "approval_points": 2
            }
        }
    )

class ResponseV1(BaseModel):
    """
    Stage D Answerer response schema
    
    This represents the final user-facing response from the NEWIDEA.MD pipeline,
    containing human-readable information about the request processing results.
    """
    
    # Core response information
    response_type: ResponseType = Field(..., description="Type of response being provided")
    message: str = Field(..., description="Main response message for the user")
    confidence: ConfidenceLevel = Field(..., description="Confidence level in the response")
    
    # Execution plan summary (when applicable)
    execution_summary: Optional[ExecutionSummary] = Field(None, description="Summary of execution plan")
    
    # Approval workflow (when required)
    approval_required: bool = Field(default=False, description="Whether approval is required before execution")
    approval_points: List[ApprovalPoint] = Field(default=[], description="Points requiring approval")
    
    # Follow-up suggestions
    suggested_actions: List[ActionSuggestion] = Field(default=[], description="Suggested follow-up actions")
    
    # Context and metadata
    sources_consulted: List[str] = Field(default=[], description="Sources of information used")
    related_documentation: List[str] = Field(default=[], description="Links to relevant documentation")
    
    # Error handling
    warnings: List[str] = Field(default=[], description="Warnings about the request or plan")
    limitations: List[str] = Field(default=[], description="Limitations or constraints identified")
    
    # Technical details (for advanced users)
    technical_details: Optional[Dict[str, Any]] = Field(None, description="Technical details for advanced users")
    
    # Clarification support (when response_type is CLARIFICATION)
    clarification_needed: Optional[List["ClarificationRequest"]] = Field(None, description="List of clarifications needed")
    partial_analysis: Optional[Dict[str, Any]] = Field(None, description="Partial analysis completed so far")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    # Response metadata
    response_id: str = Field(..., description="Unique response identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response generation timestamp")
    processing_time_ms: int = Field(..., description="Time taken to generate response in milliseconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response_type": "plan_summary",
                "message": "I've created a comprehensive plan to restart the web service safely. The plan includes 5 steps with built-in safety checks and will take approximately 3 minutes to complete.",
                "confidence": "high",
                "execution_summary": {
                    "total_steps": 5,
                    "estimated_duration": 180,
                    "risk_level": "medium",
                    "tools_involved": ["systemctl", "journalctl", "ps"],
                    "safety_checks": 12,
                    "approval_points": 2
                },
                "approval_required": True,
                "approval_points": [
                    {
                        "step_id": "step_003_restart_service",
                        "reason": "Production service restart requires approval",
                        "risk_level": "high",
                        "approver_role": "operations_manager"
                    }
                ],
                "suggested_actions": [
                    {
                        "action": "Monitor service health",
                        "description": "Watch service metrics for 10 minutes after restart",
                        "priority": "high",
                        "estimated_time": 600
                    }
                ],
                "sources_consulted": ["service_configuration", "deployment_logs", "monitoring_data"],
                "related_documentation": ["/docs/service-restart-procedures", "/docs/monitoring-guidelines"],
                "warnings": ["Service restart will cause brief downtime"],
                "limitations": ["Cannot verify external dependencies"],
                "response_id": "resp_001_20240101_120000",
                "timestamp": "2024-01-01T12:00:00Z",
                "processing_time_ms": 250
            }
        }
    )

class ClarificationRequest(BaseModel):
    """Request for clarification from the user"""
    question: str = Field(..., description="Question that needs clarification")
    options: List[str] = Field(default=[], description="Possible options for the user to choose from")
    required: bool = Field(default=True, description="Whether this clarification is required to proceed")
    context: str = Field(..., description="Context explaining why clarification is needed")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Which environment should I target for this deployment?",
                "options": ["development", "staging", "production"],
                "required": True,
                "context": "The request mentions 'web service' but doesn't specify the target environment. This affects the safety procedures and approval requirements."
            }
        }
    )

class ClarificationResponse(BaseModel):
    """Response requesting clarification from the user"""
    response_type: Literal[ResponseType.CLARIFICATION] = ResponseType.CLARIFICATION
    message: str = Field(..., description="Main clarification request message")
    clarifications_needed: List[ClarificationRequest] = Field(..., description="List of clarifications needed")
    partial_analysis: Optional[Dict[str, Any]] = Field(None, description="Partial analysis completed so far")
    
    # Response metadata
    response_id: str = Field(..., description="Unique response identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response generation timestamp")
    processing_time_ms: int = Field(..., description="Time taken to generate response in milliseconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response_type": "clarification",
                "message": "I need some additional information to create the best plan for your request.",
                "clarifications_needed": [
                    {
                        "question": "Which environment should I target?",
                        "options": ["development", "staging", "production"],
                        "required": True,
                        "context": "This affects safety procedures and approval requirements"
                    }
                ],
                "partial_analysis": {
                    "intent": "service_restart",
                    "confidence": 0.85,
                    "identified_service": "web-service"
                },
                "response_id": "resp_clarify_001",
                "timestamp": "2024-01-01T12:00:00Z",
                "processing_time_ms": 150
            }
        }
    )