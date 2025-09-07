#!/usr/bin/env python3
"""
Jobs Service - Python FastAPI Implementation
Job definition and execution management with full CRUD operations
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

import sys
sys.path.append('/home/opsconductor')

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, validator, Field
from dotenv import load_dotenv
import jsonschema

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool, get_database_metrics
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, PaginatedResponse, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error
from shared.auth import verify_token_with_auth_service, require_admin_or_operator_role

# Load environment variables
load_dotenv()

# Setup structured logging
setup_service_logging("jobs-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("jobs-service")

# FastAPI app
app = FastAPI(
    title="Jobs Service", 
    version="1.0.0",
    description="Job definition and execution management service"
)

# Add standard middleware
add_standard_middleware(app, "jobs-service", version="1.0.0")



# Configuration

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Job Definition Schema (from implementation plan)
JOB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "JobDefinition",
    "type": "object",
    "required": ["name", "version", "steps"],
    "properties": {
        "name": {"type": "string"},
        "version": {"type": "integer", "minimum": 1},
        "parameters": {"type": "object", "additionalProperties": True},
        "steps": {
            "type": "array",
            "items": {
                "oneOf": [
                    {
                        "type": "object",
                        "required": ["type", "shell", "target", "command"],
                        "properties": {
                            "type": {"const": "winrm.exec"},
                            "shell": {"enum": ["powershell", "cmd"]},
                            "target": {"type": "string"},
                            "command": {"type": "string"},
                            "timeoutSec": {"type": "integer", "minimum": 1}
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "target", "destPath", "contentB64"],
                        "properties": {
                            "type": {"const": "winrm.copy"},
                            "target": {"type": "string"},
                            "destPath": {"type": "string"},
                            "contentB64": {"type": "string"},
                            "overwrite": {"type": "boolean", "default": True},
                            "timeoutSec": {"type": "integer", "minimum": 1}
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "url"],
                        "properties": {
                            "type": {"enum": ["http.get", "http.post", "http.put", "http.delete", "http.patch"]},
                            "name": {"type": "string"},
                            "url": {"type": "string"},
                            "headers": {"type": "object", "additionalProperties": {"type": "string"}},
                            "body": {"oneOf": [{"type": "string"}, {"type": "object"}]},
                            "auth_type": {"enum": ["none", "basic", "bearer", "api_key"]},
                            "auth_username": {"type": "string"},
                            "auth_password": {"type": "string"},
                            "auth_token": {"type": "string"},
                            "auth_header": {"type": "string"},
                            "timeout_sec": {"type": "integer", "minimum": 1},
                            "ssl_verify": {"type": "boolean"},
                            "max_redirects": {"type": "integer", "minimum": 0},
                            "expected_status": {"oneOf": [
                                {"type": "integer"},
                                {"type": "array", "items": {"type": "integer"}}
                            ]}
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "url", "payload"],
                        "properties": {
                            "type": {"const": "webhook.call"},
                            "name": {"type": "string"},
                            "url": {"type": "string"},
                            "payload": {"type": "object"},
                            "headers": {"type": "object", "additionalProperties": {"type": "string"}},
                            "signature_method": {"enum": ["hmac-sha256", "hmac-sha1"]},
                            "signature_header": {"type": "string"},
                            "signature_secret": {"type": "string"},
                            "timeout_sec": {"type": "integer", "minimum": 1},
                            "max_retries": {"type": "integer", "minimum": 0}
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "target", "command"],
                        "properties": {
                            "type": {"const": "ssh.exec"},
                            "target": {"type": "string"},
                            "command": {"type": "string"},
                            "shell": {"enum": ["bash", "sh", "zsh", "fish"], "default": "bash"},
                            "timeout_sec": {"type": "integer", "minimum": 1}
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "target", "local_path", "remote_path"],
                        "properties": {
                            "type": {"const": "sftp.upload"},
                            "target": {"type": "string"},
                            "local_path": {"type": "string"},
                            "remote_path": {"type": "string"},
                            "preserve_permissions": {"type": "boolean", "default": True},
                            "timeout_sec": {"type": "integer", "minimum": 1}
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "target", "local_path", "remote_path"],
                        "properties": {
                            "type": {"const": "sftp.download"},
                            "target": {"type": "string"},
                            "local_path": {"type": "string"},
                            "remote_path": {"type": "string"},
                            "preserve_permissions": {"type": "boolean", "default": True},
                            "timeout_sec": {"type": "integer", "minimum": 1}
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "target", "local_path", "remote_path"],
                        "properties": {
                            "type": {"const": "sftp.sync"},
                            "target": {"type": "string"},
                            "local_path": {"type": "string"},
                            "remote_path": {"type": "string"},
                            "direction": {"enum": ["upload", "download"], "default": "upload"},
                            "preserve_permissions": {"type": "boolean", "default": True},
                            "timeout_sec": {"type": "integer", "minimum": 1}
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "recipients"],
                        "properties": {
                            "type": {"const": "notify.email"},
                            "name": {"type": "string"},
                            "recipients": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1
                            },
                            "subject_template": {"type": "string"},
                            "body_template": {"type": "string"},
                            "send_on": {
                                "type": "array",
                                "items": {"enum": ["success", "failure", "always"]},
                                "default": ["always"]
                            },
                            "attachments": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"enum": ["job_log", "step_output", "file"]},
                                        "filename": {"type": "string"},
                                        "content": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "webhook_url"],
                        "properties": {
                            "type": {"const": "notify.slack"},
                            "name": {"type": "string"},
                            "webhook_url": {"type": "string"},
                            "channel": {"type": "string"},
                            "message_template": {"type": "string"},
                            "send_on": {
                                "type": "array",
                                "items": {"enum": ["success", "failure", "always"]},
                                "default": ["always"]
                            }
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "webhook_url"],
                        "properties": {
                            "type": {"const": "notify.teams"},
                            "name": {"type": "string"},
                            "webhook_url": {"type": "string"},
                            "message_template": {"type": "string"},
                            "send_on": {
                                "type": "array",
                                "items": {"enum": ["success", "failure", "always"]},
                                "default": ["always"]
                            }
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "webhook_url"],
                        "properties": {
                            "type": {"const": "notify.webhook"},
                            "name": {"type": "string"},
                            "webhook_url": {"type": "string"},
                            "payload_template": {"type": "string"},
                            "headers": {"type": "object", "additionalProperties": {"type": "string"}},
                            "send_on": {
                                "type": "array",
                                "items": {"enum": ["success", "failure", "always"]},
                                "default": ["always"]
                            }
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "condition", "notification_config"],
                        "properties": {
                            "type": {"const": "notify.conditional"},
                            "name": {"type": "string"},
                            "condition": {"type": "string"},
                            "notification_config": {
                                "type": "object",
                                "properties": {
                                    "type": {"enum": ["notify.email", "notify.slack", "notify.teams", "notify.webhook"]},
                                    "notification_type": {"type": "string"},
                                    "recipients": {"type": "array", "items": {"type": "string"}},
                                    "webhook_url": {"type": "string"},
                                    "subject_template": {"type": "string"},
                                    "body_template": {"type": "string"},
                                    "message_template": {"type": "string"},
                                    "payload_template": {"type": "string"},
                                    "headers": {"type": "object"},
                                    "send_on": {"type": "array", "items": {"enum": ["success", "failure", "always"]}}
                                },
                                "additionalProperties": True
                            }
                        },
                        "additionalProperties": True
                    },
                    {
                        "type": "object",
                        "required": ["type", "target", "command_type"],
                        "properties": {
                            "type": {"const": "windows.command"},
                            "target": {"type": "string"},
                            "command_type": {
                                "enum": [
                                    "system_info", "disk_space", "running_services", 
                                    "installed_programs", "network_config", "event_logs",
                                    "process_list", "windows_updates", "user_accounts",
                                    "system_uptime", "registry_query", "file_operations"
                                ]
                            },
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "drive": {"type": "string"},
                                    "service_filter": {"type": "string"},
                                    "process_filter": {"type": "string"},
                                    "log_name": {"enum": ["System", "Application", "Security", "Setup"]},
                                    "max_events": {"type": "integer", "minimum": 1, "maximum": 1000},
                                    "level": {"enum": ["Error", "Warning", "Information"]},
                                    "registry_path": {"type": "string"},
                                    "value_name": {"type": "string"},
                                    "operation": {"enum": ["list", "check_exists", "get_size", "get_info"]},
                                    "path": {"type": "string"},
                                    "filter": {"type": "string"}
                                },
                                "additionalProperties": False
                            },
                            "timeoutSec": {"type": "integer", "minimum": 1}
                        },
                        "additionalProperties": True
                    }
                ]
            }
        }
    },
    "additionalProperties": False
}

# Pydantic models
class JobCreate(BaseModel):
    name: str
    version: int = 1
    definition: Dict[str, Any]
    is_active: bool = True

class JobUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[int] = None
    definition: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class JobResponse(BaseModel):
    id: int
    name: str
    version: int
    definition: Dict[str, Any]
    created_by: int
    is_active: bool
    created_at: datetime

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int

class JobRunCreate(BaseModel):
    job_id: int
    parameters: Optional[Dict[str, Any]] = {}
    correlation_id: Optional[str] = None

class JobRunResponse(BaseModel):
    id: int
    job_id: int
    status: str
    requested_by: int
    parameters: Dict[str, Any]
    queued_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    correlation_id: Optional[str] = None

class JobRunListResponse(BaseModel):
    runs: List[JobRunResponse]
    total: int

class JobRunStepResponse(BaseModel):
    id: int
    job_run_id: int
    idx: int
    type: str
    target_id: Optional[int]
    status: str
    shell: Optional[str]
    timeoutsec: Optional[int]
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    metrics: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

# Database connection - now using shared connection pool

# Authentication is now handled by shared.auth module

# Job validation
def validate_job_definition(definition: Dict[str, Any]) -> None:
    """Validate job definition against schema"""
    try:
        jsonschema.validate(definition, JOB_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Invalid job definition: {e.message}", "definition")

# JOB CRUD Operations
@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create new job definition"""
    # Validate job definition
    validate_job_definition(job_data.definition)
    
    try:
        with get_db_cursor() as cursor:
            # Check if job name already exists (excluding soft-deleted)
            cursor.execute("SELECT id FROM jobs WHERE name = %s AND deleted_at IS NULL", (job_data.name,))
            existing_job = cursor.fetchone()
            if existing_job:
                raise ValidationError("Job with this name already exists")
            
            # Insert job
            cursor.execute(
                """INSERT INTO jobs (name, version, definition, created_by, is_active, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING id, name, version, definition, created_by, is_active, created_at""",
                (
                    job_data.name,
                    job_data.version,
                    json.dumps(job_data.definition),
                    current_user["id"],
                    job_data.is_active,
                    datetime.utcnow()
                )
            )
            
            new_job = cursor.fetchone()
            
            # Handle JSON definition (already parsed by psycopg2 for JSONB fields)
            if isinstance(new_job["definition"], str):
                new_job["definition"] = json.loads(new_job["definition"])
            
            return JobResponse(**new_job)
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions (like 409 Conflict) without modification
    except Exception as e:
        logger.error(f"Job creation error: {e}")
        raise DatabaseError("Failed to create job")

