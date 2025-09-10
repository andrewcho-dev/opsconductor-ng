#!/usr/bin/env python3
"""
Jobs Service - Visual Workflow Format Only
Complete rewrite to support only the visual node-based format
Includes export/import functionality
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import zipfile
import tempfile

import sys
sys.path.append('/home/opsconductor')

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator, Field
from dotenv import load_dotenv
import jsonschema

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool, get_database_metrics
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, PaginatedResponse, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error
from shared.auth import require_admin_role, get_user_from_request
# Job scheduling now handled by Celery tasks

# Import visual job schema
from visual_job_schema import VISUAL_JOB_SCHEMA, EXPORT_FORMAT_SCHEMA

# Load environment variables
load_dotenv()

# Setup structured logging
setup_service_logging("jobs-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("jobs-service")

# FastAPI app
app = FastAPI(
    title="Jobs Service - Visual Workflows", 
    version="2.0.0",
    description="Visual workflow job management service with export/import capabilities"
)

# Add standard middleware
add_standard_middleware(app, "jobs-service", version="2.0.0")

# Helper functions for header-based authentication
def get_user_from_headers(request: Request):
    """Extract user info from nginx headers (set by gateway authentication)"""
    return {
        "id": request.headers.get("X-User-ID"),
        "username": request.headers.get("X-Username"),
        "email": request.headers.get("X-User-Email"),
        "role": request.headers.get("X-User-Role")
    }

async def get_current_user(request: Request):
    """Get current user info (simplified - trust nginx gateway)"""
    # For internal services, provide default system user since nginx handles auth
    return {
        "id": 1,
        "user_id": 1,
        "username": "system",
        "email": "system@opsconductor.local",
        "role": "admin"
    }

# Database configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "opsconductor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres123")

# Pydantic Models
class VisualJobDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    version: int = Field(1, ge=1)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    nodes: List[Dict[str, Any]] = Field(..., min_items=1)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('nodes')
    def validate_nodes(cls, v):
        # Ensure at least one start node exists
        start_nodes = [node for node in v if node.get('type') == 'flow.start']
        if not start_nodes:
            raise ValueError('At least one flow.start node is required')
        
        # Validate unique node IDs
        node_ids = [node.get('id') for node in v]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError('Node IDs must be unique')
        
        return v

    @validator('edges')
    def validate_edges(cls, v, values):
        if 'nodes' not in values:
            return v
        
        node_ids = {node.get('id') for node in values['nodes']}
        
        # Validate edge references
        for edge in v:
            source = edge.get('source')
            target = edge.get('target')
            
            if source not in node_ids:
                raise ValueError(f'Edge source "{source}" references non-existent node')
            if target not in node_ids:
                raise ValueError(f'Edge target "{target}" references non-existent node')
        
        return v

class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    definition: VisualJobDefinition

class JobUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    definition: Optional[VisualJobDefinition] = None
    is_active: Optional[bool] = None

class JobResponse(BaseModel):
    id: int
    name: str
    version: int
    definition: Dict[str, Any]
    created_by: Optional[int]
    is_active: bool
    created_at: datetime

class JobExport(BaseModel):
    format_version: str = "1.0"
    export_timestamp: str
    export_metadata: Dict[str, Any]
    jobs: List[Dict[str, Any]]

# Utility Functions
def validate_job_definition(definition: Dict[str, Any]) -> None:
    """Validate job definition against visual schema"""
    try:
        jsonschema.validate(definition, VISUAL_JOB_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Invalid job definition: {e.message}")

# Legacy conversion removed - only visual format supported
# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    checks = [
        HealthCheck(name="database", status="healthy" if check_database_health() else "unhealthy")
    ]
    
    overall_status = "healthy" if all(check.status == "healthy" for check in checks) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        checks=checks,
        metrics=get_database_metrics()
    )

@app.get("/jobs", response_model=PaginatedResponse)
async def list_jobs(
    request: Request,
    page: int = 1,
    limit: int = 50,
    active_only: bool = True
):
    """List all jobs with pagination"""
    # Get user info from headers
    user_info = await get_user_from_request(request)
    try:
        offset = (page - 1) * limit
        
        with get_db_cursor() as cursor:
            # Count total jobs
            count_query = "SELECT COUNT(*) FROM jobs"
            count_params = []
            
            if active_only:
                count_query += " WHERE is_active = %s"
                count_params.append(True)
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['count']
            
            # Get jobs
            query = """
                SELECT j.id, j.name, j.version, j.definition, j.created_by, j.is_active, j.created_at,
                       u.username as created_by_username
                FROM jobs j
                LEFT JOIN users u ON j.created_by = u.id
            """
            params = []
            
            if active_only:
                query += " WHERE j.is_active = %s"
                params.append(True)
            
            query += " ORDER BY j.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            jobs = []
            for row in rows:
                definition = row['definition']
                
                # Only process visual format jobs
                if 'nodes' not in definition:
                    logger.warning(f"Skipping job {row['id']} - not in visual format")
                    continue
                
                jobs.append({
                    "id": row['id'],
                    "name": row['name'],
                    "version": row['version'],
                    "definition": definition,
                    "created_by": row['created_by'],
                    "created_by_username": row['created_by_username'],
                    "is_active": row['is_active'],
                    "created_at": row['created_at'].isoformat()
                })
            
            return PaginatedResponse.create(
                items=jobs,
                page=page,
                per_page=limit,
                total_items=total
            )
            
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise handle_database_error(e)

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    request: Request
):
    """Get a specific job by ID"""
    # Get user info from headers
    user_info = await get_user_from_request(request)
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT j.id, j.name, j.version, j.definition, j.created_by, j.is_active, j.created_at,
                       u.username as created_by_username
                FROM jobs j
                LEFT JOIN users u ON j.created_by = u.id
                WHERE j.id = %s
            """, (job_id,))
            
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Job {job_id} not found")
            
            definition = row['definition']
            
            # Only support visual format jobs
            if 'nodes' not in definition:
                raise NotFoundError(f"Job {job_id} is not in visual format")
            
            return JobResponse(
                id=row['id'],
                name=row['name'],
                version=row['version'],
                definition=definition,
                created_by=row['created_by'],
                is_active=row['is_active'],
                created_at=row['created_at']
            )
            
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise handle_database_error(e)

