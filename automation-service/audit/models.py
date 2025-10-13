"""Pydantic models for audit records."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ToolExecution(BaseModel):
    """Record of a single tool execution within an AI query."""
    name: str = Field(..., description="Tool name")
    latency_ms: int = Field(..., ge=0, description="Tool execution latency in milliseconds")
    ok: bool = Field(..., description="Whether the tool execution succeeded")


class AIQueryAuditRecord(BaseModel):
    """Audit record for an AI query/response interaction.
    
    This model captures the complete context of an AI interaction for compliance
    and observability purposes.
    """
    trace_id: str = Field(..., description="Distributed trace ID (W3C format)")
    user_id: str = Field(..., description="User or service account identifier")
    input: str = Field(..., description="User input/prompt")
    output: str = Field(..., description="AI-generated response")
    tools: List[ToolExecution] = Field(default_factory=list, description="Tools executed during query")
    duration_ms: int = Field(..., ge=0, description="Total query duration in milliseconds")
    created_at: datetime = Field(..., description="Timestamp of query (ISO-8601)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
                "user_id": "user-123",
                "input": "Deploy application to production",
                "output": "Deployment initiated successfully",
                "tools": [
                    {"name": "kubectl_apply", "latency_ms": 450, "ok": True},
                    {"name": "verify_deployment", "latency_ms": 230, "ok": True}
                ],
                "duration_ms": 1250,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class AuditResponse(BaseModel):
    """Response from audit endpoint."""
    status: str = Field(..., description="Status of audit operation")
    message: str = Field(..., description="Human-readable message")
    record_id: Optional[str] = Field(None, description="Unique identifier for the audit record")