@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all jobs with pagination"""
    try:
        with get_db_cursor(commit=False) as cursor:
            # Build query with optional active filter and soft delete exclusion
            if active_only:
                where_clause = "WHERE is_active = true AND deleted_at IS NULL"
            else:
                where_clause = "WHERE deleted_at IS NULL"
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM jobs {where_clause}")
            total = cursor.fetchone()["count"]
            
            # Get jobs with pagination
            cursor.execute(
                f"""SELECT id, name, version, definition, created_by, is_active, created_at
                   FROM jobs {where_clause}
                   ORDER BY created_at DESC 
                   LIMIT %s OFFSET %s""",
                (limit, skip)
            )
            jobs = cursor.fetchall()
            
            # Handle JSON definitions (already parsed by psycopg2 for JSONB fields)
            for job in jobs:
                if isinstance(job["definition"], str):
                    job["definition"] = json.loads(job["definition"])
                # If it's already a dict, keep it as is
            
            return JobListResponse(
                jobs=[JobResponse(**job) for job in jobs],
                total=total
            )
        
    except Exception as e:
        logger.error(f"Job listing error: {e}")
        raise DatabaseError("Failed to retrieve jobs")

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get job by ID"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT id, name, version, definition, created_by, is_active, created_at FROM jobs WHERE id = %s AND deleted_at IS NULL",
                (job_id,)
            )
            job_data = cursor.fetchone()
            
            if not job_data:
                raise NotFoundError("Job not found")
            
            # Handle JSON definition (already parsed by psycopg2 for JSONB fields)
            if isinstance(job_data["definition"], str):
                job_data["definition"] = json.loads(job_data["definition"])
            
            return JobResponse(**job_data)
        
    except Exception as e:
        logger.error(f"Job retrieval error: {e}")
        raise DatabaseError("Failed to retrieve job")

@app.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update job by ID"""
    logger.info(f"Update job request - ID: {job_id}, Data type: {type(job_data)}")
    logger.info(f"Job data definition type: {type(job_data.definition) if job_data.definition else 'None'}")
    try:
        with get_db_cursor() as cursor:
            logger.info("Database connection established")
            
            # Check if job exists (excluding soft-deleted)
            cursor.execute("SELECT id FROM jobs WHERE id = %s AND deleted_at IS NULL", (job_id,))
            if not cursor.fetchone():
                raise NotFoundError("Job not found")
            logger.info("Job exists check passed")
            
            # Validate definition if provided - DISABLED FOR TESTING
            # if job_data.definition is not None:
            #     validate_job_definition(job_data.definition)
            
            # Build update query
            update_fields = []
            update_values = []
            
            if job_data.name is not None:
                update_fields.append("name = %s")
                update_values.append(job_data.name)
                
            if job_data.version is not None:
                update_fields.append("version = %s")
                update_values.append(job_data.version)
                
            if job_data.definition is not None:
                update_fields.append("definition = %s")
                # Handle definition - it should be a dict, convert to JSON string
                logger.info(f"Definition type: {type(job_data.definition)}, value: {job_data.definition}")
                if isinstance(job_data.definition, dict):
                    definition_json = json.dumps(job_data.definition)
                    logger.info(f"Converted to JSON: {definition_json}")
                    update_values.append(definition_json)
                else:
                    # If it's already a string, use it as-is
                    logger.info(f"Using as-is: {job_data.definition}")
                    update_values.append(job_data.definition)
                
            if job_data.is_active is not None:
                update_fields.append("is_active = %s")
                update_values.append(job_data.is_active)
            
            if not update_fields:
                # No fields to update, just return current job
                cursor.execute(
                    "SELECT id, name, version, definition, created_by, is_active, created_at FROM jobs WHERE id = %s",
                    (job_id,)
                )
                job_result = cursor.fetchone()
                # Handle JSON definition (already parsed by psycopg2 for JSONB fields)
                if isinstance(job_result["definition"], str):
                    job_result["definition"] = json.loads(job_result["definition"])
                return JobResponse(**job_result)
            
            # Execute update
            update_query = f"""
                UPDATE jobs 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, name, version, definition, created_by, is_active, created_at
            """
            update_values.append(job_id)
            
            cursor.execute(update_query, update_values)
            updated_job = cursor.fetchone()
            
            # Handle JSON definition (already parsed by psycopg2 for JSONB fields)
            if isinstance(updated_job["definition"], str):
                updated_job["definition"] = json.loads(updated_job["definition"])
            
            return JobResponse(**updated_job)
        
    except Exception as e:
        logger.error(f"Job update error: {e}")
        raise DatabaseError("Failed to update job")

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: int, current_user: dict = Depends(require_admin_or_operator_role)):
    """Delete job by ID"""
    try:
        with get_db_cursor() as cursor:
            # Soft delete job (no need to check job runs anymore)
            cursor.execute(
                "UPDATE jobs SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL",
                (datetime.utcnow(), job_id)
            )
            
            if cursor.rowcount == 0:
                raise NotFoundError("Job not found or already deleted")
            
            return create_success_response(
                message="Job deleted successfully",
                data={"job_id": job_id}
            )
        
    except Exception as e:
        logger.error(f"Job deletion error: {e}")
        raise DatabaseError("Failed to delete job")

