#!/usr/bin/env python3
"""
OpsConductor Automation Service
Handles jobs, workflows, and execution
Consolidates: jobs-service + executor-service
"""

import sys
import os
import json
from typing import List, Optional
from fastapi import Query, HTTPException, status, WebSocket
from pydantic import BaseModel
from datetime import datetime
sys.path.append('/app/shared')
from base_service import BaseService
from celery_monitor import CeleryMonitor

# ============================================================================
# STATUS CONSTANTS AND UTILITIES
# ============================================================================

class JobExecutionStatus:
    """Enhanced job execution status constants"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED_SUCCESS = "completed_success"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    @classmethod
    def is_terminal_status(cls, status: str) -> bool:
        """Check if status indicates job has finished (terminal state)"""
        return status in [cls.COMPLETED_SUCCESS, cls.COMPLETED_WITH_ERRORS, cls.FAILED, cls.CANCELLED]
    
    @classmethod
    def is_successful_completion(cls, status: str) -> bool:
        """Check if status indicates successful completion"""
        return status == cls.COMPLETED_SUCCESS
    
    @classmethod
    def has_errors(cls, status: str) -> bool:
        """Check if status indicates completion with errors"""
        return status == cls.COMPLETED_WITH_ERRORS
    
    @classmethod
    def get_status_description(cls, status: str) -> str:
        """Get human-readable description of status"""
        descriptions = {
            cls.PENDING: "Job is queued and waiting to start",
            cls.QUEUED: "Job is queued for execution",
            cls.RUNNING: "Job is currently executing",
            cls.COMPLETED_SUCCESS: "Job completed successfully with all steps successful",
            cls.COMPLETED_WITH_ERRORS: "Job completed but some steps failed",
            cls.FAILED: "Job failed to complete due to system error",
            cls.CANCELLED: "Job was manually cancelled"
        }
        return descriptions.get(status, f"Unknown status: {status}")

# ============================================================================
# MODELS
# ============================================================================

class Job(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    workflow_definition: dict = {}
    schedule_expression: Optional[str] = None
    is_enabled: bool
    tags: List[str] = []
    metadata: dict = {}
    job_type: str = "general"
    created_by: int
    updated_by: int
    created_at: str
    updated_at: str

class JobCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_definition: dict = {}
    schedule_expression: Optional[str] = None
    is_enabled: bool = True
    tags: List[str] = []
    metadata: dict = {}
    job_type: str = "general"

class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_definition: Optional[dict] = None
    schedule_expression: Optional[str] = None
    is_enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    job_type: Optional[str] = None

class JobListResponse(BaseModel):
    jobs: List[Job]
    total: int
    skip: int
    limit: int

class JobExecution(BaseModel):
    id: int
    job_id: int
    job_name: str
    execution_id: str
    status: str
    trigger_type: str
    input_data: dict = {}
    output_data: dict = {}
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    started_by: Optional[int] = None
    created_at: str
    
    # Enhanced status information
    @property
    def status_description(self) -> str:
        """Get human-readable status description"""
        return JobExecutionStatus.get_status_description(self.status)
    
    @property
    def is_terminal(self) -> bool:
        """Check if execution has finished"""
        return JobExecutionStatus.is_terminal_status(self.status)
    
    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully"""
        return JobExecutionStatus.is_successful_completion(self.status)
    
    @property
    def has_errors(self) -> bool:
        """Check if execution completed with errors"""
        return JobExecutionStatus.has_errors(self.status)

class ExecutionCreate(BaseModel):
    job_id: int
    trigger_type: str = "manual"
    input_data: dict = {}

class ExecutionUpdate(BaseModel):
    status: Optional[str] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None

class ExecutionListResponse(BaseModel):
    executions: List[JobExecution]
    total: int
    skip: int
    limit: int

class StepExecution(BaseModel):
    id: int
    job_execution_id: int
    step_id: str
    step_name: str
    step_type: str
    status: str
    input_data: dict = {}
    output_data: dict = {}
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_order: int



class JobExportRequest(BaseModel):
    job_ids: List[int]
    include_executions: bool = False
    include_metadata: bool = True

class JobImportRequest(BaseModel):
    jobs_data: dict
    overwrite_existing: bool = False
    import_executions: bool = False

class JobSchedule(BaseModel):
    id: int
    job_id: int
    job_name: str
    schedule_type: str
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    is_active: bool
    next_run: Optional[str] = None
    created_by: int
    created_at: str
    updated_at: str

class ScheduleCreate(BaseModel):
    job_id: int
    schedule_expression: str
    timezone: str = "UTC"
    is_active: bool = True

class ScheduleUpdate(BaseModel):
    schedule_expression: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None

class ScheduleListResponse(BaseModel):
    schedules: List[JobSchedule]
    total: int
    skip: int
    limit: int

