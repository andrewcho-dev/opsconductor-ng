"""
Comprehensive Job Monitoring and Status Tracking System
"""
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .database import get_db_cursor
from .logging import get_logger
from .celery_config import celery_app

logger = get_logger(__name__)

class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"

class StepStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABORTED = "aborted"

@dataclass
class JobRunMetrics:
    """Job run execution metrics"""
    job_run_id: int
    total_steps: int
    completed_steps: int
    failed_steps: int
    running_steps: int
    execution_time_ms: Optional[int]
    worker_hostname: Optional[str]
    queue_name: Optional[str]
    retry_count: int
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

@dataclass
class QueueMetrics:
    """Queue performance metrics"""
    queue_name: str
    pending_tasks: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_processing_time_ms: Optional[int]
    worker_count: int

@dataclass
class WorkerMetrics:
    """Celery worker metrics"""
    hostname: str
    worker_name: str
    status: str
    active_tasks: int
    processed_tasks: int
    failed_tasks: int
    last_heartbeat: datetime
    queues: List[str]
    load_average: Optional[float]
    memory_usage_mb: Optional[int]
    cpu_usage_percent: Optional[float]

class JobMonitoringService:
    """Comprehensive job monitoring and status tracking service"""
    
    def __init__(self):
        self.celery_app = celery_app
    
    async def get_job_run_status(self, job_run_id: int) -> Optional[JobRunMetrics]:
        """Get detailed status and metrics for a job run"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        jr.id,
                        jr.status,
                        jr.started_at,
                        jr.finished_at,
                        jr.execution_time_ms,
                        jr.worker_hostname,
                        jr.queue_name,
                        jr.retry_count,
                        COUNT(jrs.id) as total_steps,
                        COUNT(jrs.id) FILTER (WHERE jrs.status = 'succeeded') as completed_steps,
                        COUNT(jrs.id) FILTER (WHERE jrs.status = 'failed') as failed_steps,
                        COUNT(jrs.id) FILTER (WHERE jrs.status = 'running') as running_steps
                    FROM job_runs jr
                    LEFT JOIN job_run_steps jrs ON jr.id = jrs.job_run_id
                    WHERE jr.id = %s
                    GROUP BY jr.id, jr.status, jr.started_at, jr.finished_at, 
                             jr.execution_time_ms, jr.worker_hostname, jr.queue_name, jr.retry_count
                """, (job_run_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return JobRunMetrics(
                    job_run_id=result['id'],
                    total_steps=result['total_steps'] or 0,
                    completed_steps=result['completed_steps'] or 0,
                    failed_steps=result['failed_steps'] or 0,
                    running_steps=result['running_steps'] or 0,
                    execution_time_ms=result['execution_time_ms'],
                    worker_hostname=result['worker_hostname'],
                    queue_name=result['queue_name'],
                    retry_count=result['retry_count'] or 0,
                    status=result['status'],
                    started_at=result['started_at'],
                    finished_at=result['finished_at']
                )
                
        except Exception as e:
            logger.error(f"Error getting job run status for {job_run_id}: {str(e)}")
            return None
    
    async def get_active_job_runs(self, limit: int = 100) -> List[JobRunMetrics]:
        """Get all currently active (queued or running) job runs"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        jr.id,
                        jr.status,
                        jr.started_at,
                        jr.finished_at,
                        jr.execution_time_ms,
                        jr.worker_hostname,
                        jr.queue_name,
                        jr.retry_count,
                        COUNT(jrs.id) as total_steps,
                        COUNT(jrs.id) FILTER (WHERE jrs.status = 'succeeded') as completed_steps,
                        COUNT(jrs.id) FILTER (WHERE jrs.status = 'failed') as failed_steps,
                        COUNT(jrs.id) FILTER (WHERE jrs.status = 'running') as running_steps
                    FROM job_runs jr
                    LEFT JOIN job_run_steps jrs ON jr.id = jrs.job_run_id
                    WHERE jr.status IN ('queued', 'running')
                    GROUP BY jr.id, jr.status, jr.started_at, jr.finished_at, 
                             jr.execution_time_ms, jr.worker_hostname, jr.queue_name, jr.retry_count
                    ORDER BY jr.queued_at DESC
                    LIMIT %s
                """, (limit,))
                
                results = cursor.fetchall()
                return [
                    JobRunMetrics(
                        job_run_id=row['id'],
                        total_steps=row['total_steps'] or 0,
                        completed_steps=row['completed_steps'] or 0,
                        failed_steps=row['failed_steps'] or 0,
                        running_steps=row['running_steps'] or 0,
                        execution_time_ms=row['execution_time_ms'],
                        worker_hostname=row['worker_hostname'],
                        queue_name=row['queue_name'],
                        retry_count=row['retry_count'] or 0,
                        status=row['status'],
                        started_at=row['started_at'],
                        finished_at=row['finished_at']
                    )
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error getting active job runs: {str(e)}")
            return []
    
    async def get_queue_metrics(self) -> List[QueueMetrics]:
        """Get performance metrics for all queues"""
        try:
            # Get database metrics
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT 
                        COALESCE(queue_name, 'celery') as queue_name,
                        COUNT(*) FILTER (WHERE status = 'queued') as pending_tasks,
                        COUNT(*) FILTER (WHERE status = 'running') as active_tasks,
                        COUNT(*) FILTER (WHERE status = 'succeeded') as completed_tasks,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
                        AVG(execution_time_ms)::INTEGER as avg_processing_time_ms
                    FROM job_runs 
                    WHERE queued_at > NOW() - INTERVAL '24 hours'
                    GROUP BY queue_name
                """)
                
                db_metrics = cursor.fetchall()
            
            # Get Celery worker metrics
            worker_metrics = await self.get_worker_metrics()
            queue_worker_count = {}
            
            for worker in worker_metrics:
                for queue in worker.queues:
                    queue_worker_count[queue] = queue_worker_count.get(queue, 0) + 1
            
            # Combine metrics
            queue_metrics = []
            for row in db_metrics:
                queue_metrics.append(QueueMetrics(
                    queue_name=row['queue_name'],
                    pending_tasks=row['pending_tasks'] or 0,
                    active_tasks=row['active_tasks'] or 0,
                    completed_tasks=row['completed_tasks'] or 0,
                    failed_tasks=row['failed_tasks'] or 0,
                    avg_processing_time_ms=row['avg_processing_time_ms'],
                    worker_count=queue_worker_count.get(row['queue_name'], 0)
                ))
            
            return queue_metrics
            
        except Exception as e:
            logger.error(f"Error getting queue metrics: {str(e)}")
            return []
    
    async def get_worker_metrics(self) -> List[WorkerMetrics]:
        """Get metrics for all Celery workers"""
        try:
            # Get worker stats from Celery
            inspect = self.celery_app.control.inspect()
            
            # Get active workers
            active_workers = inspect.active() or {}
            stats = inspect.stats() or {}
            registered_tasks = inspect.registered() or {}
            
            worker_metrics = []
            
            for worker_name, worker_stats in stats.items():
                # Parse worker hostname
                hostname = worker_name.split('@')[1] if '@' in worker_name else worker_name
                
                # Get active tasks for this worker
                active_tasks = active_workers.get(worker_name, [])
                
                # Get registered queues (from task routing)
                queues = list(registered_tasks.get(worker_name, {}).keys()) if registered_tasks.get(worker_name) else ['celery']
                
                worker_metrics.append(WorkerMetrics(
                    hostname=hostname,
                    worker_name=worker_name,
                    status='online',  # If we can get stats, worker is online
                    active_tasks=len(active_tasks),
                    processed_tasks=worker_stats.get('total', {}).get('tasks.received', 0),
                    failed_tasks=worker_stats.get('total', {}).get('tasks.failed', 0),
                    last_heartbeat=datetime.now(timezone.utc),  # Approximate
                    queues=queues,
                    load_average=None,  # Would need system monitoring
                    memory_usage_mb=None,  # Would need system monitoring
                    cpu_usage_percent=None  # Would need system monitoring
                ))
            
            # Update database with worker metrics
            await self._update_worker_metrics_db(worker_metrics)
            
            return worker_metrics
            
        except Exception as e:
            logger.error(f"Error getting worker metrics: {str(e)}")
            return []
    
    async def _update_worker_metrics_db(self, worker_metrics: List[WorkerMetrics]):
        """Update worker metrics in database"""
        try:
            with get_db_cursor() as cursor:
                for worker in worker_metrics:
                    cursor.execute("""
                        INSERT INTO celery_workers (
                            hostname, worker_name, queues, status, last_heartbeat,
                            active_tasks, processed_tasks, failed_tasks, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (hostname) DO UPDATE SET
                            worker_name = EXCLUDED.worker_name,
                            queues = EXCLUDED.queues,
                            status = EXCLUDED.status,
                            last_heartbeat = EXCLUDED.last_heartbeat,
                            active_tasks = EXCLUDED.active_tasks,
                            processed_tasks = EXCLUDED.processed_tasks,
                            failed_tasks = EXCLUDED.failed_tasks,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        worker.hostname,
                        worker.worker_name,
                        worker.queues,
                        worker.status,
                        worker.last_heartbeat,
                        worker.active_tasks,
                        worker.processed_tasks,
                        worker.failed_tasks,
                        datetime.now(timezone.utc)
                    ))
                    
        except Exception as e:
            logger.error(f"Error updating worker metrics in database: {str(e)}")
    
    async def get_job_execution_history(
        self, 
        job_id: Optional[int] = None, 
        hours: int = 24, 
        limit: int = 100
    ) -> List[JobRunMetrics]:
        """Get job execution history"""
        try:
            with get_db_cursor(commit=False) as cursor:
                if job_id:
                    cursor.execute("""
                        SELECT 
                            jr.id,
                            jr.status,
                            jr.started_at,
                            jr.finished_at,
                            jr.execution_time_ms,
                            jr.worker_hostname,
                            jr.queue_name,
                            jr.retry_count,
                            COUNT(jrs.id) as total_steps,
                            COUNT(jrs.id) FILTER (WHERE jrs.status = 'succeeded') as completed_steps,
                            COUNT(jrs.id) FILTER (WHERE jrs.status = 'failed') as failed_steps,
                            COUNT(jrs.id) FILTER (WHERE jrs.status = 'running') as running_steps
                        FROM job_runs jr
                        LEFT JOIN job_run_steps jrs ON jr.id = jrs.job_run_id
                        WHERE jr.job_id = %s AND jr.queued_at > NOW() - INTERVAL '%s hours'
                        GROUP BY jr.id, jr.status, jr.started_at, jr.finished_at, 
                                 jr.execution_time_ms, jr.worker_hostname, jr.queue_name, jr.retry_count
                        ORDER BY jr.queued_at DESC
                        LIMIT %s
                    """, (job_id, hours, limit))
                else:
                    cursor.execute("""
                        SELECT 
                            jr.id,
                            jr.status,
                            jr.started_at,
                            jr.finished_at,
                            jr.execution_time_ms,
                            jr.worker_hostname,
                            jr.queue_name,
                            jr.retry_count,
                            COUNT(jrs.id) as total_steps,
                            COUNT(jrs.id) FILTER (WHERE jrs.status = 'succeeded') as completed_steps,
                            COUNT(jrs.id) FILTER (WHERE jrs.status = 'failed') as failed_steps,
                            COUNT(jrs.id) FILTER (WHERE jrs.status = 'running') as running_steps
                        FROM job_runs jr
                        LEFT JOIN job_run_steps jrs ON jr.id = jrs.job_run_id
                        WHERE jr.queued_at > NOW() - INTERVAL '%s hours'
                        GROUP BY jr.id, jr.status, jr.started_at, jr.finished_at, 
                                 jr.execution_time_ms, jr.worker_hostname, jr.queue_name, jr.retry_count
                        ORDER BY jr.queued_at DESC
                        LIMIT %s
                    """, (hours, limit))
                
                results = cursor.fetchall()
                return [
                    JobRunMetrics(
                        job_run_id=row['id'],
                        total_steps=row['total_steps'] or 0,
                        completed_steps=row['completed_steps'] or 0,
                        failed_steps=row['failed_steps'] or 0,
                        running_steps=row['running_steps'] or 0,
                        execution_time_ms=row['execution_time_ms'],
                        worker_hostname=row['worker_hostname'],
                        queue_name=row['queue_name'],
                        retry_count=row['retry_count'] or 0,
                        status=row['status'],
                        started_at=row['started_at'],
                        finished_at=row['finished_at']
                    )
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error getting job execution history: {str(e)}")
            return []
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        try:
            # Get active job runs
            active_jobs = await self.get_active_job_runs(limit=1000)
            
            # Get queue metrics
            queue_metrics = await self.get_queue_metrics()
            
            # Get worker metrics
            worker_metrics = await self.get_worker_metrics()
            
            # Calculate health scores
            total_workers = len(worker_metrics)
            online_workers = len([w for w in worker_metrics if w.status == 'online'])
            
            total_queued = sum(q.pending_tasks for q in queue_metrics)
            total_running = sum(q.active_tasks for q in queue_metrics)
            total_failed_24h = sum(q.failed_tasks for q in queue_metrics)
            
            # Health status determination
            worker_health = 'healthy' if online_workers >= total_workers * 0.8 else 'degraded'
            queue_health = 'healthy' if total_queued < 100 else 'degraded'
            
            overall_health = 'healthy'
            if worker_health == 'degraded' or queue_health == 'degraded':
                overall_health = 'degraded'
            if online_workers == 0:
                overall_health = 'critical'
            
            return {
                'overall_health': overall_health,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'workers': {
                    'total': total_workers,
                    'online': online_workers,
                    'health': worker_health
                },
                'queues': {
                    'total_queued': total_queued,
                    'total_running': total_running,
                    'total_failed_24h': total_failed_24h,
                    'health': queue_health
                },
                'jobs': {
                    'active_runs': len(active_jobs),
                    'queued_runs': len([j for j in active_jobs if j.status == 'queued']),
                    'running_runs': len([j for j in active_jobs if j.status == 'running'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system health summary: {str(e)}")
            return {
                'overall_health': 'unknown',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }

# Global monitoring service instance
monitoring_service = JobMonitoringService()