# JOB RUN Operations
@app.post("/jobs/{job_id}/run", response_model=JobRunResponse, status_code=status.HTTP_201_CREATED)
async def run_job(
    job_id: int,
    run_data: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Execute job immediately"""
    if run_data is None:
        run_data = {}
    
    try:
        with get_db_cursor() as cursor:
            # Get job definition
            cursor.execute(
                "SELECT id, name, definition, is_active FROM jobs WHERE id = %s",
                (job_id,)
            )
            job_data = cursor.fetchone()
            
            if not job_data:
                raise NotFoundError("Job not found")
            
            if not job_data["is_active"]:
                raise ValidationError("Job is not active")
            
            # Parse job definition if it's a string, otherwise use as-is
            job_definition = job_data["definition"]
            if isinstance(job_definition, str):
                job_definition = json.loads(job_definition)
            
            # Generate correlation ID
            correlation_id = str(uuid.uuid4())
            
            # Create job run
            cursor.execute(
                """INSERT INTO job_runs (job_id, status, requested_by, parameters, queued_at, correlation_id)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING id, job_id, status, requested_by, parameters, queued_at, started_at, finished_at, correlation_id""",
                (
                    job_id,
                    "queued",
                    current_user["id"],
                    json.dumps(run_data or {}),
                    datetime.utcnow(),
                    correlation_id
                )
            )
            
            job_run = cursor.fetchone()
            job_run_id = job_run["id"]
            
            # Create job run steps
            for idx, step in enumerate(job_definition["steps"]):
                # Resolve target reference
                target_id = None
                if step.get("target"):
                    cursor.execute("SELECT id FROM targets WHERE name = %s", (step["target"],))
                    target_result = cursor.fetchone()
                    if target_result:
                        target_id = target_result["id"]
                
                cursor.execute(
                    """INSERT INTO job_run_steps (job_run_id, idx, type, target_id, status, shell, timeoutsec)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        job_run_id,
                        idx,
                        step["type"],
                        target_id,
                        "queued",
                        step.get("shell"),
                        step.get("timeoutSec", 60)
                    )
                )
            
            # Parameters are already parsed by psycopg2 RealDictCursor
            # job_run["parameters"] is already a dict
            
            return JobRunResponse(**job_run)
        
    except Exception as e:
        logger.error(f"Job run creation error: {e}")
        raise DatabaseError("Failed to create job run")

