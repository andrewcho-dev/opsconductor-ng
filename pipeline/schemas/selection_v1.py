"""
Selection v1 JSON Schema
Output from Stage B (Selector)

This schema defines the standardized format for tool selection decisions
in the NEWIDEA.MD pipeline architecture.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class PermissionLevel(str, Enum):
    """Permission levels for tools"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ToolCapability(BaseModel):
    """Individual tool capability definition"""
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="What this capability does")
    required_inputs: List[str] = Field(default=[], description="Required input parameters")
    optional_inputs: List[str] = Field(default=[], description="Optional input parameters")

class Tool(BaseModel):
    """Tool definition with capabilities and constraints"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    capabilities: List[ToolCapability] = Field(..., description="Tool capabilities")
    required_inputs: List[str] = Field(default=[], description="Base required inputs")
    permissions: PermissionLevel = Field(..., description="Required permission level")
    production_safe: bool = Field(..., description="Safe for production use")
    max_execution_time: int = Field(default=30, description="Maximum execution time in seconds")
    dependencies: List[str] = Field(default=[], description="Tool dependencies")

class SelectedTool(BaseModel):
    """Selected tool with justification and requirements"""
    tool_name: str = Field(..., description="Name of selected tool")
    justification: str = Field(..., description="Why this tool was selected")
    inputs_needed: List[str] = Field(default=[], description="Additional inputs required")
    execution_order: int = Field(default=1, description="Order of execution")
    depends_on: List[str] = Field(default=[], description="Tools this depends on")

class ExecutionPolicy(BaseModel):
    """Execution policy and constraints"""
    requires_approval: bool = Field(..., description="Whether approval is required")
    production_environment: bool = Field(default=False, description="Targeting production")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    max_execution_time: int = Field(..., description="Maximum total execution time")
    parallel_execution: bool = Field(default=False, description="Can tools run in parallel")
    rollback_required: bool = Field(default=False, description="Rollback capability needed")

class SelectionV1(BaseModel):
    """
    Selection v1 Schema - Output from Stage B (Selector)
    
    This is the standardized format for tool selection decisions.
    """
    
    # Core Selection Fields
    selection_id: str = Field(..., description="Unique selection identifier")
    decision_id: str = Field(..., description="Source decision ID from Stage A")
    timestamp: str = Field(..., description="ISO timestamp of selection")
    
    # Tool Selection
    selected_tools: List[SelectedTool] = Field(..., description="Selected tools with justification")
    total_tools: int = Field(..., description="Total number of tools selected")
    
    # Execution Policy
    policy: ExecutionPolicy = Field(..., description="Execution policy and constraints")
    
    # Additional Requirements
    additional_inputs_needed: List[str] = Field(default=[], description="Inputs not available from decision")
    environment_requirements: Dict[str, Any] = Field(default={}, description="Environment constraints")
    
    # Processing Metadata
    stage_b_version: str = Field(default="1.0.0", description="Stage B version")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    selection_confidence: float = Field(..., ge=0.0, le=1.0, description="Selection confidence")
    
    # Next Stage Routing
    next_stage: Literal["stage_c", "stage_d"] = Field(..., description="Next pipeline stage")
    ready_for_execution: bool = Field(default=False, description="Ready for immediate execution")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "selection_id": "sel_20241201_143025_def456",
                "decision_id": "dec_20241201_143022_abc123",
                "timestamp": "2024-12-01T14:30:25.456Z",
                "selected_tools": [
                    {
                        "tool_name": "systemctl",
                        "justification": "Required to restart nginx service",
                        "inputs_needed": ["service_name", "action"],
                        "execution_order": 1,
                        "depends_on": []
                    }
                ],
                "total_tools": 1,
                "policy": {
                    "requires_approval": True,
                    "production_environment": True,
                    "risk_level": "medium",
                    "max_execution_time": 60,
                    "parallel_execution": False,
                    "rollback_required": True
                },
                "additional_inputs_needed": [],
                "environment_requirements": {
                    "os": "linux",
                    "sudo_required": True
                },
                "stage_b_version": "1.0.0",
                "processing_time_ms": 125,
                "selection_confidence": 0.88,
                "next_stage": "stage_c",
                "ready_for_execution": False
            }
        }
    )

def validate_selection_v1(data: Dict[str, Any]) -> SelectionV1:
    """
    Validate and parse Selection v1 data
    
    Args:
        data: Raw selection data
        
    Returns:
        Validated SelectionV1 instance
        
    Raises:
        ValidationError: If data is invalid
    """
    return SelectionV1(**data)

def create_selection_template() -> Dict[str, Any]:
    """
    Create a template Selection v1 structure
    
    Returns:
        Template dictionary for Selection v1
    """
    return {
        "selection_id": "",
        "decision_id": "",
        "timestamp": "",
        "selected_tools": [],
        "total_tools": 0,
        "policy": {
            "requires_approval": False,
            "production_environment": False,
            "risk_level": "low",
            "max_execution_time": 30,
            "parallel_execution": False,
            "rollback_required": False
        },
        "additional_inputs_needed": [],
        "environment_requirements": {},
        "stage_b_version": "1.0.0",
        "processing_time_ms": None,
        "selection_confidence": 0.0,
        "next_stage": "stage_c",
        "ready_for_execution": False
    }