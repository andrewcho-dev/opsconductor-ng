"""Pydantic v2 data models for OpsConductor NG."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class UserIntent(BaseModel):
    """User's intent parsed from input."""
    
    query: str = Field(..., description="The user's query or request")
    trace_id: str = Field(..., description="Trace ID for this request")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class SelectedTool(BaseModel):
    """A tool selected for execution."""
    
    tool_name: str = Field(..., description="Name of the selected tool")
    tool_id: Optional[str] = Field(None, description="Unique identifier for the tool")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Selection confidence score")
    reasoning: Optional[str] = Field(None, description="Reasoning for tool selection")


class Step(BaseModel):
    """A single step in an execution plan."""
    
    step_id: str = Field(..., description="Unique identifier for this step")
    tool_name: str = Field(..., description="Tool to execute in this step")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters for tool execution")
    depends_on: list[str] = Field(default_factory=list, description="Step IDs this step depends on")
    description: Optional[str] = Field(None, description="Human-readable description of the step")


class ExecutionPlan(BaseModel):
    """A complete execution plan."""
    
    plan_id: str = Field(..., description="Unique identifier for this plan")
    trace_id: str = Field(..., description="Trace ID for this request")
    steps: list[Step] = Field(..., description="Ordered list of steps to execute")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional plan metadata")


class StepResult(BaseModel):
    """Result of executing a single step."""
    
    step_id: str = Field(..., description="ID of the executed step")
    success: bool = Field(..., description="Whether the step succeeded")
    output: Any = Field(None, description="Output from the step execution")
    error: Optional[str] = Field(None, description="Error message if step failed")
    duration_ms: Optional[float] = Field(None, description="Execution duration in milliseconds")


class RunResult(BaseModel):
    """Result of executing a complete plan."""
    
    run_id: str = Field(..., description="Unique identifier for this run")
    plan_id: str = Field(..., description="ID of the executed plan")
    trace_id: str = Field(..., description="Trace ID for this request")
    success: bool = Field(..., description="Whether the entire run succeeded")
    step_results: list[StepResult] = Field(..., description="Results from each step")
    total_duration_ms: Optional[float] = Field(None, description="Total execution duration in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional run metadata")