class AutomationService(BaseService):
    def __init__(self):
        super().__init__("automation-service", "1.0.0", 3003)
        # Initialize Celery monitor
        self.monitor = CeleryMonitor()
    
    async def setup_service_dependencies(self):
        """Setup automation service specific dependencies"""
        # Identity service dependency
        identity_url = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:3001")
        self.startup_manager.add_service_dependency(
            "identity-service",
            identity_url,
            endpoint="/ready",
            timeout=60,
            critical=True
        )
        
        # Asset service dependency
        asset_url = os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002")
        self.startup_manager.add_service_dependency(
            "asset-service",
            asset_url,
            endpoint="/ready",
            timeout=60,
            critical=True
        )
    
    def _get_current_user_id(self) -> int:
        """Get current user ID from authentication context
        For now returns 1, but should be replaced with proper auth"""
        # TODO: Implement proper authentication context
        return 1
    
    def _parse_json_field(self, value, default=None):
        """Helper to parse JSON fields that might be strings or already parsed"""
        if value is None:
            return default or {}
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return default or {}
        return value
    
    async def on_startup(self):
        """Set the database schema to automation"""
        print("AUTOMATION SERVICE STARTUP CALLED")  # Debug print
        self.logger.info("AUTOMATION SERVICE STARTUP CALLED")
        os.environ["DB_SCHEMA"] = "automation"
        
        # Setup routes
        self._setup_routes()
        self._setup_monitoring_routes()
        
        # Start the Celery monitor
        self.logger.info("About to start Celery monitoring...")
        try:
            await self.monitor.start_monitoring()
            self.logger.info("Celery monitoring started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _setup_routes(self):
        self.logger.info("Starting route setup...")
        @self.app.get("/jobs", response_model=JobListResponse)
        async def list_jobs(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000),
            job_type: Optional[str] = Query(None, description="Filter by job type")
        ):
            """List all jobs"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build WHERE clause for job_type filter
                    where_clause = ""
                    count_params = []
                    query_params = []
                    
                    if job_type:
                        where_clause = "WHERE job_type = $1"
                        count_params = [job_type]
                        query_params = [job_type, limit, skip]
                    else:
                        query_params = [limit, skip]
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM automation.jobs {where_clause}"
                    total = await conn.fetchval(count_query, *count_params)
                    
                    # Get jobs with pagination
                    if job_type:
                        rows = await conn.fetch("""
                            SELECT id, name, description, workflow_definition, schedule_expression,
                                   is_enabled, tags, metadata, job_type, created_by, updated_by, created_at, updated_at
                            FROM automation.jobs 
                            WHERE job_type = $1
                            ORDER BY created_at DESC 
                            LIMIT $2 OFFSET $3
                        """, *query_params)
                    else:
                        rows = await conn.fetch("""
                            SELECT id, name, description, workflow_definition, schedule_expression,
                                   is_enabled, tags, metadata, job_type, created_by, updated_by, created_at, updated_at
                            FROM automation.jobs 
                            ORDER BY created_at DESC 
                            LIMIT $1 OFFSET $2
                        """, *query_params)
                    
                    jobs = []
                    for row in rows:
                        jobs.append(Job(
                            id=row['id'],
                            name=row['name'],
                            description=row['description'],
                            workflow_definition=json.loads(row['workflow_definition']) if row['workflow_definition'] else {},
                            schedule_expression=row['schedule_expression'],
                            is_enabled=row['is_enabled'],
                            tags=json.loads(row['tags']) if row['tags'] else [],
                            metadata=json.loads(row['metadata']) if row['metadata'] else {},
                            job_type=row['job_type'],
                            created_by=row['created_by'],
                            updated_by=row['updated_by'],
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return JobListResponse(
                        jobs=jobs,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch jobs", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch jobs"
                )

        @self.app.post("/jobs", response_model=dict)
        async def create_job(job_data: JobCreate):
            """Create a new job with workflow complexity validation"""
            try:
                # ============================================================================
                # AUTOMATION JOB VALIDATION - Prevent invalid and resource-exhausting jobs
                # ============================================================================
                
                workflow_def = job_data.workflow_definition or {}
                
                # Validation 1: Ensure workflow has meaningful content
                steps = workflow_def.get('steps', [])
                nodes = workflow_def.get('nodes', [])
                total_steps = len(steps) + len(nodes)
                
                # Prevent empty workflows from being created (except for specific job types)
                if total_steps == 0 and job_data.job_type not in ['template', 'placeholder']:
                    self.logger.error(f"Empty workflow rejected for job type '{job_data.job_type}'")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Workflow definition cannot be empty. Please add at least one step or node."
                    )
                
                # Validation 2: Validate step structure for non-empty workflows
                if total_steps > 0:
                    invalid_steps = []
                    for i, step in enumerate(steps + nodes):
                        step_id = step.get('id', f'step_{i}')
                        step_name = step.get('name', '')
                        library_name = step.get('library')
                        function_name = step.get('function')
                        command = step.get('command')
                        
                        # Each step must have either library+function or command
                        if not ((library_name and function_name) or command):
                            invalid_steps.append(f"Step '{step_id}' ({step_name}) has no executable action (missing library+function or command)")
                    
                    if invalid_steps:
                        self.logger.error(f"Invalid steps found: {invalid_steps}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid workflow steps: {'; '.join(invalid_steps)}"
                        )
                
                # Limit 3: Maximum workflow steps (prevents infinite loops and memory issues)
                max_steps = 100
                if total_steps > max_steps:
                    self.logger.error(f"Workflow too complex: {total_steps} steps exceeds limit of {max_steps}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Workflow too complex: {total_steps} steps exceeds maximum of {max_steps} steps"
                    )
                
                # Limit 2: Maximum workflow depth (prevents deep recursion)
                max_depth = 20
                workflow_depth = self._calculate_workflow_depth(workflow_def)
                
                if workflow_depth > max_depth:
                    self.logger.error(f"Workflow too deep: {workflow_depth} levels exceeds limit of {max_depth}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Workflow too deep: {workflow_depth} levels exceeds maximum of {max_depth} levels"
                    )
                
                # Limit 3: Maximum parallel branches (prevents worker exhaustion)
                max_parallel = 10
                parallel_branches = self._count_parallel_branches(workflow_def)
                
                if parallel_branches > max_parallel:
                    self.logger.error(f"Too many parallel branches: {parallel_branches} exceeds limit of {max_parallel}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Too many parallel branches: {parallel_branches} exceeds maximum of {max_parallel}"
                    )
                
                # Limit 4: Maximum loop iterations (prevents infinite loops)
                max_iterations = 1000
                total_iterations = self._estimate_loop_iterations(workflow_def)
                
                if total_iterations > max_iterations:
                    self.logger.error(f"Too many loop iterations: {total_iterations} exceeds limit of {max_iterations}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Estimated loop iterations {total_iterations} exceeds maximum of {max_iterations}"
                    )
                
                self.logger.info(f"Workflow validation passed: {total_steps} steps, {workflow_depth} depth, {parallel_branches} parallel, {total_iterations} iterations")
                
                async with self.db.pool.acquire() as conn:

                    row = await conn.fetchrow("""
                        INSERT INTO automation.jobs (name, description, workflow_definition, 
                                                   schedule_expression, is_enabled, tags, metadata, job_type,
                                                   created_by, updated_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        RETURNING id, name, description, workflow_definition, schedule_expression,
                                  is_enabled, tags, metadata, job_type, created_by, updated_by, created_at, updated_at
                    """, job_data.name, job_data.description, json.dumps(job_data.workflow_definition or {}),
                         job_data.schedule_expression, job_data.is_enabled, json.dumps(job_data.tags or []),
                         json.dumps(job_data.metadata or {}), job_data.job_type, 
                         self._get_current_user_id(), self._get_current_user_id())
                    

                    job = Job(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        workflow_definition=json.loads(row['workflow_definition']) if row['workflow_definition'] else {},
                        schedule_expression=row['schedule_expression'],
                        is_enabled=row['is_enabled'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        job_type=row['job_type'],
                        created_by=row['created_by'],
                        updated_by=row['updated_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Job created", "data": job}
            except Exception as e:
                self.logger.error("Failed to create job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create job"
                )

        @self.app.get("/jobs/{job_id}", response_model=dict)
        async def get_job(job_id: int):
            """Get job by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, name, description, workflow_definition, schedule_expression,
                               is_enabled, tags, metadata, job_type, created_by, updated_by, created_at, updated_at
                        FROM automation.jobs WHERE id = $1
                    """, job_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Job not found")
                    

                    job = Job(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        workflow_definition=json.loads(row['workflow_definition']) if row['workflow_definition'] else {},
                        schedule_expression=row['schedule_expression'],
                        is_enabled=row['is_enabled'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        job_type=row['job_type'],
                        created_by=row['created_by'],
                        updated_by=row['updated_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat()
                    )
                    
                    return {"success": True, "data": job}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get job"
                )

        @self.app.put("/jobs/{job_id}", response_model=dict)
        async def update_job(job_id: int, job_data: JobUpdate):
            """Update job with workflow validation"""
            try:
                # ============================================================================
                # VALIDATE WORKFLOW UPDATES - Prevent dangerous modifications
                # ============================================================================
                
                if job_data.workflow_definition is not None:
                    workflow_def = job_data.workflow_definition
                    
                    # Apply same validation as job creation
                    steps = workflow_def.get('steps', [])
                    nodes = workflow_def.get('nodes', [])
                    total_steps = len(steps) + len(nodes)
                    
                    if total_steps > 100:
                        self.logger.error(f"Workflow update rejected: {total_steps} steps exceeds limit of 100")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Workflow update rejected: {total_steps} steps exceeds maximum of 100 steps"
                        )
                    
                    workflow_depth = self._calculate_workflow_depth(workflow_def)
                    if workflow_depth > 20:
                        self.logger.error(f"Workflow update rejected: {workflow_depth} depth exceeds limit of 20")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Workflow update rejected: {workflow_depth} levels exceeds maximum of 20 levels"
                        )
                    
                    parallel_branches = self._count_parallel_branches(workflow_def)
                    if parallel_branches > 10:
                        self.logger.error(f"Workflow update rejected: {parallel_branches} parallel branches exceeds limit of 10")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Workflow update rejected: {parallel_branches} parallel branches exceeds maximum of 10"
                        )
                    
                    total_iterations = self._estimate_loop_iterations(workflow_def)
                    if total_iterations > 1000:
                        self.logger.error(f"Workflow update rejected: {total_iterations} iterations exceeds limit of 1000")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Workflow update rejected: estimated {total_iterations} iterations exceeds maximum of 1000"
                        )
                    
                    self.logger.info(f"Workflow update validation passed: {total_steps} steps, {workflow_depth} depth, {parallel_branches} parallel, {total_iterations} iterations")
                
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if job_data.name is not None:
                        updates.append(f"name = ${param_count}")
                        values.append(job_data.name)
                        param_count += 1
                    if job_data.description is not None:
                        updates.append(f"description = ${param_count}")
                        values.append(job_data.description)
                        param_count += 1
                    if job_data.workflow_definition is not None:
    
                        updates.append(f"workflow_definition = ${param_count}")
                        values.append(json.dumps(job_data.workflow_definition))
                        param_count += 1
                    if job_data.schedule_expression is not None:
                        updates.append(f"schedule_expression = ${param_count}")
                        values.append(job_data.schedule_expression)
                        param_count += 1
                    if job_data.is_enabled is not None:
                        updates.append(f"is_enabled = ${param_count}")
                        values.append(job_data.is_enabled)
                        param_count += 1
                    if job_data.tags is not None:
                        updates.append(f"tags = ${param_count}")
                        values.append(job_data.tags)
                        param_count += 1
                    if job_data.metadata is not None:
                        updates.append(f"metadata = ${param_count}")
                        values.append(job_data.metadata)
                        param_count += 1
                    if job_data.job_type is not None:
                        updates.append(f"job_type = ${param_count}")
                        values.append(job_data.job_type)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    updates.append(f"updated_by = ${param_count}")
                    values.append(1)
                    param_count += 1
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    values.append(job_id)
                    
                    query = f"""
                        UPDATE automation.jobs 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, name, description, workflow_definition, schedule_expression,
                                  is_enabled, tags, metadata, job_type, created_by, updated_by, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Job not found")
                    

                    job = Job(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        workflow_definition=json.loads(row['workflow_definition']) if row['workflow_definition'] else {},
                        schedule_expression=row['schedule_expression'],
                        is_enabled=row['is_enabled'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        job_type=row['job_type'],
                        created_by=row['created_by'],
                        updated_by=row['updated_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Job updated", "data": job}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update job"
                )

        @self.app.delete("/jobs/{job_id}", response_model=dict)
        async def delete_job(job_id: int):
            """Delete job"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM automation.jobs WHERE id = $1", job_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Job not found")
                    
                    return {"success": True, "message": "Job deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete job"
                )

        @self.app.post("/jobs/{job_id}/run", response_model=dict)
        async def run_job(job_id: int, input_data: dict = None):
            """Execute a job immediately with runtime validation"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get job details
                    job_row = await conn.fetchrow(
                        "SELECT id, name, workflow_definition FROM automation.jobs WHERE id = $1 AND is_enabled = true",
                        job_id
                    )
                    
                    if not job_row:
                        raise HTTPException(status_code=404, detail="Job not found or disabled")
                    
                    # ============================================================================
                    # RUNTIME VALIDATION - Re-validate workflow before execution
                    # ============================================================================
                    

                    workflow_def = json.loads(job_row['workflow_definition']) if job_row['workflow_definition'] else {}
                    
                    # Re-validate workflow complexity at runtime (in case job was modified)
                    steps = workflow_def.get('steps', [])
                    nodes = workflow_def.get('nodes', [])
                    total_steps = len(steps) + len(nodes)
                    
                    if total_steps > 100:
                        self.logger.error(f"Runtime validation failed: {total_steps} steps exceeds limit")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Cannot execute: workflow has {total_steps} steps (max 100)"
                        )
                    
                    workflow_depth = self._calculate_workflow_depth(workflow_def)
                    if workflow_depth > 20:
                        self.logger.error(f"Runtime validation failed: {workflow_depth} depth exceeds limit")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Cannot execute: workflow depth {workflow_depth} exceeds maximum of 20"
                        )
                    
                    self.logger.info(f"Runtime validation passed for job {job_id}: {total_steps} steps, {workflow_depth} depth")
                    
                    # Queue the job for execution using Celery first to get task ID
                    from worker import execute_job
                    task = execute_job.delay(
                        job_id=job_id,
                        workflow_definition=job_row['workflow_definition'],
                        input_data=input_data or {}
                    )
                    
                    # Use Celery task ID as execution_id for proper tracking
                    execution_id = task.id
                    
                    # Store execution record with Celery task_id as execution_id
                    execution_row = await conn.fetchrow("""
                        INSERT INTO automation.job_executions 
                        (job_id, execution_id, status, trigger_type, input_data, started_by, created_at)
                        VALUES ($1, $2, 'queued', 'manual', $3, 1, NOW())
                        RETURNING id
                    """, job_id, execution_id, json.dumps(input_data or {}))
                    
                    return {
                        "success": True,
                        "message": "Job execution started",
                        "data": {
                            "execution_id": execution_id,
                            "job_id": job_id,
                            "job_name": job_row['name'],
                            "task_id": task.id,
                            "status": "queued",
                            "status_url": f"/tasks/{task.id}/status",
                            "job_status_url": f"/jobs/{job_id}/status/{task.id}"
                        }
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to run job", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to run job"
                )

        @self.app.get("/jobs/{job_id}/status/{task_id}", response_model=dict)
        async def get_job_status(job_id: int, task_id: str):
            """Get job execution status directly from Celery"""
            try:
                from celery import Celery
                from worker import execute_job
                
                # Get the Celery app instance
                celery_app = execute_job.app
                
                # Get task result directly from Celery
                task_result = celery_app.AsyncResult(task_id)
                
                # Get basic task info
                status = task_result.status
                result = task_result.result
                traceback = task_result.traceback
                
                # Format the response
                response_data = {
                    "job_id": job_id,
                    "task_id": task_id,
                    "status": status,
                    "result": result,
                    "traceback": traceback,
                    "ready": task_result.ready(),
                    "successful": task_result.successful() if task_result.ready() else None,
                    "failed": task_result.failed() if task_result.ready() else None
                }
                
                # Add additional info if available
                if hasattr(task_result, 'info') and task_result.info:
                    response_data["info"] = task_result.info
                
                return {
                    "success": True,
                    "data": response_data
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get job status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get job status: {str(e)}"
                )

        @self.app.get("/tasks/{task_id}/status", response_model=dict)
        async def get_task_status(task_id: str):
            """Get task status directly from Celery (simplified)"""
            try:
                from celery import Celery
                from worker import execute_job
                
                # Get the Celery app instance
                celery_app = execute_job.app
                
                # Get task result directly from Celery
                task_result = celery_app.AsyncResult(task_id)
                
                return {
                    "task_id": task_id,
                    "status": task_result.status,
                    "result": task_result.result,
                    "traceback": task_result.traceback,
                    "ready": task_result.ready(),
                    "successful": task_result.successful() if task_result.ready() else None,
                    "failed": task_result.failed() if task_result.ready() else None,
                    "info": getattr(task_result, 'info', None)
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get task status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get task status: {str(e)}"
                )

        @self.app.get("/jobs/{job_id}/execution-status", response_model=dict)
        async def get_job_execution_status(job_id: int):
            """Get the latest execution status for a job (simplified for UI)"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get the most recent execution for this job
                    execution_row = await conn.fetchrow("""
                        SELECT job_id, execution_id, status, trigger_type, input_data, 
                               started_at, completed_at, created_at
                        FROM automation.job_executions 
                        WHERE job_id = $1 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """, job_id)
                    
                    if not execution_row:
                        return {
                            "job_id": job_id,
                            "status": "never_run",
                            "message": "Job has never been executed"
                        }
                    
                    # If we have a recent execution, we can try to get its Celery status
                    # For now, just return the database status
                    return {
                        "job_id": job_id,
                        "execution_id": execution_row['execution_id'],
                        "status": execution_row['status'],
                        "trigger_type": execution_row['trigger_type'],
                        "started_at": execution_row['started_at'].isoformat() if execution_row['started_at'] else None,
                        "completed_at": execution_row['completed_at'].isoformat() if execution_row['completed_at'] else None,
                        "created_at": execution_row['created_at'].isoformat(),
                        "message": f"Last execution: {execution_row['status']}"
                    }
                    
            except Exception as e:
                self.logger.error(f"Failed to get job execution status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get job execution status: {str(e)}"
                )

        @self.app.post("/jobs/export", response_model=dict)
        async def export_jobs(export_request: JobExportRequest):
            """Export jobs to JSON format"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get jobs data
                    jobs_data = []
                    for job_id in export_request.job_ids:
                        job_row = await conn.fetchrow("""
                            SELECT id, name, description, workflow_definition, schedule_expression,
                                   is_enabled, tags, metadata, created_by, updated_by, created_at, updated_at
                            FROM automation.jobs WHERE id = $1
                        """, job_id)
                        
                        if not job_row:
                            continue
                            
                        job_data = {
                            "id": job_row['id'],
                            "name": job_row['name'],
                            "description": job_row['description'],
                            "workflow_definition": job_row['workflow_definition'],
                            "schedule_expression": job_row['schedule_expression'],
                            "is_enabled": job_row['is_enabled'],
                            "tags": job_row['tags'],
                            "metadata": job_row['metadata'] if export_request.include_metadata else {},
                            "created_by": job_row['created_by'],
                            "updated_by": job_row['updated_by'],
                            "created_at": job_row['created_at'].isoformat(),
                            "updated_at": job_row['updated_at'].isoformat()
                        }
                        
                        # Include executions if requested
                        if export_request.include_executions:
                            execution_rows = await conn.fetch("""
                                SELECT id, execution_id, status, trigger_type, input_data, output_data,
                                       error_message, started_at, completed_at, started_by, created_at
                                FROM automation.job_executions WHERE job_id = $1
                                ORDER BY created_at DESC LIMIT 10
                            """, job_id)
                            
                            job_data["recent_executions"] = [
                                {
                                    "id": row['id'],
                                    "execution_id": row['execution_id'],
                                    "status": row['status'],
                                    "trigger_type": row['trigger_type'],
                                    "input_data": row['input_data'],
                                    "output_data": row['output_data'],
                                    "error_message": row['error_message'],
                                    "started_at": row['started_at'].isoformat() if row['started_at'] else None,
                                    "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None,
                                    "started_by": row['started_by'],
                                    "created_at": row['created_at'].isoformat()
                                }
                                for row in execution_rows
                            ]
                        
                        jobs_data.append(job_data)
                    
                    export_data = {
                        "version": "1.0",
                        "exported_at": datetime.utcnow().isoformat(),
                        "jobs": jobs_data,
                        "total_jobs": len(jobs_data)
                    }
                    
                    return {
                        "success": True,
                        "message": f"Exported {len(jobs_data)} jobs",
                        "data": export_data
                    }
            except Exception as e:
                self.logger.error("Failed to export jobs", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to export jobs"
                )

        @self.app.post("/jobs/import", response_model=dict)
        async def import_jobs(import_request: JobImportRequest):
            """Import jobs from JSON format with validation"""
            try:
                async with self.db.pool.acquire() as conn:
                    jobs_data = import_request.jobs_data.get('jobs', [])
                    imported_count = 0
                    skipped_count = 0
                    errors = []
                    
                    for job_data in jobs_data:
                        try:
                            # ============================================================================
                            # VALIDATE IMPORTED WORKFLOWS - Prevent dangerous imports
                            # ============================================================================
                            
                            workflow_def = job_data.get('workflow_definition', {})
                            if workflow_def:
                                # Apply same validation as job creation
                                steps = workflow_def.get('steps', [])
                                nodes = workflow_def.get('nodes', [])
                                total_steps = len(steps) + len(nodes)
                                
                                if total_steps > 100:
                                    errors.append(f"Job '{job_data['name']}': {total_steps} steps exceeds limit of 100")
                                    skipped_count += 1
                                    continue
                                
                                workflow_depth = self._calculate_workflow_depth(workflow_def)
                                if workflow_depth > 20:
                                    errors.append(f"Job '{job_data['name']}': workflow depth {workflow_depth} exceeds limit of 20")
                                    skipped_count += 1
                                    continue
                                
                                parallel_branches = self._count_parallel_branches(workflow_def)
                                if parallel_branches > 10:
                                    errors.append(f"Job '{job_data['name']}': {parallel_branches} parallel branches exceeds limit of 10")
                                    skipped_count += 1
                                    continue
                                
                                total_iterations = self._estimate_loop_iterations(workflow_def)
                                if total_iterations > 1000:
                                    errors.append(f"Job '{job_data['name']}': estimated {total_iterations} iterations exceeds limit of 1000")
                                    skipped_count += 1
                                    continue
                                
                                self.logger.info(f"Import validation passed for '{job_data['name']}': {total_steps} steps, {workflow_depth} depth")
                            
                            # Check if job already exists
                            existing_job = await conn.fetchrow(
                                "SELECT id FROM automation.jobs WHERE name = $1",
                                job_data['name']
                            )
                            
                            if existing_job and not import_request.overwrite_existing:
                                skipped_count += 1
                                continue
                            
                            if existing_job and import_request.overwrite_existing:
                                # Update existing job
            
                                await conn.execute("""
                                    UPDATE automation.jobs 
                                    SET description = $1, workflow_definition = $2, schedule_expression = $3,
                                        is_enabled = $4, tags = $5, metadata = $6, updated_by = $7, updated_at = NOW()
                                    WHERE id = $8
                                """, job_data.get('description'), json.dumps(job_data.get('workflow_definition', {})),
                                     job_data.get('schedule_expression'), job_data.get('is_enabled', True),
                                     json.dumps(job_data.get('tags', [])), json.dumps(job_data.get('metadata', {})), 
                                     self._get_current_user_id(), existing_job['id'])
                            else:
                                # Create new job
            
                                await conn.execute("""
                                    INSERT INTO automation.jobs 
                                    (name, description, workflow_definition, schedule_expression, is_enabled, 
                                     tags, metadata, created_by, updated_by)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                """, job_data['name'], job_data.get('description'), 
                                     json.dumps(job_data.get('workflow_definition', {})), job_data.get('schedule_expression'),
                                     job_data.get('is_enabled', True), json.dumps(job_data.get('tags', [])), 
                                     json.dumps(job_data.get('metadata', {})), 
                                     self._get_current_user_id(), self._get_current_user_id())
                            
                            imported_count += 1
                            
                        except Exception as job_error:
                            errors.append(f"Job '{job_data.get('name', 'unknown')}': {str(job_error)}")
                    
                    return {
                        "success": True,
                        "message": f"Import completed: {imported_count} imported, {skipped_count} skipped",
                        "data": {
                            "imported_count": imported_count,
                            "skipped_count": skipped_count,
                            "errors": errors
                        }
                    }
            except Exception as e:
                self.logger.error("Failed to import jobs", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to import jobs"
                )
        
        @self.app.get("/schedules", response_model=ScheduleListResponse)
        async def list_schedules(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all job schedules"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM automation.job_schedules")
                    
                    # Get schedules with job names
                    rows = await conn.fetch("""
                        SELECT js.id, js.job_id, j.name as job_name, js.schedule_expression,
                               js.timezone, js.is_active, js.next_run_at, js.last_run_at,
                               js.created_at, js.updated_at
                        FROM automation.job_schedules js
                        JOIN automation.jobs j ON js.job_id = j.id
                        ORDER BY js.created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    schedules = []
                    for row in rows:
                        schedules.append(JobSchedule(
                            id=row['id'],
                            job_id=row['job_id'],
                            job_name=row['job_name'],
                            schedule_type="cron",
                            cron_expression=row['schedule_expression'],
                            interval_seconds=None,
                            is_active=row['is_active'],
                            next_run=row['next_run_at'].isoformat() if row['next_run_at'] else None,
                            created_by=self._get_current_user_id(),
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return ScheduleListResponse(
                        schedules=schedules,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch schedules", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch schedules"
                )

        @self.app.post("/schedules", response_model=dict)
        async def create_schedule(schedule_data: ScheduleCreate):
            """Create a new schedule with workflow validation"""
            try:
                async with self.db.pool.acquire() as conn:
                    # ============================================================================
                    # VALIDATE SCHEDULED WORKFLOW - Prevent scheduling dangerous workflows
                    # ============================================================================
                    
                    # Get the job's workflow definition
                    job_row = await conn.fetchrow(
                        "SELECT workflow_definition FROM automation.jobs WHERE id = $1",
                        schedule_data.job_id
                    )
                    
                    if not job_row:
                        raise HTTPException(status_code=404, detail="Job not found")
                    

                    workflow_def = json.loads(job_row['workflow_definition']) if job_row['workflow_definition'] else {}
                    
                    if workflow_def:
                        # Validate the workflow before allowing it to be scheduled
                        steps = workflow_def.get('steps', [])
                        nodes = workflow_def.get('nodes', [])
                        total_steps = len(steps) + len(nodes)
                        
                        if total_steps > 100:
                            self.logger.error(f"Schedule creation rejected: job {schedule_data.job_id} has {total_steps} steps exceeds limit")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Cannot schedule: job workflow has {total_steps} steps (max 100)"
                            )
                        
                        workflow_depth = self._calculate_workflow_depth(workflow_def)
                        if workflow_depth > 20:
                            self.logger.error(f"Schedule creation rejected: job {schedule_data.job_id} depth {workflow_depth} exceeds limit")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Cannot schedule: workflow depth {workflow_depth} exceeds maximum of 20"
                            )
                        
                        # Additional validation for scheduled jobs - be more restrictive
                        parallel_branches = self._count_parallel_branches(workflow_def)
                        if parallel_branches > 5:  # Lower limit for scheduled jobs
                            self.logger.error(f"Schedule creation rejected: job {schedule_data.job_id} has {parallel_branches} parallel branches")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Cannot schedule: {parallel_branches} parallel branches exceeds maximum of 5 for scheduled jobs"
                            )
                        
                        total_iterations = self._estimate_loop_iterations(workflow_def)
                        if total_iterations > 500:  # Lower limit for scheduled jobs
                            self.logger.error(f"Schedule creation rejected: job {schedule_data.job_id} has {total_iterations} iterations")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Cannot schedule: estimated {total_iterations} iterations exceeds maximum of 500 for scheduled jobs"
                            )
                        
                        self.logger.info(f"Schedule validation passed for job {schedule_data.job_id}: {total_steps} steps, {workflow_depth} depth")
                    
                    row = await conn.fetchrow("""
                        INSERT INTO automation.job_schedules (job_id, schedule_expression, timezone, is_active)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id, job_id, schedule_expression, timezone, is_active, 
                                  next_run_at, last_run_at, created_at, updated_at
                    """, schedule_data.job_id, schedule_data.schedule_expression, 
                         schedule_data.timezone, schedule_data.is_active)
                    
                    # Get job name
                    job_row = await conn.fetchrow("SELECT name FROM automation.jobs WHERE id = $1", schedule_data.job_id)
                    job_name = job_row['name'] if job_row else "Unknown"
                    
                    schedule = JobSchedule(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=job_name,
                        schedule_type="cron",
                        cron_expression=row['schedule_expression'],
                        interval_seconds=None,
                        is_active=row['is_active'],
                        next_run=row['next_run_at'].isoformat() if row['next_run_at'] else None,
                        created_by=1,
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Schedule created", "data": schedule}
            except Exception as e:
                self.logger.error("Failed to create schedule", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create schedule"
                )

        @self.app.get("/schedules/{schedule_id}", response_model=dict)
        async def get_schedule(schedule_id: int):
            """Get schedule by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT js.id, js.job_id, j.name as job_name, js.schedule_expression,
                               js.timezone, js.is_active, js.next_run_at, js.last_run_at,
                               js.created_at, js.updated_at
                        FROM automation.job_schedules js
                        JOIN automation.jobs j ON js.job_id = j.id
                        WHERE js.id = $1
                    """, schedule_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Schedule not found")
                    
                    schedule = JobSchedule(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=row['job_name'],
                        schedule_expression=row['schedule_expression'],
                        timezone=row['timezone'],
                        is_active=row['is_active'],
                        next_run_at=row['next_run_at'].isoformat() if row['next_run_at'] else None,
                        last_run_at=row['last_run_at'].isoformat() if row['last_run_at'] else None,
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": schedule}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get schedule", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get schedule"
                )

        @self.app.put("/schedules/{schedule_id}", response_model=dict)
        async def update_schedule(schedule_id: int, schedule_data: ScheduleUpdate):
            """Update schedule"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if schedule_data.schedule_expression is not None:
                        updates.append(f"schedule_expression = ${param_count}")
                        values.append(schedule_data.schedule_expression)
                        param_count += 1
                    if schedule_data.timezone is not None:
                        updates.append(f"timezone = ${param_count}")
                        values.append(schedule_data.timezone)
                        param_count += 1
                    if schedule_data.is_active is not None:
                        updates.append(f"is_active = ${param_count}")
                        values.append(schedule_data.is_active)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    values.append(schedule_id)
                    
                    query = f"""
                        UPDATE automation.job_schedules 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, job_id, schedule_expression, timezone, is_active,
                                  next_run_at, last_run_at, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Schedule not found")
                    
                    # Get job name
                    job_row = await conn.fetchrow("SELECT name FROM automation.jobs WHERE id = $1", row['job_id'])
                    job_name = job_row['name'] if job_row else "Unknown"
                    
                    schedule = JobSchedule(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=job_name,
                        schedule_expression=row['schedule_expression'],
                        timezone=row['timezone'],
                        is_active=row['is_active'],
                        next_run_at=row['next_run_at'].isoformat() if row['next_run_at'] else None,
                        last_run_at=row['last_run_at'].isoformat() if row['last_run_at'] else None,
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Schedule updated", "data": schedule}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update schedule", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update schedule"
                )

        @self.app.delete("/schedules/{schedule_id}", response_model=dict)
        async def delete_schedule(schedule_id: int):
            """Delete schedule"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM automation.job_schedules WHERE id = $1", schedule_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Schedule not found")
                    
                    return {"success": True, "message": "Schedule deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete schedule", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete schedule"
                )
        
        @self.app.get("/executions", response_model=ExecutionListResponse)
        async def list_executions(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all job executions"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM automation.job_executions")
                    
                    # Get executions with job names
                    rows = await conn.fetch("""
                        SELECT je.id, je.job_id, j.name as job_name, je.execution_id, je.status,
                               je.trigger_type, je.input_data, je.output_data, je.error_message,
                               je.started_at, je.completed_at, je.started_by, je.created_at
                        FROM automation.job_executions je
                        JOIN automation.jobs j ON je.job_id = j.id
                        ORDER BY je.created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    executions = []
                    for row in rows:
                        # Parse JSON strings if needed
                        input_data = self._parse_json_field(row['input_data'])
                        output_data = self._parse_json_field(row['output_data'])
                        
                        executions.append(JobExecution(
                            id=row['id'],
                            job_id=row['job_id'],
                            job_name=row['job_name'],
                            execution_id=str(row['execution_id']),
                            status=row['status'],
                            trigger_type=row['trigger_type'],
                            input_data=input_data,
                            output_data=output_data,
                            error_message=row['error_message'],
                            started_at=row['started_at'].isoformat() if row['started_at'] else None,
                            completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                            started_by=row['started_by'],
                            created_at=row['created_at'].isoformat()
                        ))
                    
                    return ExecutionListResponse(
                        executions=executions,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch executions", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch executions"
                )

        @self.app.post("/executions", response_model=dict)
        async def create_execution(execution_data: ExecutionCreate):
            """Create a new execution with pre-execution validation"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get job details including workflow definition and job type
                    job_row = await conn.fetchrow("""
                        SELECT name, workflow_definition, job_type, is_enabled FROM automation.jobs WHERE id = $1
                    """, execution_data.job_id)
                    
                    if not job_row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Job not found"
                        )
                    
                    # Check if job is enabled
                    if not job_row['is_enabled']:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot execute disabled job"
                        )
                    
                    # Validate workflow before execution
                    workflow_def = json.loads(job_row['workflow_definition']) if job_row['workflow_definition'] else {}
                    steps = workflow_def.get('steps', [])
                    nodes = workflow_def.get('nodes', [])
                    total_steps = len(steps) + len(nodes)
                    
                    # Prevent execution of empty workflows (except for specific job types)
                    if total_steps == 0 and job_row['job_type'] not in ['template', 'placeholder']:
                        self.logger.error(f"Execution rejected: Job {execution_data.job_id} has empty workflow")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot execute job with empty workflow definition"
                        )
                    
                    # Validate step structure for non-empty workflows
                    if total_steps > 0:
                        invalid_steps = []
                        for i, step in enumerate(steps + nodes):
                            step_id = step.get('id', f'step_{i}')
                            step_name = step.get('name', '')
                            library_name = step.get('library')
                            function_name = step.get('function')
                            command = step.get('command')
                            
                            # Each step must have either library+function or command
                            if not ((library_name and function_name) or command):
                                invalid_steps.append(f"Step '{step_id}' ({step_name}) has no executable action")
                        
                        if invalid_steps:
                            self.logger.error(f"Execution rejected: Job {execution_data.job_id} has invalid steps: {invalid_steps}")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Cannot execute job with invalid steps: {'; '.join(invalid_steps[:3])}{'...' if len(invalid_steps) > 3 else ''}"
                            )
                    
                    # Queue the job for execution using Celery first to get task ID
                    try:
                        from worker import execute_job
                        task = execute_job.delay(
                            job_id=execution_data.job_id,
                            workflow_definition=job_row['workflow_definition'],
                            input_data=execution_data.input_data or {}
                        )
                        # Use Celery task ID as execution_id for proper synchronization
                        execution_id = task.id
                        self.logger.info(f"Queued execution with task ID {execution_id}")
                    except Exception as task_error:
                        self.logger.error(f"Failed to queue task: {task_error}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to queue task: {str(task_error)}"
                        )

                    row = await conn.fetchrow("""
                        INSERT INTO automation.job_executions (job_id, execution_id, status, trigger_type, 
                                                   input_data, started_by)
                        VALUES ($1, $2, 'pending', $3, $4, $5)
                        RETURNING id, job_id, execution_id, status, trigger_type, input_data,
                                  output_data, error_message, started_at, completed_at, started_by, created_at
                    """, execution_data.job_id, execution_id, execution_data.trigger_type, 
                         json.dumps(execution_data.input_data) if execution_data.input_data else '{}',
                         self._get_current_user_id())
                    
                    execution = JobExecution(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=job_row['name'],
                        execution_id=str(row['execution_id']),
                        status=row['status'],
                        trigger_type=row['trigger_type'],
                        input_data=json.loads(row['input_data']) if row['input_data'] else {},
                        output_data=json.loads(row['output_data']) if row['output_data'] else {},
                        error_message=row['error_message'],
                        started_at=row['started_at'].isoformat() if row['started_at'] else None,
                        completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                        started_by=row['started_by'],
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Execution created and queued", "data": execution}
            except Exception as e:
                self.logger.error("Failed to create execution", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create execution"
                )

        @self.app.get("/executions/{execution_id}", response_model=dict)
        async def get_execution(execution_id: int):
            """Get execution by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT je.id, je.job_id, j.name as job_name, je.execution_id, je.status,
                               je.trigger_type, je.input_data, je.output_data, je.error_message,
                               je.started_at, je.completed_at, je.started_by, je.created_at
                        FROM automation.job_executions je
                        JOIN automation.jobs j ON je.job_id = j.id
                        WHERE je.id = $1
                    """, execution_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Execution not found")
                    
                    execution = JobExecution(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=row['job_name'],
                        execution_id=str(row['execution_id']),
                        status=row['status'],
                        trigger_type=row['trigger_type'],
                        input_data=self._parse_json_field(row['input_data']),
                        output_data=self._parse_json_field(row['output_data']),
                        error_message=row['error_message'],
                        started_at=row['started_at'].isoformat() if row['started_at'] else None,
                        completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                        started_by=row['started_by'],
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "data": execution}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get execution", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get execution"
                )

        @self.app.get("/executions/{execution_id}/steps", response_model=dict)
        async def get_execution_steps(execution_id: int):
            """Get execution steps"""
            try:
                async with self.db.pool.acquire() as conn:
                    # First check if execution exists
                    execution_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM automation.job_executions WHERE id = $1)", 
                        execution_id
                    )
                    
                    if not execution_exists:
                        raise HTTPException(status_code=404, detail="Execution not found")
                    
                    # Get execution info and actual step executions
                    execution_row = await conn.fetchrow("""
                        SELECT je.id, je.execution_id, je.status, je.started_at, je.completed_at,
                               je.error_message, j.name as job_name, j.workflow_definition
                        FROM automation.job_executions je
                        JOIN automation.jobs j ON je.job_id = j.id
                        WHERE je.id = $1
                    """, execution_id)
                    
                    # Get actual step executions from database
                    step_rows = await conn.fetch("""
                        SELECT id, step_id, step_name, step_type, status, 
                               started_at, completed_at, output_data, error_message, execution_order
                        FROM automation.step_executions
                        WHERE job_execution_id = $1
                        ORDER BY execution_order
                    """, execution_id)
                    
                    # Convert step executions to API format
                    steps = []
                    for i, row in enumerate(step_rows):
                        duration_ms = None
                        if row['started_at'] and row['completed_at']:
                            duration = row['completed_at'] - row['started_at']
                            duration_ms = int(duration.total_seconds() * 1000)
                        
                        # Parse output_data if it's a JSON string
                        output_data = None
                        if row['output_data']:
                            try:
                                import json
                                output_data = json.loads(row['output_data']) if isinstance(row['output_data'], str) else row['output_data']
                            except:
                                output_data = row['output_data']
                        
                        step = {
                            "id": row['id'],
                            "step_id": row['step_id'],
                            "name": row['step_name'],
                            "type": row['step_type'],
                            "status": row['status'],
                            "started_at": row['started_at'].isoformat() if row['started_at'] else None,
                            "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None,
                            "duration_ms": duration_ms,
                            "error_message": row['error_message'],
                            "output": output_data
                        }
                        steps.append(step)
                    
                    # If no step executions found, fall back to generating mock steps
                    if not steps:
                        steps = self._generate_execution_steps(
                            execution_row['workflow_definition'],
                            execution_row['status'],
                            execution_row['started_at'],
                            execution_row['completed_at'],
                            execution_row['error_message']
                        )
                    
                    return {
                        "success": True,
                        "data": {
                            "execution_id": execution_id,
                            "job_name": execution_row['job_name'],
                            "status": execution_row['status'],
                            "steps": steps,
                            "total_steps": len(steps),
                            "completed_steps": len([s for s in steps if s['status'] == 'completed']),
                            "failed_steps": len([s for s in steps if s['status'] == 'failed'])
                        }
                    }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get execution steps", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get execution steps"
                )

        @self.app.post("/executions/cleanup-stuck", response_model=dict)
        async def cleanup_stuck_executions():
            """Clean up stuck executions that are in queued/running state but have no active Celery task"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Find executions that have been in queued/running state for more than 30 minutes
                    stuck_executions = await conn.fetch("""
                        SELECT je.id, je.job_id, je.execution_id, je.status, j.name as job_name,
                               j.workflow_definition, je.created_at
                        FROM automation.job_executions je
                        JOIN automation.jobs j ON je.job_id = j.id
                        WHERE je.status IN ('queued', 'running', 'pending')
                        AND je.created_at < NOW() - INTERVAL '30 minutes'
                        ORDER BY je.created_at
                    """)
                    
                    cleaned_count = 0
                    errors = []
                    
                    for execution in stuck_executions:
                        try:
                            # Check if this is an empty workflow job
                            workflow_def = json.loads(execution['workflow_definition']) if execution['workflow_definition'] else {}
                            steps = workflow_def.get('steps', [])
                            nodes = workflow_def.get('nodes', [])
                            total_steps = len(steps) + len(nodes)
                            
                            error_message = None
                            if total_steps == 0:
                                error_message = "Job has empty workflow definition - no executable steps"
                            else:
                                error_message = "Job execution stuck - cleaned up by system"
                            
                            # Update to failed status
                            await conn.execute("""
                                UPDATE automation.job_executions 
                                SET status = 'failed', 
                                    completed_at = NOW(), 
                                    error_message = $1
                                WHERE id = $2
                            """, error_message, execution['id'])
                            
                            cleaned_count += 1
                            self.logger.info(f"Cleaned up stuck execution {execution['id']} for job '{execution['job_name']}'")
                            
                        except Exception as e:
                            error_msg = f"Failed to clean execution {execution['id']}: {str(e)}"
                            errors.append(error_msg)
                            self.logger.error(error_msg)
                    
                    return {
                        "success": True,
                        "message": f"Cleanup completed: {cleaned_count} executions cleaned",
                        "data": {
                            "cleaned_count": cleaned_count,
                            "errors": errors,
                            "total_found": len(stuck_executions)
                        }
                    }
            except Exception as e:
                self.logger.error("Failed to cleanup stuck executions", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to cleanup stuck executions"
                )

        @self.app.post("/jobs/validate-existing", response_model=dict)
        async def validate_existing_jobs():
            """Validate all existing jobs and report issues"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get all jobs
                    jobs = await conn.fetch("""
                        SELECT id, name, workflow_definition, job_type, is_enabled
                        FROM automation.jobs
                        ORDER BY created_at DESC
                    """)
                    
                    issues = []
                    valid_count = 0
                    
                    for job in jobs:
                        job_issues = []
                        workflow_def = json.loads(job['workflow_definition']) if job['workflow_definition'] else {}
                        steps = workflow_def.get('steps', [])
                        nodes = workflow_def.get('nodes', [])
                        total_steps = len(steps) + len(nodes)
                        
                        # Check for empty workflows
                        if total_steps == 0 and job['job_type'] not in ['template', 'placeholder']:
                            job_issues.append("Empty workflow definition")
                        
                        # Check for invalid steps
                        if total_steps > 0:
                            invalid_steps = []
                            for i, step in enumerate(steps + nodes):
                                step_id = step.get('id', f'step_{i}')
                                library_name = step.get('library')
                                function_name = step.get('function')
                                command = step.get('command')
                                
                                if not ((library_name and function_name) or command):
                                    invalid_steps.append(step_id)
                            
                            if invalid_steps:
                                job_issues.append(f"Invalid steps (no executable action): {', '.join(invalid_steps[:3])}")
                        
                        if job_issues:
                            issues.append({
                                "job_id": job['id'],
                                "job_name": job['name'],
                                "job_type": job['job_type'],
                                "is_enabled": job['is_enabled'],
                                "issues": job_issues
                            })
                        else:
                            valid_count += 1
                    
                    return {
                        "success": True,
                        "message": f"Validation completed: {valid_count} valid, {len(issues)} with issues",
                        "data": {
                            "valid_count": valid_count,
                            "issues_count": len(issues),
                            "total_jobs": len(jobs),
                            "issues": issues
                        }
                    }
            except Exception as e:
                self.logger.error("Failed to validate existing jobs", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to validate existing jobs"
                )

        @self.app.put("/executions/{execution_id}", response_model=dict)
        async def update_execution(execution_id: int, execution_data: ExecutionUpdate):
            """Update execution"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if execution_data.status is not None:
                        updates.append(f"status = ${param_count}")
                        values.append(execution_data.status)
                        param_count += 1
                        
                        # Set completed_at if status is completed or failed
                        if execution_data.status in ['completed', 'failed']:
                            updates.append(f"completed_at = ${param_count}")
                            values.append(datetime.utcnow())
                            param_count += 1
                    
                    if execution_data.output_data is not None:
                        updates.append(f"output_data = ${param_count}")
                        values.append(execution_data.output_data)
                        param_count += 1
                    
                    if execution_data.error_message is not None:
                        updates.append(f"error_message = ${param_count}")
                        values.append(execution_data.error_message)
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    values.append(execution_id)
                    
                    query = f"""
                        UPDATE automation.job_executions 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, job_id, execution_id, status, trigger_type, input_data,
                                  output_data, error_message, started_at, completed_at, started_by, created_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Execution not found")
                    
                    # Get job name
                    job_row = await conn.fetchrow("SELECT name FROM automation.jobs WHERE id = $1", row['job_id'])
                    job_name = job_row['name'] if job_row else "Unknown"
                    
                    execution = JobExecution(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=job_name,
                        execution_id=str(row['execution_id']),
                        status=row['status'],
                        trigger_type=row['trigger_type'],
                        input_data=self._parse_json_field(row['input_data']),
                        output_data=self._parse_json_field(row['output_data']),
                        error_message=row['error_message'],
                        started_at=row['started_at'].isoformat() if row['started_at'] else None,
                        completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                        started_by=row['started_by'],
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "message": "Execution updated", "data": execution}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update execution", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update execution"
                )

        @self.app.delete("/executions/{execution_id}", response_model=dict)
        async def delete_execution(execution_id: int):
            """Delete execution"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM automation.job_executions WHERE id = $1", execution_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Execution not found")
                    
                    return {"success": True, "message": "Execution deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete execution", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete execution"
                )
        # ============================================================================
        # RUNS ENDPOINTS (Alias for executions for frontend compatibility)
        # ============================================================================
        
        @self.app.get("/runs", response_model=ExecutionListResponse)
        async def list_runs(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all job executions (alias for /executions)"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM automation.job_executions")
                    
                    # Get executions with pagination
                    rows = await conn.fetch("""
                        SELECT je.id, je.job_id, j.name as job_name, je.execution_id, je.status,
                               je.trigger_type, je.input_data, je.output_data, je.error_message,
                               je.started_at, je.completed_at, je.started_by, je.created_at
                        FROM automation.job_executions je
                        LEFT JOIN automation.jobs j ON je.job_id = j.id
                        ORDER BY je.created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    executions = []
                    for row in rows:
    
                        executions.append(JobExecution(
                            id=row['id'],
                            job_id=row['job_id'],
                            job_name=row['job_name'] or f"Job {row['job_id']}",
                            execution_id=str(row['execution_id']),
                            status=row['status'],
                            trigger_type=row['trigger_type'],
                            input_data=json.loads(row['input_data']) if row['input_data'] else {},
                            output_data=json.loads(row['output_data']) if row['output_data'] else {},
                            error_message=row['error_message'],
                            started_at=row['started_at'].isoformat() if row['started_at'] else None,
                            completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                            started_by=row['started_by'],
                            created_at=row['created_at'].isoformat()
                        ))
                    
                    return ExecutionListResponse(
                        executions=executions,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch runs", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch runs"
                )

        @self.app.get("/runs/{run_id}", response_model=dict)
        async def get_run(run_id: int):
            """Get run by ID (alias for execution)"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT je.id, je.job_id, j.name as job_name, je.execution_id, je.status,
                               je.trigger_type, je.input_data, je.output_data, je.error_message,
                               je.started_at, je.completed_at, je.started_by, je.created_at
                        FROM automation.job_executions je
                        LEFT JOIN automation.jobs j ON je.job_id = j.id
                        WHERE je.id = $1
                    """, run_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Run not found")
                    

                    execution = JobExecution(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=row['job_name'] or f"Job {row['job_id']}",
                        execution_id=str(row['execution_id']),
                        status=row['status'],
                        trigger_type=row['trigger_type'],
                        input_data=json.loads(row['input_data']) if row['input_data'] else {},
                        output_data=json.loads(row['output_data']) if row['output_data'] else {},
                        error_message=row['error_message'],
                        started_at=row['started_at'].isoformat() if row['started_at'] else None,
                        completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                        started_by=row['started_by'],
                        created_at=row['created_at'].isoformat()
                    )
                    
                    return {"success": True, "data": execution}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get run", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get run"
                )

        @self.app.get("/runs/{run_id}/steps", response_model=List[StepExecution])
        async def get_run_steps(run_id: int):
            """Get steps for a specific run"""
            try:
                async with self.db.pool.acquire() as conn:
                    # First verify the run exists
                    run_exists = await conn.fetchval("""
                        SELECT EXISTS(SELECT 1 FROM automation.job_executions WHERE id = $1)
                    """, run_id)
                    
                    if not run_exists:
                        raise HTTPException(status_code=404, detail="Run not found")
                    
                    # Get steps for the run
                    rows = await conn.fetch("""
                        SELECT id, job_execution_id, step_id, step_name, step_type, status,
                               input_data, output_data, error_message, started_at, completed_at, execution_order
                        FROM automation.step_executions
                        WHERE job_execution_id = $1
                        ORDER BY execution_order ASC
                    """, run_id)
                    
                    steps = []
                    for row in rows:
                        steps.append(StepExecution(
                            id=row['id'],
                            job_execution_id=row['job_execution_id'],
                            step_id=row['step_id'],
                            step_name=row['step_name'],
                            step_type=row['step_type'],
                            status=row['status'],
                            input_data=json.loads(row['input_data']) if row['input_data'] else {},
                            output_data=json.loads(row['output_data']) if row['output_data'] else {},
                            error_message=row['error_message'],
                            started_at=row['started_at'].isoformat() if row['started_at'] else None,
                            completed_at=row['completed_at'].isoformat() if row['completed_at'] else None,
                            execution_order=row['execution_order']
                        ))
                    
                    return steps
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get run steps", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get run steps"
                )

        @self.app.post("/automation/test-connection", response_model=dict)
        async def test_connection(connection_data: dict):
            """Test connection to a target service"""
            try:
                # Extract connection parameters
                host = connection_data.get('host')
                port = connection_data.get('port')
                service_type = connection_data.get('service_type', '').lower()
                credential_type = connection_data.get('credential_type')
                username = connection_data.get('username')
                service_id = connection_data.get('service_id')
                target_id = connection_data.get('target_id')
                
                if not host or not port:
                    raise HTTPException(status_code=400, detail="Host and port are required")
                
                success = False
                error_message = ""
                
                # Perform service-specific connection test
                if service_type == 'ssh':
                    success, error_message = await self._test_ssh_connection(host, port, username)
                elif service_type in ['winrm_http', 'winrm_https']:
                    success, error_message = await self._test_winrm_connection(host, port, service_type, username)
                else:
                    # Basic port connectivity test for other services
                    success, error_message = await self._test_port_connection(host, port)
                
                # Update the asset database with connection status if service_id is provided
                if service_id and target_id:
                    try:
                        async with self.db.pool.acquire() as conn:
                            connection_status = 'connected' if success else 'failed'
                            await conn.execute("""
                                UPDATE assets.target_services 
                                SET connection_status = $1, last_tested_at = NOW()
                                WHERE id = $2 AND target_id = $3
                            """, connection_status, service_id, target_id)
                    except Exception as db_error:
                        self.logger.warning("Failed to update connection status in database", error=str(db_error))
                        # Don't fail the whole request if database update fails
                
                return {
                    "success": success,
                    "error": error_message if not success else None,
                    "host": host,
                    "port": port,
                    "service_type": service_type
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Connection test failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Connection test failed: {str(e)}"
                )

    # ============================================================================
    # EXECUTION HELPER METHODS
    # ============================================================================
    
    def _generate_execution_steps(self, workflow_definition: str, execution_status: str, 
                                started_at: str, completed_at: str, error_message: str) -> list:
        """Generate execution steps based on workflow definition and status"""
        import json
        from datetime import datetime, timedelta
        
        try:
            # Parse workflow definition
            if isinstance(workflow_definition, str):
                workflow = json.loads(workflow_definition)
            else:
                workflow = workflow_definition or {}
            
            # Extract nodes/steps from workflow
            nodes = workflow.get('nodes', [])
            if not nodes:
                # Create default steps if no workflow definition
                nodes = [
                    {"id": "1", "type": "start", "name": "Initialize"},
                    {"id": "2", "type": "execute", "name": "Execute Task"},
                    {"id": "3", "type": "end", "name": "Complete"}
                ]
            
            steps = []
            base_time = datetime.fromisoformat(started_at.replace('Z', '+00:00')) if started_at else datetime.utcnow()
            
            for i, node in enumerate(nodes):
                step_status = self._determine_step_status(i, len(nodes), execution_status, error_message)
                
                # Calculate step timing
                step_start = base_time + timedelta(seconds=i * 2)  # 2 seconds between steps
                step_end = step_start + timedelta(seconds=1) if step_status in ['completed', 'failed'] else None
                
                step = {
                    "id": i + 1,
                    "step_id": node.get('id', str(i + 1)),
                    "name": node.get('name', f"Step {i + 1}"),
                    "type": node.get('type', 'execute'),
                    "status": step_status,
                    "started_at": step_start.isoformat() if step_status != 'pending' else None,
                    "completed_at": step_end.isoformat() if step_end else None,
                    "duration_ms": 1000 if step_status in ['completed', 'failed'] else None,
                    "error_message": error_message if step_status == 'failed' and i == len(nodes) - 1 else None,
                    "output": {"result": "success"} if step_status == 'completed' else None
                }
                
                steps.append(step)
            
            return steps
            
        except Exception as e:
            self.logger.error("Failed to generate execution steps", error=str(e))
            # Return default steps on error
            return [
                {
                    "id": 1,
                    "step_id": "1",
                    "name": "Execution",
                    "type": "execute",
                    "status": execution_status,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "error_message": error_message if execution_status == 'failed' else None
                }
            ]
    
    def _determine_step_status(self, step_index: int, total_steps: int, execution_status: str, error_message: str) -> str:
        """Determine individual step status based on execution status"""
        if execution_status == 'pending':
            return 'pending'
        elif execution_status == 'running':
            # First few steps completed, current step running, rest pending
            if step_index < total_steps // 2:
                return 'completed'
            elif step_index == total_steps // 2:
                return 'running'
            else:
                return 'pending'
        elif execution_status == 'completed':
            return 'completed'
        elif execution_status == 'failed':
            # Steps before failure completed, failure step failed, rest pending
            if step_index < total_steps - 1:
                return 'completed'
            else:
                return 'failed'
        else:
            return 'pending'
    
    # ============================================================================
    # WORKFLOW VALIDATION HELPER METHODS
    # ============================================================================
    
    def _calculate_workflow_depth(self, workflow_def: dict) -> int:
        """Calculate maximum depth of workflow (nested steps/conditions)"""
        try:
            nodes = workflow_def.get('nodes', [])
            steps = workflow_def.get('steps', [])
            
            if not nodes and not steps:
                return 1
            
            max_depth = 1
            
            # Check for nested structures in nodes
            for node in nodes:
                node_depth = self._calculate_node_depth(node, 1)
                max_depth = max(max_depth, node_depth)
            
            # Check for nested structures in steps
            for step in steps:
                step_depth = self._calculate_step_depth(step, 1)
                max_depth = max(max_depth, step_depth)
            
            return max_depth
        except Exception:
            return 1
    
    def _calculate_node_depth(self, node: dict, current_depth: int) -> int:
        """Recursively calculate depth of a workflow node"""
        max_depth = current_depth
        
        # Check for nested conditions, loops, or sub-workflows
        if 'conditions' in node:
            for condition in node.get('conditions', []):
                if isinstance(condition, dict) and 'steps' in condition:
                    for step in condition['steps']:
                        step_depth = self._calculate_step_depth(step, current_depth + 1)
                        max_depth = max(max_depth, step_depth)
        
        if 'children' in node:
            for child in node.get('children', []):
                child_depth = self._calculate_node_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _calculate_step_depth(self, step: dict, current_depth: int) -> int:
        """Recursively calculate depth of a workflow step"""
        max_depth = current_depth
        
        # Check for nested steps
        if 'steps' in step:
            for nested_step in step.get('steps', []):
                nested_depth = self._calculate_step_depth(nested_step, current_depth + 1)
                max_depth = max(max_depth, nested_depth)
        
        return max_depth
    
    def _count_parallel_branches(self, workflow_def: dict) -> int:
        """Count maximum number of parallel execution branches"""
        try:
            nodes = workflow_def.get('nodes', [])
            steps = workflow_def.get('steps', [])
            
            max_parallel = 1
            
            # Check nodes for parallel execution
            for node in nodes:
                if node.get('type') == 'parallel' or node.get('parallel', False):
                    branches = len(node.get('branches', [])) or len(node.get('children', [])) or 1
                    max_parallel = max(max_parallel, branches)
            
            # Check steps for parallel execution
            for step in steps:
                if step.get('type') == 'parallel' or step.get('parallel', False):
                    branches = len(step.get('branches', [])) or len(step.get('steps', [])) or 1
                    max_parallel = max(max_parallel, branches)
            
            return max_parallel
        except Exception:
            return 1
    
    def _estimate_loop_iterations(self, workflow_def: dict) -> int:
        """Estimate total loop iterations in workflow"""
        try:
            nodes = workflow_def.get('nodes', [])
            steps = workflow_def.get('steps', [])
            
            total_iterations = 0
            
            # Check nodes for loops
            for node in nodes:
                if node.get('type') in ['loop', 'while', 'for', 'repeat']:
                    # Estimate iterations based on configuration
                    iterations = node.get('iterations', node.get('max_iterations', 10))
                    if isinstance(iterations, int):
                        total_iterations += iterations
                    else:
                        total_iterations += 10  # Default estimate
            
            # Check steps for loops
            for step in steps:
                if step.get('type') in ['loop', 'while', 'for', 'repeat']:
                    iterations = step.get('iterations', step.get('max_iterations', 10))
                    if isinstance(iterations, int):
                        total_iterations += iterations
                    else:
                        total_iterations += 10  # Default estimate
            
            # If no explicit loops found, assume linear execution
            return max(total_iterations, 1)
        except Exception:
            return 1

    # ============================================================================
    # CONNECTION TEST HELPER METHODS
    # ============================================================================
    
    async def _test_port_connection(self, host: str, port: int) -> tuple[bool, str]:
        """Test basic TCP port connectivity"""
        import asyncio
        import socket
        
        try:
            # Create connection with timeout
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=10.0)
            
            # Close connection
            writer.close()
            await writer.wait_closed()
            
            return True, ""
        except asyncio.TimeoutError:
            return False, f"Connection timeout to {host}:{port}"
        except ConnectionRefusedError:
            return False, f"Connection refused to {host}:{port}"
        except socket.gaierror as e:
            return False, f"DNS resolution failed for {host}: {str(e)}"
        except Exception as e:
            return False, f"Connection failed to {host}:{port}: {str(e)}"
    
    async def _test_ssh_connection(self, host: str, port: int, username: str = None) -> tuple[bool, str]:
        """Test SSH connection"""
        try:
            # First test basic port connectivity
            port_success, port_error = await self._test_port_connection(host, port)
            if not port_success:
                return False, port_error
            
            # For now, just test port connectivity
            # In a full implementation, you would use paramiko or asyncssh
            # to test actual SSH protocol handshake
            return True, f"SSH port {port} is accessible on {host}"
            
        except Exception as e:
            return False, f"SSH test failed for {host}:{port}: {str(e)}"
    
    async def _test_winrm_connection(self, host: str, port: int, service_type: str, username: str = None) -> tuple[bool, str]:
        """Test WinRM connection"""
        try:
            # First test basic port connectivity
            port_success, port_error = await self._test_port_connection(host, port)
            if not port_success:
                return False, port_error
            
            # For now, just test port connectivity
            # In a full implementation, you would use pywinrm
            # to test actual WinRM protocol handshake
            protocol = "HTTPS" if service_type == "winrm_https" else "HTTP"
            return True, f"WinRM {protocol} port {port} is accessible on {host}"
            
        except Exception as e:
            return False, f"WinRM test failed for {host}:{port}: {str(e)}"

    def _setup_monitoring_routes(self):
        """Set up monitoring endpoints"""
        self.logger.info("Setting up monitoring endpoints...")
        
        @self.app.get("/monitoring/stats")
        async def get_monitoring_stats():
            """Get comprehensive monitoring statistics"""
            try:
                stats = await self.monitor.get_monitoring_stats()
                return {"success": True, "data": stats}
            except Exception as e:
                self.logger.error(f"Error getting monitoring stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/monitoring/tasks")
        async def get_tasks(
            limit: int = Query(100, ge=1, le=1000),
            state: Optional[str] = Query(None),
            active_only: bool = Query(False)
        ):
            """Get task information"""
            try:
                if active_only:
                    tasks = await self.monitor.get_active_tasks()
                else:
                    tasks = await self.monitor.get_all_tasks(limit)
                
                # Filter by state if specified
                if state:
                    tasks = [task for task in tasks if task.state == state]
                
                # Convert to serializable format
                task_data = []
                for task in tasks:
                    task_dict = {
                        "task_id": task.task_id,
                        "name": task.name,
                        "state": task.state,
                        "received": task.received.isoformat() if task.received else None,
                        "started": task.started.isoformat() if task.started else None,
                        "runtime": task.runtime,
                        "queue": task.queue,
                        "worker": task.worker
                    }
                    task_data.append(task_dict)
                
                return {"success": True, "data": task_data}
            except Exception as e:
                self.logger.error(f"Error getting tasks: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/monitoring/workers")
        async def get_workers():
            """Get worker information"""
            try:
                workers = await self.monitor.get_worker_info()
                
                # Convert to serializable format
                worker_data = []
                for worker in workers:
                    worker_dict = {
                        "hostname": worker.hostname,
                        "status": worker.status,
                        "active_tasks": worker.active_tasks,
                        "processed_tasks": worker.processed_tasks,
                        "load_avg": worker.load_avg,
                        "last_heartbeat": worker.last_heartbeat.isoformat() if worker.last_heartbeat else None
                    }
                    worker_data.append(worker_dict)
                
                return {"success": True, "data": worker_data}
            except Exception as e:
                self.logger.error(f"Error getting workers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/monitoring/queues")
        async def get_queues():
            """Get queue information"""
            try:
                queues = await self.monitor.get_queue_info()
                
                # Convert to serializable format
                queue_data = []
                for queue in queues:
                    queue_dict = {
                        "name": queue.name,
                        "length": queue.length,
                        "consumers": queue.consumers
                    }
                    queue_data.append(queue_dict)
                
                return {"success": True, "data": queue_data}
            except Exception as e:
                self.logger.error(f"Error getting queues: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/monitoring/ws")
        async def websocket_monitoring(websocket: WebSocket):
            """WebSocket endpoint for real-time monitoring updates"""
            from fastapi import WebSocket, WebSocketDisconnect
            import asyncio
            
            await websocket.accept()
            self.logger.info("WebSocket connection accepted")
            
            # Debug: Check if monitor is available
            if not hasattr(self, 'monitor') or self.monitor is None:
                self.logger.error("Monitor not available!")
                await websocket.close()
                return
            
            try:
                # Send initial data with timing
                import time
                start_time = time.time()
                self.logger.info("Starting to load WebSocket initial data...")
                
                stats = await self.monitor.get_monitoring_stats()
                stats_time = time.time()
                self.logger.info(f"Stats loaded in {stats_time-start_time:.3f}s")
                
                active_tasks = await self.monitor.get_active_tasks()
                tasks_time = time.time()
                self.logger.info(f"Tasks loaded in {tasks_time-stats_time:.3f}s")
                
                workers = await self.monitor.get_worker_info()
                workers_time = time.time()
                self.logger.info(f"Workers loaded in {workers_time-tasks_time:.3f}s")
                
                queues = await self.monitor.get_queue_info()
                queues_time = time.time()
                self.logger.info(f"Queues loaded in {queues_time-workers_time:.3f}s")
                
                self.logger.info(f"WebSocket data loading times - Stats: {stats_time-start_time:.3f}s, Tasks: {tasks_time-stats_time:.3f}s, Workers: {workers_time-tasks_time:.3f}s, Queues: {queues_time-workers_time:.3f}s")
                
                # Convert to serializable format (limit data for performance)
                task_data = []
                for task in active_tasks[:20]:  # Limit to 20 most recent tasks
                    task_dict = {
                        "task_id": task.task_id,
                        "name": task.name,
                        "state": task.state,
                        "received": task.received.isoformat() if task.received else None,
                        "started": task.started.isoformat() if task.started else None,
                        "runtime": task.runtime,
                        "queue": task.queue,
                        "worker": task.worker,
                        "retries": task.retries,
                        "args": task.args[:3] if task.args else [],  # Limit args for performance
                        "kwargs": dict(list(task.kwargs.items())[:3]) if task.kwargs else {}  # Limit kwargs
                    }
                    task_data.append(task_dict)
                
                worker_data = []
                for worker in workers:
                    worker_dict = {
                        "hostname": worker.hostname,
                        "status": worker.status,
                        "active_tasks": worker.active_tasks,
                        "processed_tasks": worker.processed_tasks,
                        "load_avg": worker.load_avg,
                        "last_heartbeat": worker.last_heartbeat.isoformat() if worker.last_heartbeat else None
                    }
                    worker_data.append(worker_dict)
                
                queue_data = []
                for queue in queues:
                    queue_dict = {
                        "name": queue.name,
                        "length": queue.length,
                        "consumers": queue.consumers
                    }
                    queue_data.append(queue_dict)
                
                initial_data = {
                    "type": "initial_data",
                    "data": {
                        "stats": stats,
                        "tasks": task_data,
                        "workers": worker_data,
                        "queues": queue_data
                    }
                }
                
                await websocket.send_json(initial_data)
                
                # Keep connection alive and send periodic updates
                import asyncio
                while True:
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
                    try:
                        # Get updated data
                        stats = await self.monitor.get_monitoring_stats()
                        active_tasks = await self.monitor.get_active_tasks()
                        
                        # Convert tasks to serializable format
                        task_data = []
                        for task in active_tasks:
                            task_dict = {
                                "task_id": task.task_id,
                                "name": task.name,
                                "state": task.state,
                                "received": task.received.isoformat() if task.received else None,
                                "started": task.started.isoformat() if task.started else None,
                                "runtime": task.runtime,
                                "queue": task.queue,
                                "worker": task.worker
                            }
                            task_data.append(task_dict)
                        
                        await websocket.send_json({
                            "type": "stats_update",
                            "data": stats
                        })
                        
                        await websocket.send_json({
                            "type": "tasks_update",
                            "data": task_data
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error sending WebSocket update: {e}")
                        break
                        
            except WebSocketDisconnect:
                self.logger.info("WebSocket client disconnected")
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
            finally:
                try:
                    await websocket.close()
                except:
                    pass

if __name__ == "__main__":
    service = AutomationService()
    service.run()
