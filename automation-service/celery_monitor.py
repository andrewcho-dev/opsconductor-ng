#!/usr/bin/env python3
"""
Celery Monitoring and Management Module
Provides real-time visibility into Celery tasks, queues, and workers
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import Celery
from celery.events.state import State
from celery.events import EventReceiver
import asyncpg
import redis
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class TaskInfo:
    """Enhanced task information"""
    task_id: str
    name: str
    state: str
    received: Optional[datetime] = None
    started: Optional[datetime] = None
    succeeded: Optional[datetime] = None
    failed: Optional[datetime] = None
    retried: Optional[datetime] = None
    revoked: Optional[datetime] = None
    args: List = None
    kwargs: Dict = None
    result: Any = None
    exception: str = None
    traceback: str = None
    runtime: Optional[float] = None
    retries: int = 0
    eta: Optional[datetime] = None
    expires: Optional[datetime] = None
    queue: str = "default"
    worker: str = None
    routing_key: str = None
    
    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.kwargs is None:
            self.kwargs = {}

@dataclass
class WorkerInfo:
    """Worker status information"""
    hostname: str
    status: str  # online, offline, heartbeat
    active_tasks: int
    processed_tasks: int
    load_avg: List[float]
    last_heartbeat: datetime
    pool_processes: int
    pool_max_concurrency: int
    pool_max_memory_per_child: int

@dataclass
class QueueInfo:
    """Queue status information"""
    name: str
    length: int
    consumers: int
    messages_ready: int
    messages_unacknowledged: int

class CeleryMonitor:
    """Real-time Celery monitoring and management"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/3")
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/opsconductor")
        
        # Initialize Celery app for monitoring
        self.celery_app = Celery('automation-worker', broker=self.redis_url, backend=self.redis_url)
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
        )
        
        # Redis client for direct queue inspection
        self.redis_client = redis.from_url(self.redis_url)
        
        # Task state tracking
        self.state = State()
        self.tasks: Dict[str, TaskInfo] = {}
        self.workers: Dict[str, WorkerInfo] = {}
        self.queues: Dict[str, QueueInfo] = {}
        
        # Event receiver for real-time updates
        self.receiver = None
        self.monitoring = False
        
    async def start_monitoring(self):
        """Start real-time monitoring of Celery events"""
        if self.monitoring:
            return
            
        self.monitoring = True
        logger.info("Starting Celery monitoring...")
        
        # Start event monitoring in background (temporarily disable event monitoring)
        # asyncio.create_task(self._monitor_events())  # Disabled due to connection issues
        asyncio.create_task(self._monitor_queues())
        asyncio.create_task(self._monitor_workers())
        
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.receiver:
            self.receiver.should_stop = True
            
    async def _monitor_events(self):
        """Monitor Celery events in real-time"""
        try:
            # Run event monitoring in a separate thread to avoid blocking
            import threading
            
            def event_monitor_thread():
                try:
                    with self.celery_app.connection() as connection:
                        self.receiver = EventReceiver(connection, handlers={
                            'task-sent': self._on_task_sent,
                            'task-received': self._on_task_received,
                            'task-started': self._on_task_started,
                            'task-succeeded': self._on_task_succeeded,
                            'task-failed': self._on_task_failed,
                            'task-retried': self._on_task_retried,
                            'task-revoked': self._on_task_revoked,
                            'worker-online': self._on_worker_online,
                            'worker-offline': self._on_worker_offline,
                            'worker-heartbeat': self._on_worker_heartbeat,
                        })
                        
                        while self.monitoring:
                            try:
                                self.receiver.capture(limit=None, timeout=1.0, wakeup=True)
                            except Exception as e:
                                logger.error(f"Error in event monitoring: {e}")
                                import time
                                time.sleep(1)
                                
                except Exception as e:
                    logger.error(f"Failed to start event monitoring: {e}")
            
            # Start the event monitoring in a separate thread
            self.event_thread = threading.Thread(target=event_monitor_thread, daemon=True)
            self.event_thread.start()
            
            # Keep the async method alive while monitoring
            while self.monitoring:
                await asyncio.sleep(5)
                        
        except Exception as e:
            logger.error(f"Failed to start event monitoring: {e}")
            
    async def _monitor_queues(self):
        """Monitor queue statistics"""
        while self.monitoring:
            try:
                # Get queue information from Redis
                queue_names = ['celery', 'default', 'high_priority', 'low_priority']
                
                for queue_name in queue_names:
                    try:
                        # Get queue length
                        length = self.redis_client.llen(queue_name)
                        
                        # Update queue info
                        self.queues[queue_name] = QueueInfo(
                            name=queue_name,
                            length=length,
                            consumers=0,  # Would need RabbitMQ for this
                            messages_ready=length,
                            messages_unacknowledged=0
                        )
                    except Exception as e:
                        logger.warning(f"Error monitoring queue {queue_name}: {e}")
                        
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in queue monitoring: {e}")
                await asyncio.sleep(5)
                
    async def _monitor_workers(self):
        """Monitor worker statistics"""
        while self.monitoring:
            try:
                # Get active workers
                inspect = self.celery_app.control.inspect()
                
                # Get worker stats
                stats = inspect.stats()
                active = inspect.active()
                
                if stats:
                    for worker_name, worker_stats in stats.items():
                        active_tasks = len(active.get(worker_name, [])) if active else 0
                        
                        self.workers[worker_name] = WorkerInfo(
                            hostname=worker_name,
                            status="online",
                            active_tasks=active_tasks,
                            processed_tasks=worker_stats.get('total', {}).get('tasks.total', 0),
                            load_avg=worker_stats.get('rusage', {}).get('load_avg', [0, 0, 0]),
                            last_heartbeat=datetime.utcnow(),
                            pool_processes=worker_stats.get('pool', {}).get('processes', 0),
                            pool_max_concurrency=worker_stats.get('pool', {}).get('max-concurrency', 0),
                            pool_max_memory_per_child=worker_stats.get('pool', {}).get('max-memory-per-child', 0)
                        )
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in worker monitoring: {e}")
                await asyncio.sleep(10)
    
    # Event handlers
    def _on_task_sent(self, event):
        """Handle task-sent event"""
        task_id = event['uuid']
        self.tasks[task_id] = TaskInfo(
            task_id=task_id,
            name=event['name'],
            state='SENT',
            received=datetime.fromtimestamp(event['timestamp']),
            args=event.get('args', []),
            kwargs=event.get('kwargs', {}),
            eta=datetime.fromtimestamp(event['eta']) if event.get('eta') else None,
            expires=datetime.fromtimestamp(event['expires']) if event.get('expires') else None,
            queue=event.get('queue', 'default'),
            routing_key=event.get('routing_key', 'default')
        )
        
    def _on_task_received(self, event):
        """Handle task-received event"""
        task_id = event['uuid']
        if task_id in self.tasks:
            self.tasks[task_id].state = 'RECEIVED'
            self.tasks[task_id].received = datetime.fromtimestamp(event['timestamp'])
        
    def _on_task_started(self, event):
        """Handle task-started event"""
        task_id = event['uuid']
        if task_id in self.tasks:
            self.tasks[task_id].state = 'STARTED'
            self.tasks[task_id].started = datetime.fromtimestamp(event['timestamp'])
            self.tasks[task_id].worker = event.get('hostname')
            
    def _on_task_succeeded(self, event):
        """Handle task-succeeded event"""
        task_id = event['uuid']
        if task_id in self.tasks:
            self.tasks[task_id].state = 'SUCCESS'
            self.tasks[task_id].succeeded = datetime.fromtimestamp(event['timestamp'])
            self.tasks[task_id].result = event.get('result')
            self.tasks[task_id].runtime = event.get('runtime')
            
    def _on_task_failed(self, event):
        """Handle task-failed event"""
        task_id = event['uuid']
        if task_id in self.tasks:
            self.tasks[task_id].state = 'FAILURE'
            self.tasks[task_id].failed = datetime.fromtimestamp(event['timestamp'])
            self.tasks[task_id].exception = event.get('exception')
            self.tasks[task_id].traceback = event.get('traceback')
            
    def _on_task_retried(self, event):
        """Handle task-retried event"""
        task_id = event['uuid']
        if task_id in self.tasks:
            self.tasks[task_id].state = 'RETRY'
            self.tasks[task_id].retried = datetime.fromtimestamp(event['timestamp'])
            self.tasks[task_id].retries += 1
            
    def _on_task_revoked(self, event):
        """Handle task-revoked event"""
        task_id = event['uuid']
        if task_id in self.tasks:
            self.tasks[task_id].state = 'REVOKED'
            self.tasks[task_id].revoked = datetime.fromtimestamp(event['timestamp'])
            
    def _on_worker_online(self, event):
        """Handle worker-online event"""
        hostname = event['hostname']
        self.workers[hostname] = WorkerInfo(
            hostname=hostname,
            status="online",
            active_tasks=0,
            processed_tasks=0,
            load_avg=[0, 0, 0],
            last_heartbeat=datetime.fromtimestamp(event['timestamp']),
            pool_processes=0,
            pool_max_concurrency=0,
            pool_max_memory_per_child=0
        )
        
    def _on_worker_offline(self, event):
        """Handle worker-offline event"""
        hostname = event['hostname']
        if hostname in self.workers:
            self.workers[hostname].status = "offline"
            
    def _on_worker_heartbeat(self, event):
        """Handle worker-heartbeat event"""
        hostname = event['hostname']
        if hostname in self.workers:
            self.workers[hostname].last_heartbeat = datetime.fromtimestamp(event['timestamp'])
            self.workers[hostname].status = "online"
    
    # Public API methods
    async def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get detailed information about a specific task"""
        return self.tasks.get(task_id)
        
    async def get_all_tasks(self, limit: int = 100) -> List[TaskInfo]:
        """Get all tracked tasks"""
        tasks = list(self.tasks.values())
        return sorted(tasks, key=lambda t: t.received or datetime.min, reverse=True)[:limit]
        
    async def get_active_tasks(self, limit: int = 50) -> List[TaskInfo]:
        """Get currently active tasks"""
        active_tasks = [task for task in self.tasks.values() if task.state in ['SENT', 'RECEIVED', 'STARTED']]
        # Sort by received time and limit results for performance
        return sorted(active_tasks, key=lambda t: t.received or datetime.min, reverse=True)[:limit]
        
    async def get_worker_info(self) -> List[WorkerInfo]:
        """Get all worker information"""
        return list(self.workers.values())
        
    async def get_queue_info(self) -> List[QueueInfo]:
        """Get all queue information"""
        return list(self.queues.values())
        
    async def cancel_task(self, task_id: str, terminate: bool = False) -> bool:
        """Cancel a running task"""
        try:
            self.celery_app.control.revoke(task_id, terminate=terminate)
            
            # Update database status
            conn = await asyncpg.connect(self.db_url)
            try:
                await conn.execute("""
                    UPDATE automation.job_executions 
                    SET status = 'cancelled', completed_at = NOW(), error_message = 'Task cancelled by user'
                    WHERE execution_id = $1 AND status IN ('queued', 'running')
                """, task_id)
            finally:
                await conn.close()
                
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
            
    async def retry_task(self, task_id: str) -> bool:
        """Retry a failed task"""
        try:
            # Get original task info
            task_info = self.tasks.get(task_id)
            if not task_info:
                return False
                
            # Re-queue the task
            self.celery_app.send_task(
                task_info.name,
                args=task_info.args,
                kwargs=task_info.kwargs,
                queue=task_info.queue
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to retry task {task_id}: {e}")
            return False
            
    async def get_monitoring_stats(self) -> Dict:
        """Get comprehensive monitoring statistics"""
        active_tasks = await self.get_active_tasks()
        workers = await self.get_worker_info()
        queues = await self.get_queue_info()
        
        return {
            "tasks": {
                "total": len(self.tasks),
                "active": len(active_tasks),
                "by_state": self._count_tasks_by_state()
            },
            "workers": {
                "total": sum(w.pool_max_concurrency for w in workers),
                "online": sum(w.pool_max_concurrency for w in workers if w.status == "online"),
                "offline": sum(w.pool_max_concurrency for w in workers if w.status == "offline"),
                "nodes": len(workers),
                "online_nodes": len([w for w in workers if w.status == "online"])
            },
            "queues": {
                "total_length": sum(q.length for q in queues),
                "by_queue": {q.name: q.length for q in queues}
            }
        }
        
    def _count_tasks_by_state(self) -> Dict[str, int]:
        """Count tasks by their current state"""
        counts = {}
        for task in self.tasks.values():
            counts[task.state] = counts.get(task.state, 0) + 1
        return counts

# Global monitor instance
monitor = CeleryMonitor()