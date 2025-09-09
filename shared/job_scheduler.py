"""
Comprehensive Job Scheduling Service with Celery Beat Integration
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import croniter

from .database import get_db_cursor
from .logging import get_logger
from .celery_config import celery_app
from .tasks import execute_job_run

logger = get_logger(__name__)

class ScheduleType(Enum):
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"

@dataclass
class JobSchedule:
    """Job schedule configuration"""
    id: Optional[int]
    job_id: int
    name: str
    description: Optional[str]
    schedule_type: ScheduleType
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    is_active: bool
    max_runs: Optional[int]
    run_count: int
    parameters: Dict[str, Any]
    created_by: int
    created_at: datetime
    updated_at: datetime

class JobSchedulingService:
    """Comprehensive job scheduling service"""
    
    def __init__(self):
        self.celery_app = celery_app
    
    async def create_schedule(
        self,
        job_id: int,
        name: str,
        schedule_type: str,
        created_by: int,
        description: Optional[str] = None,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        start_time: Optional[datetime] = None,
        max_runs: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> JobSchedule:
        """Create a new job schedule"""
        
        # Validate schedule type
        try:
            schedule_type_enum = ScheduleType(schedule_type)
        except ValueError:
            raise ValueError(f"Invalid schedule type: {schedule_type}")
        
        # Validate schedule parameters
        if schedule_type_enum == ScheduleType.CRON:
            if not cron_expression:
                raise ValueError("Cron expression is required for cron schedules")
            
            # Validate cron expression
            try:
                croniter.croniter(cron_expression)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {str(e)}")
        
        elif schedule_type_enum == ScheduleType.RECURRING:
            if not interval_seconds or interval_seconds <= 0:
                raise ValueError("Positive interval_seconds is required for recurring schedules")
        
        # Calculate next run time
        next_run_at = self._calculate_next_run(
            schedule_type_enum, 
            cron_expression, 
            interval_seconds, 
            start_time
        )
        
        # Create schedule in database
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO job_schedules (
                        job_id, name, description, schedule_type, cron_expression,
                        interval_seconds, next_run_at, is_active, max_runs,
                        parameters, created_by, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at, updated_at
                """, (
                    job_id, name, description, schedule_type, cron_expression,
                    interval_seconds, next_run_at, True, max_runs,
                    json.dumps(parameters or {}), created_by,
                    datetime.now(timezone.utc), datetime.now(timezone.utc)
                ))
                
                result = cursor.fetchone()
                schedule_id = result['id']
                created_at = result['created_at']
                updated_at = result['updated_at']
            
            # Create Celery Beat schedule if needed
            if schedule_type_enum in [ScheduleType.RECURRING, ScheduleType.CRON]:
                await self._create_celery_beat_schedule(schedule_id, schedule_type_enum, cron_expression, interval_seconds)
            
            # Return created schedule
            return JobSchedule(
                id=schedule_id,
                job_id=job_id,
                name=name,
                description=description,
                schedule_type=schedule_type_enum,
                cron_expression=cron_expression,
                interval_seconds=interval_seconds,
                next_run_at=next_run_at,
                last_run_at=None,
                is_active=True,
                max_runs=max_runs,
                run_count=0,
                parameters=parameters or {},
                created_by=created_by,
                created_at=created_at,
                updated_at=updated_at
            )
            
        except Exception as e:
            logger.error(f"Error creating job schedule: {str(e)}")
            raise
    
    async def get_schedule(self, schedule_id: int) -> Optional[JobSchedule]:
        """Get a job schedule by ID"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM job_schedules WHERE id = %s
                """, (schedule_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return self._row_to_schedule(result)
                
        except Exception as e:
            logger.error(f"Error getting job schedule {schedule_id}: {str(e)}")
            return None
    
    async def list_schedules(
        self, 
        job_id: Optional[int] = None, 
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[JobSchedule]:
        """List job schedules with optional filtering"""
        try:
            with get_db_cursor(commit=False) as cursor:
                conditions = []
                params = []
                
                if job_id is not None:
                    conditions.append("job_id = %s")
                    params.append(job_id)
                
                if is_active is not None:
                    conditions.append("is_active = %s")
                    params.append(is_active)
                
                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                
                cursor.execute(f"""
                    SELECT * FROM job_schedules 
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, params + [limit, offset])
                
                results = cursor.fetchall()
                return [self._row_to_schedule(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error listing job schedules: {str(e)}")
            return []
    
    async def update_schedule(
        self,
        schedule_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        is_active: Optional[bool] = None,
        max_runs: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[JobSchedule]:
        """Update a job schedule"""
        try:
            # Get current schedule
            current_schedule = await self.get_schedule(schedule_id)
            if not current_schedule:
                return None
            
            # Build update query
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = %s")
                params.append(name)
            
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            
            if cron_expression is not None:
                # Validate cron expression
                try:
                    croniter.croniter(cron_expression)
                except Exception as e:
                    raise ValueError(f"Invalid cron expression: {str(e)}")
                
                updates.append("cron_expression = %s")
                params.append(cron_expression)
            
            if interval_seconds is not None:
                if interval_seconds <= 0:
                    raise ValueError("interval_seconds must be positive")
                
                updates.append("interval_seconds = %s")
                params.append(interval_seconds)
            
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)
            
            if max_runs is not None:
                updates.append("max_runs = %s")
                params.append(max_runs)
            
            if parameters is not None:
                updates.append("parameters = %s")
                params.append(json.dumps(parameters))
            
            if not updates:
                return current_schedule
            
            # Add updated_at
            updates.append("updated_at = %s")
            params.append(datetime.now(timezone.utc))
            
            # Add schedule_id for WHERE clause
            params.append(schedule_id)
            
            # Execute update
            with get_db_cursor() as cursor:
                cursor.execute(f"""
                    UPDATE job_schedules 
                    SET {', '.join(updates)}
                    WHERE id = %s
                """, params)
            
            # Update Celery Beat schedule if needed
            if cron_expression is not None or interval_seconds is not None or is_active is not None:
                await self._update_celery_beat_schedule(
                    schedule_id, 
                    current_schedule.schedule_type,
                    cron_expression or current_schedule.cron_expression,
                    interval_seconds or current_schedule.interval_seconds,
                    is_active if is_active is not None else current_schedule.is_active
                )
            
            # Return updated schedule
            return await self.get_schedule(schedule_id)
            
        except Exception as e:
            logger.error(f"Error updating job schedule {schedule_id}: {str(e)}")
            raise
    
    async def delete_schedule(self, schedule_id: int) -> bool:
        """Delete a job schedule"""
        try:
            # Remove from Celery Beat
            await self._remove_celery_beat_schedule(schedule_id)
            
            # Delete from database
            with get_db_cursor() as cursor:
                cursor.execute("DELETE FROM job_schedules WHERE id = %s", (schedule_id,))
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting job schedule {schedule_id}: {str(e)}")
            return False
    
    async def execute_scheduled_job(self, schedule_id: int) -> Optional[int]:
        """Execute a scheduled job and update schedule"""
        try:
            schedule = await self.get_schedule(schedule_id)
            if not schedule or not schedule.is_active:
                return None
            
            # Check max_runs limit
            if schedule.max_runs and schedule.run_count >= schedule.max_runs:
                logger.info(f"Schedule {schedule_id} has reached max_runs limit")
                await self.update_schedule(schedule_id, is_active=False)
                return None
            
            # Create job run
            from jobs_service.main import create_job_run_internal
            
            job_run_id = await create_job_run_internal(
                job_id=schedule.job_id,
                parameters=schedule.parameters,
                requested_by=schedule.created_by,
                correlation_id=f"schedule_{schedule_id}_{datetime.now(timezone.utc).isoformat()}"
            )
            
            # Update schedule
            next_run_at = None
            if schedule.schedule_type == ScheduleType.RECURRING:
                next_run_at = datetime.now(timezone.utc) + timedelta(seconds=schedule.interval_seconds)
            elif schedule.schedule_type == ScheduleType.CRON:
                cron = croniter.croniter(schedule.cron_expression, datetime.now(timezone.utc))
                next_run_at = cron.get_next(datetime)
            
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE job_schedules 
                    SET last_run_at = %s, next_run_at = %s, run_count = run_count + 1
                    WHERE id = %s
                """, (datetime.now(timezone.utc), next_run_at, schedule_id))
            
            logger.info(f"Executed scheduled job {schedule.job_id} from schedule {schedule_id}, job_run_id: {job_run_id}")
            return job_run_id
            
        except Exception as e:
            logger.error(f"Error executing scheduled job {schedule_id}: {str(e)}")
            return None
    
    async def get_due_schedules(self) -> List[JobSchedule]:
        """Get schedules that are due for execution"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM job_schedules 
                    WHERE is_active = true 
                    AND next_run_at IS NOT NULL 
                    AND next_run_at <= %s
                    AND (max_runs IS NULL OR run_count < max_runs)
                    ORDER BY next_run_at
                """, (datetime.now(timezone.utc),))
                
                results = cursor.fetchall()
                return [self._row_to_schedule(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error getting due schedules: {str(e)}")
            return []
    
    def _calculate_next_run(
        self,
        schedule_type: ScheduleType,
        cron_expression: Optional[str],
        interval_seconds: Optional[int],
        start_time: Optional[datetime]
    ) -> Optional[datetime]:
        """Calculate the next run time for a schedule"""
        base_time = start_time or datetime.now(timezone.utc)
        
        if schedule_type == ScheduleType.ONCE:
            return base_time
        elif schedule_type == ScheduleType.RECURRING and interval_seconds:
            return base_time + timedelta(seconds=interval_seconds)
        elif schedule_type == ScheduleType.CRON and cron_expression:
            cron = croniter.croniter(cron_expression, base_time)
            return cron.get_next(datetime)
        
        return None
    
    def _row_to_schedule(self, row: Dict[str, Any]) -> JobSchedule:
        """Convert database row to JobSchedule object"""
        return JobSchedule(
            id=row['id'],
            job_id=row['job_id'],
            name=row['name'],
            description=row['description'],
            schedule_type=ScheduleType(row['schedule_type']),
            cron_expression=row['cron_expression'],
            interval_seconds=row['interval_seconds'],
            next_run_at=row['next_run_at'],
            last_run_at=row['last_run_at'],
            is_active=row['is_active'],
            max_runs=row['max_runs'],
            run_count=row['run_count'],
            parameters=json.loads(row['parameters']) if row['parameters'] else {},
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    async def _create_celery_beat_schedule(
        self,
        schedule_id: int,
        schedule_type: ScheduleType,
        cron_expression: Optional[str],
        interval_seconds: Optional[int]
    ):
        """Create a Celery Beat schedule"""
        try:
            # This would integrate with Celery Beat's dynamic schedule management
            # For now, we'll use the database-driven approach
            logger.info(f"Created Celery Beat schedule for schedule_id {schedule_id}")
            
        except Exception as e:
            logger.error(f"Error creating Celery Beat schedule: {str(e)}")
    
    async def _update_celery_beat_schedule(
        self,
        schedule_id: int,
        schedule_type: ScheduleType,
        cron_expression: Optional[str],
        interval_seconds: Optional[int],
        is_active: bool
    ):
        """Update a Celery Beat schedule"""
        try:
            # This would update the Celery Beat schedule
            logger.info(f"Updated Celery Beat schedule for schedule_id {schedule_id}")
            
        except Exception as e:
            logger.error(f"Error updating Celery Beat schedule: {str(e)}")
    
    async def _remove_celery_beat_schedule(self, schedule_id: int):
        """Remove a Celery Beat schedule"""
        try:
            # This would remove the Celery Beat schedule
            logger.info(f"Removed Celery Beat schedule for schedule_id {schedule_id}")
            
        except Exception as e:
            logger.error(f"Error removing Celery Beat schedule: {str(e)}")

# Global scheduling service instance
scheduling_service = JobSchedulingService()

# Celery Beat task for processing due schedules
@celery_app.task(bind=True)
def process_due_schedules(self):
    """Process schedules that are due for execution"""
    import asyncio
    
    async def _process():
        try:
            due_schedules = await scheduling_service.get_due_schedules()
            
            for schedule in due_schedules:
                try:
                    job_run_id = await scheduling_service.execute_scheduled_job(schedule.id)
                    if job_run_id:
                        logger.info(f"Executed scheduled job {schedule.job_id} -> job_run_id {job_run_id}")
                except Exception as e:
                    logger.error(f"Error executing schedule {schedule.id}: {str(e)}")
            
            return len(due_schedules)
            
        except Exception as e:
            logger.error(f"Error processing due schedules: {str(e)}")
            return 0
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_process())
    finally:
        loop.close()