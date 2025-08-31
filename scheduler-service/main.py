#!/usr/bin/env python3

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx
import pytz
from croniter import croniter
import requests

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Scheduler Service", version="1.0.0")

# Security
security = HTTPBearer()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "opsconductor"),
    "user": os.getenv("DB_USER", "opsconductor"),
    "password": os.getenv("DB_PASSWORD", "opsconductor123")
}

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3001")
JOBS_SERVICE_URL = os.getenv("JOBS_SERVICE_URL", "http://jobs-service:3006")

# Global scheduler state
scheduler_running = False
scheduler_task = None

def get_db_connection():
    """Get database connection with RealDictCursor"""
    return psycopg2.connect(
        cursor_factory=RealDictCursor,
        **DB_CONFIG
    )

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
            conn = get_db_connection()
            cursor = conn.cursor()
            
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
                    
                    conn.commit()
                    logger.info(f"Updated schedule {schedule_id}, next run: {next_run}")
                    
                except Exception as e:
                    logger.error(f"Error updating schedule {schedule_id}: {e}")
                    conn.rollback()
            
            conn.close()
            
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
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Count active schedules
        cursor.execute("SELECT COUNT(*) as count FROM schedules WHERE is_active = true")
        active_count = cursor.fetchone()["count"]
        
        # Get next execution time
        cursor.execute("""
            SELECT MIN(next_run_at) as next_run 
            FROM schedules 
            WHERE is_active = true AND next_run_at > NOW()
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduler status"
        )
    finally:
        conn.close()

@app.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Create a new job schedule"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Validate cron expression and calculate next run
        next_run = calculate_next_run(schedule_data.cron, schedule_data.timezone)
        
        # Verify job exists (excluding soft-deleted)
        cursor.execute("SELECT id FROM jobs WHERE id = %s AND deleted_at IS NULL", (schedule_data.job_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
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
        conn.commit()
        
        logger.info(f"Created schedule {schedule['id']} for job {schedule_data.job_id}")
        return ScheduleResponse(**schedule)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule"
        )
    finally:
        conn.close()

@app.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(
    skip: int = 0,
    limit: int = 10,
    job_id: Optional[int] = None,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """List job schedules with pagination"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedules"
        )
    finally:
        conn.close()

@app.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: dict = Depends(verify_token_with_auth_service)
):
    """Get schedule by ID"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, job_id, cron, timezone, next_run_at, last_run_at, is_active, created_at
            FROM schedules WHERE id = %s AND deleted_at IS NULL
        """, (schedule_id,))
        
        schedule = cursor.fetchone()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        return ScheduleResponse(**schedule)
        
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedule"
        )
    finally:
        conn.close()

@app.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Update schedule"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get current schedule
        cursor.execute("""
            SELECT id, job_id, cron, timezone, next_run_at, last_run_at, is_active, created_at
            FROM schedules WHERE id = %s AND deleted_at IS NULL
        """, (schedule_id,))
        
        current_schedule = cursor.fetchone()
        if not current_schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
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
        conn.commit()
        
        logger.info(f"Updated schedule {schedule_id}")
        return ScheduleResponse(**updated_schedule)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule"
        )
    finally:
        conn.close()

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Delete schedule"""
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Soft delete schedule
        cursor.execute(
            "UPDATE schedules SET deleted_at = %s WHERE id = %s AND deleted_at IS NULL RETURNING id",
            (datetime.utcnow(), schedule_id)
        )
        deleted = cursor.fetchone()
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found or already deleted"
            )
        
        conn.commit()
        logger.info(f"Soft deleted schedule {schedule_id}")
        return {"message": "Schedule deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule"
        )
    finally:
        conn.close()

@app.post("/scheduler/start")
async def start_scheduler(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin_or_operator_role)
):
    """Start the scheduler worker"""
    
    global scheduler_running, scheduler_task
    
    if scheduler_running:
        return {"message": "Scheduler is already running"}
    
    scheduler_running = True
    scheduler_task = asyncio.create_task(scheduler_worker())
    
    logger.info("Scheduler started")
    return {"message": "Scheduler started successfully"}

@app.post("/scheduler/stop")
async def stop_scheduler(current_user: dict = Depends(require_admin_or_operator_role)):
    """Stop the scheduler worker"""
    
    global scheduler_running, scheduler_task
    
    if not scheduler_running:
        return {"message": "Scheduler is not running"}
    
    scheduler_running = False
    
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        scheduler_task = None
    
    logger.info("Scheduler stopped")
    return {"message": "Scheduler stopped successfully"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Start scheduler on service startup"""
    global scheduler_running, scheduler_task
    
    logger.info("Starting scheduler service...")
    
    # Auto-start scheduler
    scheduler_running = True
    scheduler_task = asyncio.create_task(scheduler_worker())
    
    logger.info("Scheduler service started with auto-scheduler enabled")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on service shutdown"""
    global scheduler_running, scheduler_task
    
    logger.info("Shutting down scheduler service...")
    
    scheduler_running = False
    
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Scheduler service shut down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3008)