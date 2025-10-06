"""
Decision v1 JSON Schema
Core structured output from Stage A (Classifier)

This schema defines the standardized format for all AI decisions
in the NEWIDEA.MD pipeline architecture.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class DecisionType(str, Enum):
    """Type of decision made by Stage A"""
    ACTION = "action"
    INFO = "info"

class ConfidenceLevel(str, Enum):
    """Confidence levels for AI decisions"""
    HIGH = "high"      # 0.8-1.0
    MEDIUM = "medium"  # 0.5-0.79
    LOW = "low"        # 0.0-0.49

class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EntityV1(BaseModel):
    """Extracted entity from user input"""
    type: str = Field(..., description="Type of entity (hostname, service, command, etc.)")
    value: str = Field(..., description="Actual entity value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")

class IntentV1(BaseModel):
    """Classified intent from user input"""
    category: str = Field(..., description="Intent category (automation, monitoring, etc.)")
    action: str = Field(..., description="Specific action within category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    capabilities: List[str] = Field(default=[], description="Required capabilities to fulfill this intent")

class DecisionV1(BaseModel):
    """
    Decision v1 Schema - Output from Stage A (Classifier)
    
    This is the standardized format for all AI decisions in the pipeline.
    Every user request gets converted to this structured format.
    """
    
    # Core Decision Fields
    decision_id: str = Field(..., description="Unique decision identifier")
    decision_type: DecisionType = Field(..., description="Type of decision (action/info)")
    timestamp: str = Field(..., description="ISO timestamp of decision")
    
    # Intent Analysis
    intent: IntentV1 = Field(..., description="Classified user intent")
    entities: List[EntityV1] = Field(default=[], description="Extracted entities")
    
    # Confidence and Risk
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall decision confidence")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence category")
    risk_level: RiskLevel = Field(..., description="Initial risk assessment")
    
    # Context
    original_request: str = Field(..., description="Original user request")
    context: Dict[str, Any] = Field(default={}, description="Additional context")
    
    # Processing Metadata
    stage_a_version: str = Field(default="1.0.0", description="Stage A version")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    
    # Next Stage Routing
    requires_approval: bool = Field(default=False, description="Whether this decision requires approval")
    next_stage: Literal["stage_b", "stage_d"] = Field(..., description="Next pipeline stage")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision_id": "dec_20241201_143022_abc123",
                "decision_type": "action",
                "timestamp": "2024-12-01T14:30:22.123Z",
                "intent": {
                    "category": "automation",
                    "action": "restart_service",
                    "confidence": 0.92
                },
                "entities": [
                    {
                        "type": "service",
                        "value": "nginx",
                        "confidence": 0.95
                    },
                    {
                        "type": "hostname",
                        "value": "web-server-01",
                        "confidence": 0.88
                    }
                ],
                "overall_confidence": 0.90,
                "confidence_level": "high",
                "risk_level": "medium",
                "original_request": "restart nginx on web-server-01",
                "context": {
                    "user_id": "user123",
                    "session_id": "sess456"
                },
                "stage_a_version": "1.0.0",
                "processing_time_ms": 245,
                "requires_approval": True,
                "next_stage": "stage_b"
            }
        }
    )

def validate_decision_v1(data: Dict[str, Any]) -> DecisionV1:
    """
    Validate and parse Decision v1 data
    
    Args:
        data: Raw decision data
        
    Returns:
        Validated DecisionV1 instance
        
    Raises:
        ValidationError: If data is invalid
    """
    return DecisionV1(**data)

def create_decision_template() -> Dict[str, Any]:
    """
    Create a template Decision v1 structure
    
    Returns:
        Template dictionary for Decision v1
    """
    return {
        "decision_id": "",
        "decision_type": "action",
        "timestamp": "",
        "intent": {
            "category": "",
            "action": "",
            "confidence": 0.0
        },
        "entities": [],
        "overall_confidence": 0.0,
        "confidence_level": "low",
        "risk_level": "low",
        "original_request": "",
        "context": {},
        "stage_a_version": "1.0.0",
        "processing_time_ms": None,
        "requires_approval": False,
        "next_stage": "stage_b"
    }