#!/usr/bin/env python3
"""
Execution Service - Consolidated Jobs and Executor Service
Handles job management, workflow execution, and task processing
Combines the functionality of jobs-service and executor-service
"""

import os
import sys
import json
import time
import uuid
import base64
import threading
import traceback
import random
import zipfile
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, List

import psycopg2
import psycopg2.extras
import hmac
import hashlib
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator, Field
from dotenv import load_dotenv
import jsonschema
import winrm
from jinja2 import Template, Environment, BaseLoader, select_autoescape
import aiohttp
import asyncio
import requests

# Import service modules (self-contained)
from .database import get_db_cursor, check_database_health, cleanup_database_pool
from .logging_config import setup_service_logging, get_logger, log_startup, log_shutdown
from .middleware import add_standard_middleware
from .models import HealthResponse, HealthCheck, PaginatedResponse, create_success_response
from .errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error, ServiceCommunicationError
from .auth import require_admin_role, get_user_from_request
from .utils import utility_render_template, utility_render_file_paths, utility_create_error_result, get_service_client

# Import complex shared modules (kept as shared for now)
from shared.celery_config import celery_app
from shared.tasks import execute_job_run
from shared.visual_workflow_engine import workflow_engine
import shared.utility_service_clients as service_clients_utility

# Import utility modules for execution
try:
    from utils.utility_http_executor import HTTPExecutor
    from utils.utility_webhook_executor import WebhookExecutor
    from utils.utility_command_builder import CommandBuilder
    from utils.utility_sftp_executor import SFTPExecutor
    from utils.utility_notification_utils import NotificationUtils
    from ssh_executor import SSHExecutor, SFTPExecutor as SSHSFTPExecutor, SSHExecutionError
except ImportError as e:
    logger.warning(f"Some utility modules not available: {e}")

# Import visual job schema
try:
    from visual_job_schema import VISUAL_JOB_SCHEMA, EXPORT_FORMAT_SCHEMA
except ImportError:
    logger.warning("Visual job schema not available")
    VISUAL_JOB_SCHEMA = {}
    EXPORT_FORMAT_SCHEMA = {}

# Load environment variables
load_dotenv()

# Setup structured logging
setup_service_logging("execution-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("execution-service")

# FastAPI app
app = FastAPI(
    title="Execution Service", 
    version="1.0.0",
    description="Consolidated job management and execution service"
)

# Add standard middleware
add_standard_middleware(app, "execution-service", version="1.0.0")

# Configuration
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default-key-change-in-production")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default-webhook-secret")

# Global executor instance
job_executor = None

# ============================================================================
# JOB MANAGEMENT ENDPOINTS (from jobs-service)
# ============================================================================

class VisualJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    visual_workflow: Dict[str, Any] = Field(..., description="Visual workflow definition")
    schedule: Optional[str] = Field(None, description="Cron schedule expression")
    enabled: bool = Field(True, description="Whether the job is enabled")
    tags: Optional[List[str]] = Field(default_factory=list)

class VisualJobUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    visual_workflow: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None
    tags: Optional[List[str]] = None

@app.post("/jobs")
async def create_job(job: VisualJobCreate, current_user: Dict[str, Any] = Depends(require_admin_role)):
    """Create a new visual workflow job"""
    try:
        # Validate visual workflow against schema
        if VISUAL_JOB_SCHEMA:
            jsonschema.validate(job.visual_workflow, VISUAL_JOB_SCHEMA)
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO jobs (name, description, visual_workflow, schedule, enabled, tags, created_by, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (
                job.name,
                job.description,
                json.dumps(job.visual_workflow),
                job.schedule,
                job.enabled,
                json.dumps(job.tags) if job.tags else None,
                current_user["user_id"],
                current_user["user_id"]
            ))
            
            result = cursor.fetchone()
            
        return create_success_response(
            message="Job created successfully",
            data={
                "id": result["id"],
                "name": job.name,
                "created_at": result["created_at"].isoformat()
            }
        )
        
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Invalid visual workflow: {e.message}")
    except Exception as e:
        logger.error(f"Job creation error: {e}", exc_info=True)
        raise handle_database_error(e, "job creation")

