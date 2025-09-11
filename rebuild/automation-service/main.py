#!/usr/bin/env python3
"""
OpsConductor Automation Service
Handles jobs, workflows, and execution
Consolidates: jobs-service + executor-service + step-libraries-service
"""

import sys
import os
import json
from typing import List, Optional
from fastapi import Query, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
sys.path.append('/app/shared')
from base_service import BaseService

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

class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_definition: Optional[dict] = None
    schedule_expression: Optional[str] = None
    is_enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None

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

class StepLibrary(BaseModel):
    id: int
    name: str
    version: str
    description: Optional[str] = None
    manifest: dict = {}
    is_active: bool
    is_builtin: bool
    created_by: int
    created_at: str
    updated_at: str

class LibraryCreate(BaseModel):
    name: str
    version: str
    category: str
    description: Optional[str] = None
    steps_definition: dict = {}
    metadata: dict = {}

class LibraryUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    steps_definition: Optional[dict] = None
    metadata: Optional[dict] = None

class LibraryListResponse(BaseModel):
    libraries: List[StepLibrary]
    total: int
    skip: int
    limit: int

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
        self._setup_routes()
    
    async def on_startup(self):
        """Set the database schema to automation"""
        os.environ["DB_SCHEMA"] = "automation"
        await super().on_startup()
    
    def _setup_routes(self):
        @self.app.get("/jobs", response_model=JobListResponse)
        async def list_jobs(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all jobs"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM jobs")
                    
                    # Get jobs with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, description, workflow_definition, schedule_expression,
                               is_enabled, tags, metadata, created_by, updated_by, created_at, updated_at
                        FROM jobs 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    jobs = []
                    for row in rows:
                        import json
                        jobs.append(Job(
                            id=row['id'],
                            name=row['name'],
                            description=row['description'],
                            workflow_definition=json.loads(row['workflow_definition']) if row['workflow_definition'] else {},
                            schedule_expression=row['schedule_expression'],
                            is_enabled=row['is_enabled'],
                            tags=json.loads(row['tags']) if row['tags'] else [],
                            metadata=json.loads(row['metadata']) if row['metadata'] else {},
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
            """Create a new job"""
            try:
                async with self.db.pool.acquire() as conn:
                    import json
                    row = await conn.fetchrow("""
                        INSERT INTO automation.jobs (name, description, workflow_definition, 
                                                   schedule_expression, is_enabled, tags, metadata, 
                                                   created_by, updated_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, 1, 1)
                        RETURNING id, name, description, workflow_definition, schedule_expression,
                                  is_enabled, tags, metadata, created_by, updated_by, created_at, updated_at
                    """, job_data.name, job_data.description, json.dumps(job_data.workflow_definition or {}),
                         job_data.schedule_expression, job_data.is_enabled, json.dumps(job_data.tags or []),
                         json.dumps(job_data.metadata or {}))
                    
                    import json
                    job = Job(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        workflow_definition=json.loads(row['workflow_definition']) if row['workflow_definition'] else {},
                        schedule_expression=row['schedule_expression'],
                        is_enabled=row['is_enabled'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
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
                               is_enabled, tags, metadata, created_by, updated_by, created_at, updated_at
                        FROM automation.jobs WHERE id = $1
                    """, job_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Job not found")
                    
                    import json
                    job = Job(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        workflow_definition=json.loads(row['workflow_definition']) if row['workflow_definition'] else {},
                        schedule_expression=row['schedule_expression'],
                        is_enabled=row['is_enabled'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
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
            """Update job"""
            try:
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
                        values.append(job_data.workflow_definition)
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
                                  is_enabled, tags, metadata, created_by, updated_by, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Job not found")
                    
                    import json
                    job = Job(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        workflow_definition=json.loads(row['workflow_definition']) if row['workflow_definition'] else {},
                        schedule_expression=row['schedule_expression'],
                        is_enabled=row['is_enabled'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
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
            """Execute a job immediately"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get job details
                    job_row = await conn.fetchrow(
                        "SELECT id, name, workflow_definition FROM automation.jobs WHERE id = $1 AND is_enabled = true",
                        job_id
                    )
                    
                    if not job_row:
                        raise HTTPException(status_code=404, detail="Job not found or disabled")
                    
                    # Create execution record
                    import uuid
                    execution_id = str(uuid.uuid4())
                    
                    execution_row = await conn.fetchrow("""
                        INSERT INTO automation.job_executions 
                        (job_id, execution_id, status, trigger_type, input_data, started_by, created_at)
                        VALUES ($1, $2, 'pending', 'manual', $3, 'api', NOW())
                        RETURNING id
                    """, job_id, execution_id, input_data or {})
                    
                    # Queue the job for execution using Celery
                    from shared.tasks import execute_job_task
                    task = execute_job_task.delay(
                        job_id=job_id,
                        execution_id=execution_id,
                        workflow_definition=job_row['workflow_definition'],
                        input_data=input_data or {}
                    )
                    
                    return {
                        "success": True,
                        "message": "Job execution started",
                        "data": {
                            "execution_id": execution_id,
                            "job_id": job_id,
                            "job_name": job_row['name'],
                            "task_id": task.id,
                            "status": "pending"
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
                            created_by=1,
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
            """Create a new schedule"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        INSERT INTO job_schedules (job_id, schedule_expression, timezone, is_active)
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
                        FROM job_schedules js
                        JOIN jobs j ON js.job_id = j.id
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
                        UPDATE job_schedules 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, job_id, schedule_expression, timezone, is_active,
                                  next_run_at, last_run_at, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Schedule not found")
                    
                    # Get job name
                    job_row = await conn.fetchrow("SELECT name FROM jobs WHERE id = $1", row['job_id'])
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
                        "DELETE FROM job_schedules WHERE id = $1", schedule_id
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
                    total = await conn.fetchval("SELECT COUNT(*) FROM job_executions")
                    
                    # Get executions with job names
                    rows = await conn.fetch("""
                        SELECT je.id, je.job_id, j.name as job_name, je.execution_id, je.status,
                               je.trigger_type, je.input_data, je.output_data, je.error_message,
                               je.started_at, je.completed_at, je.started_by, je.created_at
                        FROM job_executions je
                        JOIN jobs j ON je.job_id = j.id
                        ORDER BY je.created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    executions = []
                    for row in rows:
                        executions.append(JobExecution(
                            id=row['id'],
                            job_id=row['job_id'],
                            job_name=row['job_name'],
                            execution_id=str(row['execution_id']),
                            status=row['status'],
                            trigger_type=row['trigger_type'],
                            input_data=row['input_data'] or {},
                            output_data=row['output_data'] or {},
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
            """Create a new execution"""
            try:
                async with self.db.pool.acquire() as conn:
                    import uuid
                    execution_id = str(uuid.uuid4())
                    
                    import json
                    row = await conn.fetchrow("""
                        INSERT INTO automation.job_executions (job_id, execution_id, status, trigger_type, 
                                                   input_data, started_by)
                        VALUES ($1, $2, 'pending', $3, $4, 1)
                        RETURNING id, job_id, execution_id, status, trigger_type, input_data,
                                  output_data, error_message, started_at, completed_at, started_by, created_at
                    """, execution_data.job_id, execution_id, execution_data.trigger_type, 
                         json.dumps(execution_data.input_data) if execution_data.input_data else '{}')
                    
                    # Get job name
                    job_row = await conn.fetchrow("SELECT name FROM automation.jobs WHERE id = $1", execution_data.job_id)
                    job_name = job_row['name'] if job_row else "Unknown"
                    
                    execution = JobExecution(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=job_name,
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
                    
                    return {"success": True, "message": "Execution created", "data": execution}
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
                        FROM job_executions je
                        JOIN jobs j ON je.job_id = j.id
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
                        input_data=row['input_data'] or {},
                        output_data=row['output_data'] or {},
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
                    
                    # Get execution steps (for now, we'll create mock steps based on execution status)
                    execution_row = await conn.fetchrow("""
                        SELECT je.id, je.execution_id, je.status, je.started_at, je.completed_at,
                               je.error_message, j.name as job_name, j.workflow_definition
                        FROM automation.job_executions je
                        JOIN automation.jobs j ON je.job_id = j.id
                        WHERE je.id = $1
                    """, execution_id)
                    
                    # Generate steps based on workflow definition and execution status
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
                        UPDATE job_executions 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, job_id, execution_id, status, trigger_type, input_data,
                                  output_data, error_message, started_at, completed_at, started_by, created_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Execution not found")
                    
                    # Get job name
                    job_row = await conn.fetchrow("SELECT name FROM jobs WHERE id = $1", row['job_id'])
                    job_name = job_row['name'] if job_row else "Unknown"
                    
                    execution = JobExecution(
                        id=row['id'],
                        job_id=row['job_id'],
                        job_name=job_name,
                        execution_id=str(row['execution_id']),
                        status=row['status'],
                        trigger_type=row['trigger_type'],
                        input_data=row['input_data'] or {},
                        output_data=row['output_data'] or {},
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
                        "DELETE FROM job_executions WHERE id = $1", execution_id
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
        
        @self.app.get("/libraries", response_model=LibraryListResponse)
        async def list_libraries(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """List all step libraries"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Get total count
                    total = await conn.fetchval("SELECT COUNT(*) FROM step_libraries")
                    
                    # Get libraries with pagination
                    rows = await conn.fetch("""
                        SELECT id, name, version, description, manifest, is_active, is_builtin,
                               created_by, created_at, updated_at
                        FROM step_libraries 
                        ORDER BY created_at DESC 
                        LIMIT $1 OFFSET $2
                    """, limit, skip)
                    
                    libraries = []
                    for row in rows:
                        import json
                        libraries.append(StepLibrary(
                            id=row['id'],
                            name=row['name'],
                            version=row['version'],
                            description=row['description'],
                            manifest=json.loads(row['manifest']) if row['manifest'] else {},
                            is_active=row['is_active'],
                            is_builtin=row['is_builtin'],
                            created_by=row['created_by'],
                            created_at=row['created_at'].isoformat(),
                            updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                        ))
                    
                    return LibraryListResponse(
                        libraries=libraries,
                        total=total,
                        skip=skip,
                        limit=limit
                    )
            except Exception as e:
                self.logger.error("Failed to fetch libraries", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch libraries"
                )

        @self.app.post("/libraries", response_model=dict)
        async def create_library(library_data: LibraryCreate):
            """Create a new library"""
            try:
                async with self.db.pool.acquire() as conn:
                    import json
                    row = await conn.fetchrow("""
                        INSERT INTO step_libraries (name, version, description, manifest, created_by)
                        VALUES ($1, $2, $3, $4, 1)
                        RETURNING id, name, version, description, manifest, is_active, is_builtin,
                                  created_by, created_at, updated_at
                    """, library_data.name, library_data.version, library_data.description,
                         json.dumps(library_data.steps_definition or {}))
                    
                    library = StepLibrary(
                        id=row['id'],
                        name=row['name'],
                        version=row['version'],
                        description=row['description'],
                        manifest=json.loads(row['manifest']) if row['manifest'] else {},
                        is_active=row['is_active'],
                        is_builtin=row['is_builtin'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Library created", "data": library}
            except Exception as e:
                self.logger.error("Failed to create library", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create library"
                )

        @self.app.get("/libraries/{library_id}", response_model=dict)
        async def get_library(library_id: int):
            """Get library by ID"""
            try:
                async with self.db.pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, name, version, description, manifest, is_active, is_builtin,
                               created_by, created_at, updated_at
                        FROM automation.step_libraries WHERE id = $1
                    """, library_id)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Library not found")
                    
                    import json
                    library = StepLibrary(
                        id=row['id'],
                        name=row['name'],
                        version=row['version'],
                        description=row['description'],
                        manifest=json.loads(row['manifest']) if row['manifest'] else {},
                        is_active=row['is_active'],
                        is_builtin=row['is_builtin'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "data": library}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get library", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get library"
                )

        @self.app.put("/libraries/{library_id}", response_model=dict)
        async def update_library(library_id: int, library_data: LibraryUpdate):
            """Update library"""
            try:
                async with self.db.pool.acquire() as conn:
                    # Build dynamic update query
                    updates = []
                    values = []
                    param_count = 1
                    
                    if library_data.name is not None:
                        updates.append(f"name = ${param_count}")
                        values.append(library_data.name)
                        param_count += 1
                    if library_data.version is not None:
                        updates.append(f"version = ${param_count}")
                        values.append(library_data.version)
                        param_count += 1
                    if library_data.description is not None:
                        updates.append(f"description = ${param_count}")
                        values.append(library_data.description)
                        param_count += 1
                    if library_data.steps_definition is not None:
                        import json
                        updates.append(f"manifest = ${param_count}")
                        values.append(json.dumps(library_data.steps_definition))
                        param_count += 1
                    
                    if not updates:
                        raise HTTPException(status_code=400, detail="No fields to update")
                    
                    updates.append(f"updated_at = ${param_count}")
                    values.append(datetime.utcnow())
                    param_count += 1
                    values.append(library_id)
                    
                    query = f"""
                        UPDATE automation.step_libraries 
                        SET {', '.join(updates)}
                        WHERE id = ${param_count}
                        RETURNING id, name, version, description, manifest, is_active, is_builtin,
                                  created_by, created_at, updated_at
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail="Library not found")
                    
                    import json
                    library = StepLibrary(
                        id=row['id'],
                        name=row['name'],
                        version=row['version'],
                        description=row['description'],
                        manifest=json.loads(row['manifest']) if row['manifest'] else {},
                        is_active=row['is_active'],
                        is_builtin=row['is_builtin'],
                        created_by=row['created_by'],
                        created_at=row['created_at'].isoformat(),
                        updated_at=row['updated_at'].isoformat() if row['updated_at'] else None
                    )
                    
                    return {"success": True, "message": "Library updated", "data": library}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update library", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update library"
                )

        @self.app.delete("/libraries/{library_id}", response_model=dict)
        async def delete_library(library_id: int):
            """Delete library"""
            try:
                async with self.db.pool.acquire() as conn:
                    result = await conn.execute(
                        "DELETE FROM step_libraries WHERE id = $1", library_id
                    )
                    
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Library not found")
                    
                    return {"success": True, "message": "Library deleted"}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete library", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete library"
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
                        import json
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
                    
                    import json
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

if __name__ == "__main__":
    service = AutomationService()
    service.run()