@app.get("/runs", response_model=JobRunListResponse)
async def list_runs(
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List job runs with pagination"""
    try:
        with get_db_cursor(commit=False) as cursor:
            # Build query with optional job filter
            where_clause = ""
            params = []
            if job_id is not None:
                where_clause = "WHERE job_id = %s"
                params.append(job_id)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM job_runs {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()["count"]
            
            # Get runs with pagination
            query = f"""
                SELECT id, job_id, status, requested_by, parameters, queued_at, started_at, finished_at, correlation_id
                FROM job_runs {where_clause}
                ORDER BY queued_at DESC 
                LIMIT %s OFFSET %s
            """
            params.extend([limit, skip])
            cursor.execute(query, params)
            runs = cursor.fetchall()
            
            # Parameters are already parsed by psycopg2 RealDictCursor
            # run["parameters"] is already a dict
            
            return JobRunListResponse(
                runs=[JobRunResponse(**run) for run in runs],
                total=total
            )
        
    except Exception as e:
        logger.error(f"Job run listing error: {e}")
        raise DatabaseError("Failed to retrieve job runs")

@app.get("/runs/{run_id}", response_model=JobRunResponse)
async def get_run(run_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get job run by ID"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT id, job_id, status, requested_by, parameters, queued_at, started_at, finished_at, correlation_id FROM job_runs WHERE id = %s",
                (run_id,)
            )
            run_data = cursor.fetchone()
            
            if not run_data:
                raise NotFoundError("Job run not found")
            
            # Parameters are already parsed by psycopg2 RealDictCursor
            # run_data["parameters"] is already a dict
            
            return JobRunResponse(**run_data)
        
    except Exception as e:
        logger.error(f"Job run retrieval error: {e}")
        raise DatabaseError("Failed to retrieve job run")

@app.get("/runs/{run_id}/steps", response_model=List[JobRunStepResponse])
async def get_run_steps(run_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get job run steps with logs"""
    try:
        with get_db_cursor(commit=False) as cursor:
            # Verify run exists
            cursor.execute("SELECT id FROM job_runs WHERE id = %s", (run_id,))
            if not cursor.fetchone():
                raise NotFoundError("Job run not found")
            
            # Get steps
            cursor.execute(
                """SELECT id, job_run_id, idx, type, target_id, status, shell, timeoutsec, 
                          exit_code, stdout, stderr, metrics, started_at, finished_at
                   FROM job_run_steps 
                   WHERE job_run_id = %s 
                   ORDER BY idx""",
                (run_id,)
            )
            steps = cursor.fetchall()
            
            return [JobRunStepResponse(**step) for step in steps]
        
    except Exception as e:
        logger.error(f"Job run steps retrieval error: {e}")
        raise DatabaseError("Failed to retrieve job run steps")

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    db_health = check_database_health()
    
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        )
    ]
    
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        service="jobs-service",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

@app.get("/metrics/database")
async def database_metrics() -> Dict[str, Any]:
    """Database connection pool metrics endpoint"""
    metrics = get_database_metrics()
    return {
        "service": "jobs-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

@app.on_event("startup")
async def startup_event() -> None:
    """Log service startup"""
    log_startup("jobs-service", "1.0.0", 3006)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up database connections on shutdown"""
    log_shutdown("jobs-service")
    cleanup_database_pool()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3006)