@app.get("/jobs")
async def list_jobs(
    page: int = 1,
    limit: int = 50,
    enabled: Optional[bool] = None,
    tag: Optional[str] = None
):
    """List all jobs with pagination and filtering"""
    try:
        offset = (page - 1) * limit
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if enabled is not None:
            where_conditions.append("enabled = %s")
            params.append(enabled)
            
        if tag:
            where_conditions.append("tags::jsonb ? %s")
            params.append(tag)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        with get_db_cursor() as cursor:
            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM jobs {where_clause}", params)
            total = cursor.fetchone()["count"]
            
            # Get jobs
            cursor.execute(f"""
                SELECT id, name, description, schedule, enabled, tags, 
                       created_at, updated_at, created_by, updated_by
                FROM jobs 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [limit, offset])
            
            jobs = cursor.fetchall()
            
        return {
            "success": True,
            "message": "Jobs retrieved successfully",
            "data": [dict(job) for job in jobs],
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Job listing error: {e}", exc_info=True)
        raise handle_database_error(e, "job listing")

# ============================================================================
# JOB EXECUTION ENDPOINTS (from executor-service)
# ============================================================================

@app.post("/jobs/{job_id}/execute")
async def execute_job(
    job_id: int,
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """Execute a job immediately"""
    try:
        # Get job details
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, visual_workflow, enabled
                FROM jobs 
                WHERE id = %s
            """, (job_id,))
            
            job = cursor.fetchone()
            if not job:
                raise NotFoundError("Job", job_id)
            
            if not job["enabled"]:
                raise ValidationError("Cannot execute disabled job")
            
            # Create job run record
            cursor.execute("""
                INSERT INTO job_runs (job_id, status, started_by, started_at)
                VALUES (%s, 'queued', %s, %s)
                RETURNING id
            """, (job_id, current_user["user_id"], datetime.utcnow()))
            
            job_run_id = cursor.fetchone()["id"]
        
        # Queue the job for execution
        task = execute_job_run.delay(job_run_id, job["visual_workflow"])
        
        return create_success_response(
            message="Job queued for execution",
            data={
                "job_id": job_id,
                "job_run_id": job_run_id,
                "task_id": task.id
            }
        )
        
    except Exception as e:
        logger.error(f"Job execution error: {e}", exc_info=True)
        raise handle_database_error(e, "job execution")

# ============================================================================
# HEALTH AND STATUS ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_health = check_database_health()
    
    # Check Celery connection
    celery_health = {"status": "healthy"}
    try:
        celery_app.control.inspect().ping()
    except Exception as e:
        celery_health = {"status": "unhealthy", "error": str(e)}
    
    checks = [
        {
            "name": "database",
            "status": db_health["status"],
            "details": db_health
        },
        {
            "name": "celery",
            "status": celery_health["status"],
            "details": celery_health
        }
    ]
    
    overall_status = "healthy" if all(check["status"] == "healthy" for check in checks) else "unhealthy"
    
    return HealthResponse(
        service="execution-service",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

# ============================================================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Service startup"""
    log_startup("execution-service", "1.0.0", 3010)
    
    # Initialize job executor
    global job_executor
    try:
        job_executor = JobExecutor()
        logger.info("Job executor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize job executor: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Service shutdown"""
    log_shutdown("execution-service")
    cleanup_database_pool()

# ============================================================================
# JOB EXECUTOR CLASS (from executor-service)
# ============================================================================

class JobExecutor:
    """Consolidated job executor for all execution types"""
    
    def __init__(self):
        self.logger = get_logger("job_executor")
        self.encryption_key = ENCRYPTION_KEY
        
    def execute_workflow(self, workflow: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a visual workflow"""
        try:
            if context is None:
                context = {}
                
            # Use the workflow engine to process the visual workflow
            result = workflow_engine.execute_workflow(workflow, context)
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow execution error: {e}", exc_info=True)
            return utility_create_error_result(
                error_message=f"Workflow execution failed: {str(e)}",
                exception=e
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3008)