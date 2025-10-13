"""FastAPI routes for audit endpoints."""

import os
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse

from audit.models import AIQueryAuditRecord, AuditResponse
from audit.sinks import enqueue_audit_record

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    include_in_schema=False,  # Keep outside public API docs unless explicitly flagged
)


def _verify_internal_auth(x_internal_key: Optional[str] = None) -> bool:
    """Verify internal authentication.
    
    Args:
        x_internal_key: Value from X-Internal-Key header
        
    Returns:
        True if authenticated, False otherwise
    """
    # Check if auth is disabled
    allow_no_auth = os.getenv("AUDIT_ALLOW_NO_AUTH", "false").lower() == "true"
    if allow_no_auth:
        return True
    
    # Verify token
    expected_token = os.getenv("AUDIT_INTERNAL_KEY")
    if not expected_token:
        logger.warning("AUDIT_INTERNAL_KEY not set, rejecting request")
        return False
    
    return x_internal_key == expected_token


@router.post(
    "/ai-query",
    response_model=AuditResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Record AI query audit trail",
    description="""
    Internal endpoint for persisting AI request/response traces for compliance.
    
    **Authentication**: Requires `X-Internal-Key` header unless `AUDIT_ALLOW_NO_AUTH=true`.
    
    **Non-blocking**: Returns 202 Accepted immediately; writes are queued.
    
    **Sinks**: Configured via `AUDIT_SINK` environment variable:
    - `stdout` (default): Logs to container stdout
    - `loki`: Pushes to Grafana Loki (requires `LOKI_URL`)
    - `postgres`: Writes to PostgreSQL (requires `POSTGRES_DSN`)
    """,
)
async def record_ai_query(
    record: AIQueryAuditRecord,
    x_internal_key: Optional[str] = Header(None, alias="X-Internal-Key"),
) -> AuditResponse:
    """Record an AI query audit trail.
    
    Args:
        record: The audit record to persist
        x_internal_key: Internal authentication token
        
    Returns:
        AuditResponse with status and record ID
        
    Raises:
        HTTPException: 401 if authentication fails, 422 if validation fails
    """
    # Verify authentication
    if not _verify_internal_auth(x_internal_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Internal-Key header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate unique record ID
    record_id = str(uuid.uuid4())
    
    # Enqueue for non-blocking write
    enqueued = await enqueue_audit_record(record)
    
    if not enqueued:
        logger.error(f"Failed to enqueue audit record {record_id}")
        # Still return 202 to avoid blocking caller, but log the error
        return AuditResponse(
            status="queued_with_errors",
            message="Audit record queued but queue is experiencing issues",
            record_id=record_id,
        )
    
    logger.info(
        f"Audit record enqueued: {record_id} "
        f"(trace_id={record.trace_id}, user_id={record.user_id})"
    )
    
    return AuditResponse(
        status="accepted",
        message="Audit record queued for processing",
        record_id=record_id,
    )


@router.get(
    "/health",
    summary="Audit subsystem health check",
    include_in_schema=False,
)
async def audit_health() -> JSONResponse:
    """Check audit subsystem health."""
    from audit.sinks import _audit_queue, _audit_worker_task
    
    queue_size = _audit_queue.qsize() if _audit_queue else None
    worker_running = _audit_worker_task and not _audit_worker_task.done()
    
    healthy = _audit_queue is not None and worker_running
    
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "queue_initialized": _audit_queue is not None,
            "worker_running": worker_running,
            "queue_size": queue_size,
        }
    )