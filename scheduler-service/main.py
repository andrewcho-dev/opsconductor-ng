#!/usr/bin/env python3

import os
import json
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx
import pytz
from croniter import croniter

import sys
sys.path.append('/home/opsconductor')

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from pydantic import BaseModel, Field

# Import shared modules
from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from shared.logging import setup_service_logging, get_logger, log_startup, log_shutdown
from shared.middleware import add_standard_middleware
from shared.models import HealthResponse, HealthCheck, create_success_response
from shared.errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error
from shared.auth import get_current_user, require_admin
from shared.utils import get_service_client

# Setup structured logging
setup_service_logging("scheduler-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("scheduler-service")

app = FastAPI(
    title="Scheduler Service", 
    version="1.0.0",
    description="Job scheduling service with cron-based execution"
)

# Add standard middleware
add_standard_middleware(app, "scheduler-service", version="1.0.0")

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")
JOBS_SERVICE_URL = os.getenv("JOBS_SERVICE_URL", "http://jobs-service:3006")

# Global scheduler state
scheduler_running = False
scheduler_task = None

# Database connection now handled by shared module

# Pydantic models
class ScheduleCreate(BaseModel):
    job_id: int
    cron: str = Field(..., description="Cron expression (e.g., '0 9 * * 1-5')")
    timezone: str = Field(default="America/Los_Angeles", description="Timezone for cron execution")
    is_active: bool = Field(default=True)

class ScheduleUpdate(BaseModel):
    cron: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None

class ScheduleResponse(BaseModel):
    id: int
    job_id: int
    cron: str
    timezone: str
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    is_active: bool
    created_at: datetime

class ScheduleListResponse(BaseModel):
    schedules: List[ScheduleResponse]
    total: int

class SchedulerStatusResponse(BaseModel):
    scheduler_running: bool
    active_schedules: int
    next_execution: Optional[datetime]
    last_check: Optional[datetime]

# Authentication
def verify_token_with_auth_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with auth service"""
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/verify", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise AuthError("Invalid token")
            
        return response.json()["user"]
        
    except requests.RequestException:
        raise ServiceCommunicationError("unknown", "Auth service unavailable")

def require_admin_or_operator_role(current_user: dict = Depends(verify_token_with_auth_service)):
    """Require admin or operator role"""
    if current_user["role"] not in ["admin", "operator"]:
        raise PermissionError("Admin or operator role required")
    return current_user

def calculate_next_run(cron_expr: str, timezone_str: str) -> datetime:
    """Calculate next run time for cron expression"""
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        cron = croniter(cron_expr, now)
        next_run = cron.get_next(datetime)
        return next_run.astimezone(pytz.UTC)
    except Exception as e:
        logger.error(f"Error calculating next run: {e}")
        raise ValueError(f"Invalid cron expression or timezone: {e}")

async def execute_scheduled_job(job_id: int, schedule_id: int):
    """Execute a scheduled job by calling the jobs service"""
    try:
        async with httpx.AsyncClient() as client:
            # Get admin token for service-to-service communication
            auth_response = await client.post(
                f"{AUTH_SERVICE_URL}/login",
                json={"username": "admin", "password": "admin123"}
            )
            
            if auth_response.status_code != 200:
                logger.error("Failed to get admin token for scheduled job execution")
                return
            
            token = auth_response.json()["access_token"]
            
            # Execute the job
            job_response = await client.post(
                f"{JOBS_SERVICE_URL}/jobs/{job_id}/run",
                headers={"Authorization": f"Bearer {token}"},
                json={"scheduled": True, "schedule_id": schedule_id}
            )
            
            if job_response.status_code == 200:
                logger.info(f"Successfully executed scheduled job {job_id}")
            else:
                logger.error(f"Failed to execute scheduled job {job_id}: {job_response.text}")
                
    except Exception as e:
        logger.error(f"Error executing scheduled job {job_id}: {e}")

async def scheduler_worker():
    """Background worker that checks for scheduled jobs"""
    global scheduler_running
    
    logger.info("Scheduler worker started")
    
    while scheduler_running:
        try:
            with get_db_cursor() as cursor:
                
                # Get schedules that need to run
                now = datetime.now(timezone.utc)
                cursor.execute("""
                    SELECT id, job_id, cron, timezone, next_run_at
                    FROM schedules 
                    WHERE is_active = true 
                    AND deleted_at IS NULL
                    AND next_run_at <= %s
                    ORDER BY next_run_at
                """, (now,))
                
                due_schedules = cursor.fetchall()
                
                for schedule in due_schedules:
                    schedule_id = schedule["id"]
                    job_id = schedule["job_id"]
                    cron_expr = schedule["cron"]
                    timezone_str = schedule["timezone"]
                    
                    logger.info(f"Executing scheduled job {job_id} (schedule {schedule_id})")
                    
                    # Execute the job
                    await execute_scheduled_job(job_id, schedule_id)
                    
                    # Calculate next run time
                    try:
                        next_run = calculate_next_run(cron_expr, timezone_str)
                        
                        # Update schedule with next run time and last run time
                        cursor.execute("""
                            UPDATE schedules 
                            SET next_run_at = %s, last_run_at = %s
                            WHERE id = %s
                        """, (next_run, now, schedule_id))
                        
                        logger.info(f"Updated schedule {schedule_id}, next run: {next_run}")
                        
                    except Exception as e:
                        logger.error(f"Error updating schedule {schedule_id}: {e}")
            
        except Exception as e:
            logger.error(f"Scheduler worker error: {e}")
        
        # Wait 30 seconds before next check
        await asyncio.sleep(30)
    
    logger.info("Scheduler worker stopped")

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "scheduler"}

@app.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        with get_db_cursor(commit=False) as cursor:
            
            # Count active schedules
            cursor.execute("SELECT COUNT(*) as count FROM schedules WHERE is_active = true AND deleted_at IS NULL")
            active_count = cursor.fetchone()["count"]
            
            # Get next execution time
            cursor.execute("""
                SELECT MIN(next_run_at) as next_run 
                FROM schedules 
                WHERE is_active = true AND deleted_at IS NULL AND next_run_at > NOW()
            """)
            next_run_result = cursor.fetchone()
            next_execution = next_run_result["next_run"] if next_run_result else None
            
            return SchedulerStatusResponse(
                scheduler_running=scheduler_running,
                active_schedules=active_count,
                next_execution=next_execution,
                last_check=datetime.now(timezone.utc)
            )
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise DatabaseError("Failed to get scheduler status")

@app.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create a new job schedule"""
    
    try:
        with get_db_cursor() as cursor:
            
            # Validate cron expression and calculate next run
            next_run = calculate_next_run(schedule_data.cron, schedule_data.timezone)
            
            # Verify job exists (excluding soft-deleted)
            cursor.execute("SELECT id FROM jobs WHERE id = %s AND deleted_at IS NULL", (schedule_data.job_id,))
            if not cursor.fetchone():
                raise NotFoundError("Job not found")
            
            # Generate schedule name
            schedule_name = f"schedule-job-{schedule_data.job_id}-{int(datetime.now().timestamp())}"
            
            # Create schedule
            cursor.execute("""
                INSERT INTO schedules (job_id, name, cron_expression, cron, timezone, next_run_at, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, job_id, cron, timezone, next_run_at, last_run_at, is_active, created_at
            """, (
                schedule_data.job_id,
                schedule_name,
                schedule_data.cron,
                schedule_data.cron,
                schedule_data.timezone,
                next_run,
                schedule_data.is_active
            ))
            
            schedule = cursor.fetchone()
            
            logger.info(f"Created schedule {schedule['id']} for job {schedule_data.job_id}")
            return ScheduleResponse(**schedule)
        
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        raise DatabaseError("Failed to create schedule")

@app.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(
    skip: int = 0,
    limit: int = 10,
    job_id: Optional[int] = None,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List job schedules with pagination"""
    
    try:
        with get_db_cursor(commit=False) as cursor:
            
            # Build query with optional job_id filter and soft delete exclusion
            if job_id is not None:
                where_clause = "WHERE job_id = %s AND deleted_at IS NULL"
                params = [job_id]
            else:
                where_clause = "WHERE deleted_at IS NULL"
                params = []
            
            # Get total count
            count_query = f"SELECT COUNT(*) as count FROM schedules {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()["count"]
            
            # Get schedules with pagination
            query = f"""
                SELECT id, job_id, cron, timezone, next_run_at, last_run_at, is_active, created_at
                FROM schedules {where_clause}
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            params.extend([limit, skip])
            cursor.execute(query, params)
            schedules = cursor.fetchall()
            
            return ScheduleListResponse(
                schedules=[ScheduleResponse(**schedule) for schedule in schedules],
                total=total
            )
        
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        raise DatabaseError("Failed to retrieve schedules")

@app.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get schedule by ID"""
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, job_id, cron, timezone, next_run_at, last_run_at, is_active, created_at
                FROM schedules WHERE id = %s AND deleted_at IS NULL
            """, (schedule_id,))
            
            schedule = cursor.fetchone()
            if not schedule:
                raise NotFoundError("Schedule not found")
            
            return ScheduleResponse(**schedule)
        
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        raise DatabaseError("Failed to retrieve schedule")

@app.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update schedule"""
    
    try:
        with get_db_cursor() as cursor:
            
            # Get current schedule
            cursor.execute("""
                SELECT id, job_id, cron, timezone, next_run_at, last_run_at, is_active, created_at
                FROM schedules WHERE id = %s AND deleted_at IS NULL
            """, (schedule_id,))
            
            current_schedule = cursor.fetchone()
            if not current_schedule:
                raise NotFoundError("Schedule not found")
            
            # Prepare update data
            update_fields = []
            update_values = []
            
            if schedule_data.cron is not None:
                update_fields.append("cron = %s")
                update_values.append(schedule_data.cron)
            
            if schedule_data.timezone is not None:
                update_fields.append("timezone = %s")
                update_values.append(schedule_data.timezone)
            
            if schedule_data.is_active is not None:
                update_fields.append("is_active = %s")
                update_values.append(schedule_data.is_active)
            
            # Recalculate next_run_at if cron or timezone changed
            if schedule_data.cron is not None or schedule_data.timezone is not None:
                new_cron = schedule_data.cron or current_schedule["cron"]
                new_timezone = schedule_data.timezone or current_schedule["timezone"]
                next_run = calculate_next_run(new_cron, new_timezone)
                update_fields.append("next_run_at = %s")
                update_values.append(next_run)
            
            if not update_fields:
                # No changes, return current schedule
                return ScheduleResponse(**current_schedule)
            
            # Perform update
            update_values.append(schedule_id)
            update_query = f"""
                UPDATE schedules 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, job_id, cron, timezone, next_run_at, last_run_at, is_active, created_at
            """
            
            cursor.execute(update_query, update_values)
            updated_schedule = cursor.fetchone()
            
            logger.info(f"Updated schedule {schedule_id}")
            return ScheduleResponse(**updated_schedule)
        
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        raise DatabaseError("Failed to update schedule")

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete schedule"""
    
    try:
        with get_db_cursor() as cursor:
            
            # Soft delete schedule
            cursor.execute(
                "UPDATE schedules SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL RETURNING id",
                (datetime.utcnow(), schedule_id)
            )
            deleted = cursor.fetchone()
            
            if not deleted:
                raise NotFoundError("Schedule not found or already deleted")
            
            logger.info(f"Soft deleted schedule {schedule_id}")
            return create_success_response(
                message="Schedule deleted successfully",
                data={"schedule_id": schedule_id}
            )
        
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        raise DatabaseError("Failed to delete schedule")

@app.post("/scheduler/start")
async def start_scheduler(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Start the scheduler worker"""
    
    global scheduler_running, scheduler_task
    
    if scheduler_running:
        return create_success_response(
            message="Scheduler is already running",
            data={"status": "running"}
        )
    
    scheduler_running = True
    scheduler_task = asyncio.create_task(scheduler_worker())
    
    logger.info("Scheduler started")
    return create_success_response(
        message="Scheduler started successfully",
        data={"status": "started"}
    )

@app.post("/scheduler/stop")
async def stop_scheduler(current_user: dict = Depends(require_admin_or_operator_role)):
    """Stop the scheduler worker"""
    
    global scheduler_running, scheduler_task
    
    if not scheduler_running:
        return create_success_response(
            message="Scheduler is not running",
            data={"status": "stopped"}
        )
    
    scheduler_running = False
    
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        scheduler_task = None
    
    logger.info("Scheduler stopped")
    return create_success_response(
        message="Scheduler stopped successfully",
        data={"status": "stopped"}
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_health = check_database_health()
    
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        ),
        HealthCheck(
            name="scheduler_worker",
            status="healthy" if scheduler_running else "unhealthy",
            message="Scheduler worker status"
        )
    ]
    
    overall_status = "healthy" if db_health["status"] == "healthy" and scheduler_running else "unhealthy"
    
    return HealthResponse(
        service="scheduler-service",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Start scheduler on service startup"""
    global scheduler_running, scheduler_task
    
    # Log service startup
    log_startup("scheduler-service", "1.0.0", 3008)
    
    # Auto-start scheduler
    scheduler_running = True
    scheduler_task = asyncio.create_task(scheduler_worker())
    
    logger.info("Scheduler service started with auto-scheduler enabled")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on service shutdown"""
    global scheduler_running, scheduler_task
    
    scheduler_running = False
    
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
    
    log_shutdown("scheduler-service")
    cleanup_database_pool()
    logger.info("Scheduler service shut down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3008)