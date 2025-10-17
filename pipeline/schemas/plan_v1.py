"""
Plan v1 JSON Schema
Output from Stage C (Planner)

This schema defines the standardized format for execution plans
in the NEWIDEA.MD pipeline architecture.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class SafetyStage(str, Enum):
    """When safety checks should be performed"""
    BEFORE = "before"
    DURING = "during"
    AFTER = "after"

class FailureAction(str, Enum):
    """Actions to take when safety checks fail"""
    ABORT = "abort"
    WARN = "warn"
    CONTINUE = "continue"

class ExecutionStep(BaseModel):
    """Individual execution step in the plan"""
    id: str = Field(..., description="Unique step identifier")
    description: str = Field(..., description="Human-readable step description")
    tool: str = Field(..., description="Tool name to execute")
    inputs: Dict[str, Any] = Field(default={}, description="Tool-specific input parameters")
    preconditions: List[str] = Field(default=[], description="Conditions that must be met before execution")
    success_criteria: List[str] = Field(default=[], description="Indicators of successful execution")
    failure_handling: str = Field(..., description="What to do if this step fails")
    estimated_duration: int = Field(..., description="Estimated execution time in seconds")
    depends_on: List[str] = Field(default=[], description="Step IDs this step depends on")
    execution_order: int = Field(default=1, description="Order of execution for this step")
    
    # Tool execution metadata (enriched from database-backed catalog)
    requires_credentials: bool = Field(default=False, description="Whether this tool requires credentials")
    execution_location: str = Field(default="automation-service", description="Which service should execute this tool")
    tool_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional tool-specific metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "step_001_gather_info",
                "description": "Gather system information using ps command",
                "tool": "ps",
                "inputs": {
                    "format": "detailed",
                    "filter": "all_processes"
                },
                "preconditions": ["system_accessible", "ps_command_available"],
                "success_criteria": ["process_list_retrieved", "no_errors_occurred"],
                "failure_handling": "Log error and continue with limited information",
                "estimated_duration": 5,
                "depends_on": [],
                "execution_order": 1
            }
        }
    )

class SafetyCheck(BaseModel):
    """Safety check definition"""
    check: str = Field(..., description="Description of the safety check")
    stage: SafetyStage = Field(..., description="When to perform this check")
    failure_action: FailureAction = Field(..., description="Action to take if check fails")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "check": "Verify system has sufficient disk space (>10GB free)",
                "stage": "before",
                "failure_action": "abort"
            }
        }
    )

class RollbackStep(BaseModel):
    """Rollback procedure for a specific step"""
    step_id: str = Field(..., description="ID of the step this rollback applies to")
    rollback_action: str = Field(..., description="How to undo this step")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step_id": "step_003_modify_config",
                "rollback_action": "Restore configuration file from backup at /tmp/config.backup"
            }
        }
    )

class ObservabilityConfig(BaseModel):
    """Observability and monitoring configuration"""
    metrics_to_collect: List[str] = Field(default=[], description="Metrics to collect during execution")
    logs_to_monitor: List[str] = Field(default=[], description="Log sources to monitor")
    alerts_to_set: List[str] = Field(default=[], description="Alert conditions to configure")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metrics_to_collect": ["cpu_usage", "memory_usage", "disk_io"],
                "logs_to_monitor": ["/var/log/syslog", "/var/log/application.log"],
                "alerts_to_set": ["high_cpu_usage > 80%", "disk_space < 10%"]
            }
        }
    )

class ExecutionPlan(BaseModel):
    """Complete execution plan"""
    steps: List[ExecutionStep] = Field(..., description="Ordered list of execution steps")
    safety_checks: List[SafetyCheck] = Field(default=[], description="Safety checks to perform")
    rollback_plan: List[RollbackStep] = Field(default=[], description="Rollback procedures")
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig, description="Monitoring configuration")

class ExecutionMetadata(BaseModel):
    """Metadata about the execution plan"""
    total_estimated_time: int = Field(..., description="Total estimated execution time in seconds")
    risk_factors: List[str] = Field(default=[], description="Identified risk factors")
    approval_points: List[str] = Field(default=[], description="Step IDs requiring manual approval")
    checkpoint_steps: List[str] = Field(default=[], description="Step IDs for progress checkpoints")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_estimated_time": 180,
                "risk_factors": ["modifies_production_config", "requires_service_restart"],
                "approval_points": ["step_003_modify_config", "step_005_restart_service"],
                "checkpoint_steps": ["step_002_backup_config", "step_004_validate_config"]
            }
        }
    )

class PlanV1(BaseModel):
    """
    Plan v1 Schema - Complete execution plan output from Stage C
    
    This is the standardized output format for the Planner stage,
    containing detailed execution steps, safety measures, and metadata.
    """
    plan: ExecutionPlan = Field(..., description="The complete execution plan")
    execution_metadata: ExecutionMetadata = Field(..., description="Execution metadata and constraints")
    
    # Processing metadata
    stage: str = Field(default="stage_c_planner", description="Processing stage identifier")
    version: str = Field(default="1.0", description="Schema version")
    timestamp: str = Field(..., description="Processing timestamp (ISO format)")
    processing_time_ms: int = Field(..., description="Time taken to generate plan in milliseconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plan": {
                    "steps": [
                        {
                            "id": "step_001_gather_info",
                            "description": "Gather system process information",
                            "tool": "ps",
                            "inputs": {"format": "detailed"},
                            "preconditions": ["system_accessible"],
                            "success_criteria": ["process_list_retrieved"],
                            "failure_handling": "Log error and continue",
                            "estimated_duration": 5,
                            "depends_on": []
                        }
                    ],
                    "safety_checks": [
                        {
                            "check": "Verify system accessibility",
                            "stage": "before",
                            "failure_action": "abort"
                        }
                    ],
                    "rollback_plan": [],
                    "observability": {
                        "metrics_to_collect": ["execution_time"],
                        "logs_to_monitor": ["/var/log/syslog"],
                        "alerts_to_set": []
                    }
                },
                "execution_metadata": {
                    "total_estimated_time": 5,
                    "risk_factors": [],
                    "approval_points": [],
                    "checkpoint_steps": []
                },
                "stage": "stage_c_planner",
                "version": "1.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "processing_time_ms": 150
            }
        }
    )