@app.post("/jobs", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    request: Request
):
    """Create a new visual workflow job"""
    # Get current user info
    user_info = await get_current_user(request)
    try:
        # Validate the job definition
        validate_job_definition(job.definition.dict())
        
        with get_db_cursor() as cursor:
            # Check if job name already exists
            cursor.execute("SELECT id FROM jobs WHERE name = %s", (job.name,))
            if cursor.fetchone():
                raise ValidationError(f"Job with name '{job.name}' already exists")
            
            # Insert new job
            cursor.execute("""
                INSERT INTO jobs (name, version, definition, created_by, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (
                job.name,
                job.definition.version,
                json.dumps(job.definition.dict()),
                user_info.get('user_id', user_info.get('id')),
                True,
                datetime.now(timezone.utc)
            ))
            
            result = cursor.fetchone()
            job_id, created_at = result['id'], result['created_at']
            
            logger.info(f"Created visual job {job_id}: {job.name}")
            
            return JobResponse(
                id=job_id,
                name=job.name,
                version=job.definition.version,
                definition=job.definition.dict(),
                created_by=user_info.get('user_id', user_info.get('id')),
                is_active=True,
                created_at=created_at
            )
            
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise handle_database_error(e)

@app.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    request: Request
):
    """Update an existing job"""
    # Get current user info
    user_info = await get_current_user(request)
    try:
        with get_db_cursor() as cursor:
            # Check if job exists
            cursor.execute("SELECT name, version, definition, created_by, is_active, created_at FROM jobs WHERE id = %s", (job_id,))
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Job {job_id} not found")
            
            current_name = row['name']
            current_version = row['version'] 
            current_definition = row['definition']
            created_by = row['created_by']
            is_active = row['is_active']
            created_at = row['created_at']
            
            # Prepare update data
            updates = []
            params = []
            
            if job_update.name is not None:
                # Check if new name conflicts with existing jobs
                cursor.execute("SELECT id FROM jobs WHERE name = %s AND id != %s", (job_update.name, job_id))
                if cursor.fetchone():
                    raise ValidationError(f"Job with name '{job_update.name}' already exists")
                updates.append("name = %s")
                params.append(job_update.name)
                current_name = job_update.name
            
            if job_update.definition is not None:
                # Validate the new definition
                validate_job_definition(job_update.definition.dict())
                updates.append("definition = %s, version = version + 1")
                params.append(json.dumps(job_update.definition.dict()))
                current_definition = job_update.definition.dict()
                current_version += 1
            
            if job_update.is_active is not None:
                updates.append("is_active = %s")
                params.append(job_update.is_active)
                is_active = job_update.is_active
            
            if not updates:
                # No changes, return current job
                return JobResponse(
                    id=job_id,
                    name=current_name,
                    version=current_version,
                    definition=current_definition,
                    created_by=created_by,
                    is_active=is_active,
                    created_at=created_at
                )
            
            # Perform update
            query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = %s RETURNING version"
            params.append(job_id)
            
            cursor.execute(query, params)
            new_version = cursor.fetchone()['version']
            
            logger.info(f"Updated job {job_id}: {current_name}")
            
            return JobResponse(
                id=job_id,
                name=current_name,
                version=new_version,
                definition=current_definition,
                created_by=created_by,
                is_active=is_active,
                created_at=created_at
            )
            
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise handle_database_error(e)

@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: int,
    request: Request
):
    """Delete a job (soft delete by setting is_active = false)"""
    # Get current user info
    user_info = await get_current_user(request)
    try:
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE jobs SET is_active = false WHERE id = %s RETURNING name", (job_id,))
            row = cursor.fetchone()
            
            if not row:
                raise NotFoundError(f"Job {job_id} not found")
            
            logger.info(f"Deleted job {job_id}: {row['name']}")
            
            return create_success_response(f"Job {job_id} deleted successfully")
            
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise handle_database_error(e)

# Job Run Models
class JobRunRequest(BaseModel):
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: Optional[str] = Field(default="normal")

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

@app.post("/jobs/{job_id}/run", response_model=JobRunResponse)
async def run_job(
    job_id: int,
    request: Request,
    run_request: Optional[JobRunRequest] = None
):
    """
    Execute a job immediately using Celery (Phase 2 Implementation)
    Creates a job run record and dispatches to Celery for execution
    """
    # Get user info from headers
    user_info = await get_user_from_request(request)
    try:
        if run_request is None:
            run_request = JobRunRequest()
            
        with get_db_cursor() as cursor:
            # Get job definition
            cursor.execute("""
                SELECT id, name, definition, is_active, created_by
                FROM jobs 
                WHERE id = %s AND is_active = true
            """, (job_id,))
            
            job_data = cursor.fetchone()
            if not job_data:
                raise NotFoundError(f"Job {job_id} not found or not active")
            
            # Validate job definition
            validate_job_definition(job_data['definition'])
            
            # Generate correlation ID
            correlation_id = str(uuid.uuid4())
            
            # Create job run record
            cursor.execute("""
                INSERT INTO job_runs (
                    job_id, status, requested_by, parameters, 
                    queued_at, correlation_id
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, job_id, status, requested_by, parameters, 
                         queued_at, started_at, finished_at, correlation_id
            """, (
                job_id,
                "queued",
                user_info.get('user_id', user_info.get('id')),
                json.dumps(run_request.parameters),
                datetime.now(timezone.utc),
                correlation_id
            ))
            
            job_run = cursor.fetchone()
            
            # Create job run steps from job definition
            job_definition = job_data['definition']
            steps = []
            
            if 'steps' in job_definition:
                # Traditional steps format
                steps = job_definition['steps']
            elif 'nodes' in job_definition and 'edges' in job_definition:
                # Visual workflow format - convert to steps
                steps = _convert_visual_workflow_to_steps(job_definition, run_request.parameters)
            
            if steps:
                for idx, step in enumerate(steps):
                    # Use target_relative_order if available, otherwise fall back to global index
                    step_idx = step.get('target_relative_order', idx)
                    
                    cursor.execute("""
                        INSERT INTO job_run_steps (
                            job_run_id, idx, type, target_id, shell, timeoutsec, status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        job_run["id"],
                        step_idx,
                        step.get('type', 'shell'),
                        step.get('target_id'),
                        step.get('shell', ''),
                        step.get('timeout', 60),
                        'queued'
                    ))
                
                logger.info(f"Created {len(steps)} steps for job run {job_run['id']}")
            else:
                logger.warning(f"No steps found in job definition for job {job_id}")
            
            # Prepare job run data for Celery
            job_run_data = {
                "id": job_run["id"],
                "job_id": job_run["job_id"],
                "job_definition": job_data["definition"],
                "parameters": run_request.parameters,
                "requested_by": job_run["requested_by"],
                "correlation_id": job_run["correlation_id"],
                "priority": run_request.priority
            }
            
            # Dispatch job execution to Celery
            from shared.tasks import execute_job_run
            from datetime import timedelta
            
            # Schedule job to run 1 minute from now using Celery
            scheduled_time = datetime.now(timezone.utc) + timedelta(minutes=1)
            
            # Use Celery's apply_async with eta for scheduling
            task_result = execute_job_run.apply_async(
                args=[job_run["id"], job_run_data],
                eta=scheduled_time,
                task_id=f"job_run_{job_run['id']}_{correlation_id}"
            )
            
            logger.info(f"Job run {job_run['id']} scheduled for Celery execution in 1 minute at {scheduled_time.isoformat()}, task_id: {task_result.id}")
            
            # Return job run response
            return JobRunResponse(
                id=job_run["id"],
                job_id=job_run["job_id"],
                status=job_run["status"],
                requested_by=job_run["requested_by"],
                parameters=run_request.parameters,
                queued_at=job_run["queued_at"],
                started_at=job_run["started_at"],
                finished_at=job_run["finished_at"],
                correlation_id=job_run["correlation_id"]
            )
            
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Error running job {job_id}: {e}")
        raise handle_database_error(e)

class ExportRequest(BaseModel):
    job_ids: Optional[List[int]] = None

@app.post("/jobs/export")
async def export_jobs(
    request: Request,
    export_request: Optional[ExportRequest] = None
):
    """Export jobs to downloadable format"""
    # Get user info from headers
    user_info = await get_user_from_request(request)
    try:
        job_ids = export_request.job_ids if export_request else None
        
        with get_db_cursor() as cursor:
            # Build query
            if job_ids:
                placeholders = ','.join(['%s'] * len(job_ids))
                query = f"""
                    SELECT id, name, version, definition, created_by, is_active, created_at
                    FROM jobs 
                    WHERE id IN ({placeholders}) AND is_active = true
                """
                params = job_ids
            else:
                query = """
                    SELECT id, name, version, definition, created_by, is_active, created_at
                    FROM jobs 
                    WHERE is_active = true
                """
                params = []
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                raise NotFoundError("No jobs found to export")
            
            # Convert jobs to export format
            jobs = []
            for row in rows:
                definition = row['definition']
                
                # Only export visual format jobs
                if 'nodes' not in definition:
                    logger.warning(f"Skipping job - not in visual format")
                    continue
                
                jobs.append(definition)
            
            # Create export data
            export_data = JobExport(
                export_timestamp=datetime.now(timezone.utc).isoformat(),
                export_metadata={
                    "exported_by": user_info.get('username', 'unknown'),
                    "opsconductor_version": "2.0.0",
                    "description": f"Export of {len(jobs)} visual workflow jobs",
                    "job_count": len(jobs)
                },
                jobs=jobs
            )
            
            # Validate export format
            jsonschema.validate(export_data.dict(), EXPORT_FORMAT_SCHEMA)
            
            # Create response
            export_json = json.dumps(export_data.dict(), indent=2, default=str)
            
            def generate():
                yield export_json.encode('utf-8')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"opsconductor_jobs_export_{timestamp}.json"
            
            return StreamingResponse(
                generate(),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error exporting jobs: {e}")
        raise handle_database_error(e)

@app.post("/jobs/import")
async def import_jobs(
    import_data: JobExport,
    request: Request
):
    """Import jobs from export format"""
    # Get current user info
    user_info = await get_current_user(request)
    try:
        # Validate import format
        jsonschema.validate(import_data.dict(), EXPORT_FORMAT_SCHEMA)
        
        imported_jobs = []
        failed_imports = []
        
        with get_db_cursor() as cursor:
            for job_data in import_data.jobs:
                try:
                    # Validate job definition
                    validate_job_definition(job_data)
                    
                    # Check if job with same name exists
                    cursor.execute("SELECT id FROM jobs WHERE name = %s AND is_active = true", (job_data['name'],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing job
                        cursor.execute("""
                            UPDATE jobs 
                            SET version = %s, definition = %s, created_by = %s, created_at = %s
                            WHERE id = %s
                            RETURNING id
                        """, (
                            job_data.get('version', 1),
                            json.dumps(job_data),
                            user_info.get('user_id', user_info.get('id')),
                            datetime.now(timezone.utc),
                            existing['id']
                        ))
                        job_id = existing['id']
                        action = "updated"
                    else:
                        # Create new job
                        cursor.execute("""
                            INSERT INTO jobs (name, version, definition, created_by, is_active, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            job_data['name'],
                            job_data.get('version', 1),
                            json.dumps(job_data),
                            user_info.get('user_id', user_info.get('id')),
                            True,
                            datetime.now(timezone.utc)
                        ))
                        job_id = cursor.fetchone()['id']
                        action = "created"
                    
                    imported_jobs.append({
                        "id": job_id,
                        "name": job_data['name'],
                        "action": action
                    })
                    
                    logger.info(f"Successfully {action} job: {job_data['name']} (ID: {job_id})")
                    
                except Exception as job_error:
                    logger.error(f"Failed to import job {job_data.get('name', 'unknown')}: {job_error}")
                    failed_imports.append({
                        "name": job_data.get('name', 'unknown'),
                        "error": str(job_error)
                    })
        
        # Create response
        result = {
            "imported_count": len(imported_jobs),
            "failed_count": len(failed_imports),
            "imported_jobs": imported_jobs,
            "failed_imports": failed_imports,
            "import_metadata": {
                "imported_by": user_info.get('username', 'unknown'),
                "import_timestamp": datetime.now(timezone.utc).isoformat(),
                "source_export_timestamp": import_data.export_timestamp,
                "source_format_version": import_data.format_version
            }
        }
        
        logger.info(f"Import completed: {len(imported_jobs)} successful, {len(failed_imports)} failed")
        
        return result
        
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Invalid import format: {e.message}")
    except Exception as e:
        logger.error(f"Error importing jobs: {e}")
        raise handle_database_error(e)

def _convert_visual_workflow_to_steps(workflow_definition: dict, parameters: dict) -> list:
    """
    Convert visual workflow format (nodes/edges) to traditional steps format using enhanced engine
    
    Args:
        workflow_definition: Visual workflow with nodes and edges
        parameters: Runtime parameters for template substitution
        
    Returns:
        List of step dictionaries
    """
    try:
        # Use the enhanced visual workflow engine
        from shared.visual_workflow_engine import workflow_engine
        
        execution_steps = workflow_engine.translate_workflow(workflow_definition, parameters)
        
        # Convert ExecutionStep objects to dictionary format expected by database
        steps = []
        for exec_step in execution_steps:
            step = {
                'type': exec_step.type,
                'shell': exec_step.command,
                'timeout': exec_step.timeout,
                'target_id': exec_step.target_id,
                'connection_type': exec_step.connection_type,
                'target_relative_order': exec_step.target_relative_order
            }
            
            # Add type-specific parameters
            if exec_step.type == 'shell':
                step.update({
                    'working_directory': exec_step.parameters.get('working_directory'),
                    'environment_variables': exec_step.parameters.get('environment_variables', {}),
                    'username': exec_step.parameters.get('username'),
                    'password': exec_step.parameters.get('password'),
                    'port': exec_step.parameters.get('port', 22),
                    'use_ssl': exec_step.parameters.get('use_ssl', False)
                })
            
            elif exec_step.type == 'http':
                step.update({
                    'method': exec_step.parameters.get('method', 'GET'),
                    'headers': exec_step.parameters.get('headers', {}),
                    'body': exec_step.parameters.get('body'),
                    'auth': exec_step.parameters.get('auth'),
                    'verify_ssl': exec_step.parameters.get('verify_ssl', True)
                })
            
            elif exec_step.type == 'file_transfer':
                step.update({
                    'source_path': exec_step.parameters.get('source_path'),
                    'dest_path': exec_step.parameters.get('dest_path'),
                    'direction': exec_step.parameters.get('direction', 'upload'),
                    'preserve_permissions': exec_step.parameters.get('preserve_permissions', True),
                    'recursive': exec_step.parameters.get('recursive', False)
                })
            
            elif exec_step.type == 'notification':
                step.update({
                    'notification_type': exec_step.parameters.get('notification_type', 'email'),
                    'recipients': exec_step.parameters.get('recipients', []),
                    'subject': exec_step.parameters.get('subject'),
                    'priority': exec_step.parameters.get('priority', 'normal')
                })
            
            # Add conditions and retry config if present
            if exec_step.conditions:
                step['conditions'] = exec_step.conditions
            
            if exec_step.retry_config:
                step['retry_config'] = exec_step.retry_config
            
            steps.append(step)
        
        logger.info(f"Enhanced workflow engine converted {len(steps)} steps")
        return steps
        
    except Exception as e:
        logger.error(f"Error converting visual workflow: {str(e)}")
        # Fallback to basic conversion for backward compatibility
        return _convert_visual_workflow_to_steps_basic(workflow_definition, parameters)

def _convert_visual_workflow_to_steps_basic(workflow_definition: dict, parameters: dict) -> list:
    """
    Basic fallback conversion for visual workflows
    """
    from jinja2 import Template
    
    nodes = workflow_definition.get('nodes', [])
    edges = workflow_definition.get('edges', [])
    
    # Find start node
    start_nodes = [node for node in nodes if node.get('type') == 'flow.start']
    if not start_nodes:
        return []
    
    # Build execution order by following edges from start
    execution_order = []
    current_node_id = start_nodes[0]['id']
    visited = set()
    
    while current_node_id and current_node_id not in visited:
        visited.add(current_node_id)
        
        # Find current node
        current_node = next((node for node in nodes if node['id'] == current_node_id), None)
        if not current_node:
            break
            
        # Skip start and end nodes
        if current_node.get('type') not in ['flow.start', 'flow.end']:
            execution_order.append(current_node)
        
        # Find next node via edges
        next_edge = next((edge for edge in edges if edge['source'] == current_node_id), None)
        current_node_id = next_edge['target'] if next_edge else None
    
    # Convert nodes to steps
    steps = []
    for node in execution_order:
        node_data = node.get('data', {})
        node_type = node.get('type', '')
        
        if node_type == 'action.command':
            # Convert command node to shell step
            command = node_data.get('command', '')
            target_host = node_data.get('target', '')
            
            # Apply parameter substitution
            if command and parameters:
                try:
                    command_template = Template(command)
                    command = command_template.render(**parameters)
                except Exception as e:
                    logger.warning(f"Failed to render command template: {e}")
            
            if target_host and parameters:
                try:
                    target_template = Template(target_host)
                    target_host = target_template.render(**parameters)
                except Exception as e:
                    logger.warning(f"Failed to render target template: {e}")
            
            step = {
                'type': 'shell',
                'shell': command,
                'timeout': node_data.get('timeout', 60),
                'target_host': target_host,
                'connection_type': node_data.get('connection_type', 'ssh')
            }
            
            # Add connection details for WinRM
            if node_data.get('connection_type') == 'winrm':
                step.update({
                    'username': node_data.get('username', ''),
                    'password': node_data.get('password', ''),
                    'port': node_data.get('port', 5985),
                    'use_ssl': node_data.get('use_ssl', False)
                })
                
                # Apply parameter substitution to connection details
                if parameters:
                    for field in ['username', 'password']:
                        if step.get(field):
                            try:
                                template = Template(step[field])
                                step[field] = template.render(**parameters)
                            except Exception as e:
                                logger.warning(f"Failed to render {field} template: {e}")
            
            steps.append(step)
    
    return steps

# Job Runs API endpoints
@app.get("/runs")
async def list_job_runs(
    request: Request,
    skip: int = 0, 
    limit: int = 100, 
    job_id: Optional[int] = None
):
    """List job runs with pagination and optional filtering by job_id"""
    # Get user info from headers
    user_info = await get_user_from_request(request)
    try:
        with get_db_cursor() as cursor:
            # Build query based on filters
            where_conditions = []
            params = []
            
            if job_id is not None:
                where_conditions.append("job_id = %s")
                params.append(job_id)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM job_runs {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['count']
            
            # Get runs with pagination
            query = f"""
                SELECT jr.*, j.name as job_name
                FROM job_runs jr
                LEFT JOIN jobs j ON jr.job_id = j.id
                {where_clause}
                ORDER BY jr.queued_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, skip])
            cursor.execute(query, params)
            runs = cursor.fetchall()
            
            # Calculate page number from skip/limit
            page = (skip // limit) + 1 if limit > 0 else 1
            
            return PaginatedResponse.create(
                items=runs,
                page=page,
                per_page=limit,
                total_items=total
            )
            
    except Exception as e:
        logger.error(f"Error listing job runs: {e}")
        raise handle_database_error(e)

@app.get("/runs/{run_id}")
async def get_job_run(
    run_id: int,
    request: Request
):
    """Get a specific job run by ID"""
    # Get user info from headers
    user_info = await get_user_from_request(request)
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT jr.*, j.name as job_name, j.definition as job_definition
                FROM job_runs jr
                LEFT JOIN jobs j ON jr.job_id = j.id
                WHERE jr.id = %s
            """
            cursor.execute(query, [run_id])
            run = cursor.fetchone()
            
            if not run:
                raise NotFoundError(f"Job run {run_id} not found")
            
            return run
            
    except Exception as e:
        logger.error(f"Error getting job run {run_id}: {e}")
        raise handle_database_error(e)

@app.get("/runs/{run_id}/steps")
async def get_job_run_steps(
    run_id: int,
    request: Request
):
    """Get all steps for a specific job run"""
    # Get user info from headers
    user_info = await get_user_from_request(request)
    try:
        with get_db_cursor() as cursor:
            # First verify the run exists
            cursor.execute("SELECT id FROM job_runs WHERE id = %s", [run_id])
            if not cursor.fetchone():
                raise NotFoundError(f"Job run {run_id} not found")
            
            # Get all steps for this run
            query = """
                SELECT *
                FROM job_run_steps
                WHERE job_run_id = %s
                ORDER BY idx ASC
            """
            cursor.execute(query, [run_id])
            steps = cursor.fetchall()
            
            return steps
            
    except Exception as e:
        logger.error(f"Error getting steps for job run {run_id}: {e}")
        raise handle_database_error(e)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    log_startup("jobs-service", "2.0.0", 3006)
    # Celery handles job scheduling - no additional initialization needed
    logger.info("Job scheduling via Celery is ready")
    logger.info("Jobs Service (Visual Workflows) started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    cleanup_database_pool()
    log_shutdown("jobs-service")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3006)