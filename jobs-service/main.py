#!/usr/bin/env python3
"""
Jobs Service - Python FastAPI Implementation
Job definition and execution management with full CRUD operations
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import psycopg2
import psycopg2.extras
import requests
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import jsonschema

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Jobs Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")

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
                        "additionalProperties": False
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
                        "additionalProperties": False
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

# Database connection
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

# Authentication
def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with auth service"""
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        return response.json()["user"]
        
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

def require_admin_or_operator_role(current_user: dict = Depends(verify_token_with_auth_service)):
    """Require admin or operator role"""
    if current_user["role"] not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or operator role required"
        )
    return current_user

# Job validation
def validate_job_definition(definition: Dict[str, Any]) -> None:
    """Validate job definition against schema"""
    try:
        jsonschema.validate(definition, JOB_SCHEMA)
    except jsonschema.ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job definition: {e.message}"
        )

# JOB CRUD Operations
@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create new job definition"""
    # Validate job definition
    validate_job_definition(job_data.definition)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if job name already exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM jobs WHERE name = %s AND deleted_at IS NULL", (job_data.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job with this name already exists"
            )
        
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
        conn.commit()
        
        # Handle JSON definition (already parsed by psycopg2 for JSONB fields)
        if isinstance(new_job["definition"], str):
            new_job["definition"] = json.loads(new_job["definition"])
        
        return JobResponse(**new_job)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Job creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )
    finally:
        conn.close()

@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List all jobs with pagination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )
    finally:
        conn.close()

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get job by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, version, definition, created_by, is_active, created_at FROM jobs WHERE id = %s AND deleted_at IS NULL",
            (job_id,)
        )
        job_data = cursor.fetchone()
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Handle JSON definition (already parsed by psycopg2 for JSONB fields)
        if isinstance(job_data["definition"], str):
            job_data["definition"] = json.loads(job_data["definition"])
        
        return JobResponse(**job_data)
        
    except Exception as e:
        logger.error(f"Job retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
        )
    finally:
        conn.close()

@app.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update job by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if job exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM jobs WHERE id = %s AND deleted_at IS NULL", (job_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Validate definition if provided
        if job_data.definition is not None:
            validate_job_definition(job_data.definition)
        
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
            update_values.append(json.dumps(job_data.definition))
            
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
        conn.commit()
        
        # Parse JSON definition
        updated_job["definition"] = json.loads(updated_job["definition"])
        
        return JobResponse(**updated_job)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Job update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job"
        )
    finally:
        conn.close()

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: int, current_user: dict = Depends(require_admin_or_operator_role)):
    """Delete job by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Soft delete job (no need to check job runs anymore)
        cursor.execute(
            "UPDATE jobs SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL",
            (datetime.utcnow(), job_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or already deleted"
            )
        
        conn.commit()
        
        return {"message": "Job deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Job deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )
    finally:
        conn.close()

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
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get job definition
        cursor.execute(
            "SELECT id, name, definition, is_active FROM jobs WHERE id = %s",
            (job_id,)
        )
        job_data = cursor.fetchone()
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        if not job_data["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job is not active"
            )
        
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
        
        conn.commit()
        
        # Parameters are already parsed by psycopg2 RealDictCursor
        # job_run["parameters"] is already a dict
        
        return JobRunResponse(**job_run)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Job run creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job run"
        )
    finally:
        conn.close()

@app.get("/runs", response_model=JobRunListResponse)
async def list_runs(
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List job runs with pagination"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job runs"
        )
    finally:
        conn.close()

@app.get("/runs/{run_id}", response_model=JobRunResponse)
async def get_run(run_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get job run by ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, job_id, status, requested_by, parameters, queued_at, started_at, finished_at, correlation_id FROM job_runs WHERE id = %s",
            (run_id,)
        )
        run_data = cursor.fetchone()
        
        if not run_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job run not found"
            )
        
        # Parameters are already parsed by psycopg2 RealDictCursor
        # run_data["parameters"] is already a dict
        
        return JobRunResponse(**run_data)
        
    except Exception as e:
        logger.error(f"Job run retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job run"
        )
    finally:
        conn.close()

@app.get("/runs/{run_id}/steps", response_model=List[JobRunStepResponse])
async def get_run_steps(run_id: int, current_user: dict = Depends(verify_token_with_auth_service)):
    """Get job run steps with logs"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify run exists
        cursor.execute("SELECT id FROM job_runs WHERE id = %s", (run_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job run not found"
            )
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job run steps"
        )
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "jobs-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3006)