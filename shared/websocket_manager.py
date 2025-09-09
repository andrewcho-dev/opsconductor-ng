"""
WebSocket Manager for Real-time Job Monitoring
"""
import json
import asyncio
from typing import Dict, Set, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import weakref

from .logging import get_logger
from .job_monitoring import monitoring_service, JobRunMetrics

logger = get_logger(__name__)

@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: str
    data: Any
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))

class WebSocketManager:
    """Manages WebSocket connections for real-time job monitoring"""
    
    def __init__(self):
        # Store active connections by type
        self.connections: Dict[str, Set[Any]] = {
            'job_monitoring': set(),
            'queue_monitoring': set(),
            'worker_monitoring': set(),
            'system_health': set()
        }
        
        # Store job-specific subscriptions
        self.job_subscriptions: Dict[int, Set[Any]] = {}
        
        # Background tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        self.is_running = False
    
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_job_status()),
            asyncio.create_task(self._monitor_queue_metrics()),
            asyncio.create_task(self._monitor_worker_health()),
            asyncio.create_task(self._monitor_system_health())
        ]
        
        logger.info("WebSocket monitoring tasks started")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks"""
        self.is_running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        self.monitoring_tasks.clear()
        logger.info("WebSocket monitoring tasks stopped")
    
    def add_connection(self, websocket, connection_type: str = 'job_monitoring'):
        """Add a WebSocket connection"""
        if connection_type not in self.connections:
            self.connections[connection_type] = set()
        
        self.connections[connection_type].add(websocket)
        logger.info(f"Added WebSocket connection for {connection_type}. Total: {len(self.connections[connection_type])}")
    
    def remove_connection(self, websocket, connection_type: str = 'job_monitoring'):
        """Remove a WebSocket connection"""
        if connection_type in self.connections:
            self.connections[connection_type].discard(websocket)
            logger.info(f"Removed WebSocket connection for {connection_type}. Total: {len(self.connections[connection_type])}")
        
        # Remove from job subscriptions
        for job_id, subscribers in list(self.job_subscriptions.items()):
            subscribers.discard(websocket)
            if not subscribers:
                del self.job_subscriptions[job_id]
    
    def subscribe_to_job(self, websocket, job_run_id: int):
        """Subscribe a WebSocket to specific job updates"""
        if job_run_id not in self.job_subscriptions:
            self.job_subscriptions[job_run_id] = set()
        
        self.job_subscriptions[job_run_id].add(websocket)
        logger.info(f"Subscribed WebSocket to job run {job_run_id}")
    
    def unsubscribe_from_job(self, websocket, job_run_id: int):
        """Unsubscribe a WebSocket from specific job updates"""
        if job_run_id in self.job_subscriptions:
            self.job_subscriptions[job_run_id].discard(websocket)
            if not self.job_subscriptions[job_run_id]:
                del self.job_subscriptions[job_run_id]
        
        logger.info(f"Unsubscribed WebSocket from job run {job_run_id}")
    
    async def broadcast_to_type(self, connection_type: str, message: WebSocketMessage):
        """Broadcast message to all connections of a specific type"""
        if connection_type not in self.connections:
            return
        
        connections = self.connections[connection_type].copy()
        if not connections:
            return
        
        message_json = message.to_json()
        disconnected = set()
        
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {str(e)}")
                disconnected.add(websocket)
        
        # Remove disconnected WebSockets
        for websocket in disconnected:
            self.remove_connection(websocket, connection_type)
    
    async def broadcast_job_update(self, job_run_id: int, job_metrics: JobRunMetrics):
        """Broadcast job-specific update to subscribers"""
        if job_run_id not in self.job_subscriptions:
            return
        
        subscribers = self.job_subscriptions[job_run_id].copy()
        if not subscribers:
            return
        
        message = WebSocketMessage(
            type='job_update',
            data={
                'job_run_id': job_run_id,
                'status': job_metrics.status,
                'total_steps': job_metrics.total_steps,
                'completed_steps': job_metrics.completed_steps,
                'failed_steps': job_metrics.failed_steps,
                'running_steps': job_metrics.running_steps,
                'execution_time_ms': job_metrics.execution_time_ms,
                'worker_hostname': job_metrics.worker_hostname,
                'retry_count': job_metrics.retry_count
            }
        )
        
        message_json = message.to_json()
        disconnected = set()
        
        for websocket in subscribers:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send job update to WebSocket: {str(e)}")
                disconnected.add(websocket)
        
        # Remove disconnected WebSockets
        for websocket in disconnected:
            self.unsubscribe_from_job(websocket, job_run_id)
    
    async def _monitor_job_status(self):
        """Monitor job status changes and broadcast updates"""
        last_check = {}
        
        while self.is_running:
            try:
                # Get active job runs
                active_jobs = await monitoring_service.get_active_job_runs(limit=200)
                
                for job_metrics in active_jobs:
                    job_id = job_metrics.job_run_id
                    current_status = (
                        job_metrics.status,
                        job_metrics.completed_steps,
                        job_metrics.failed_steps,
                        job_metrics.running_steps
                    )
                    
                    # Check if status changed
                    if job_id not in last_check or last_check[job_id] != current_status:
                        last_check[job_id] = current_status
                        
                        # Broadcast to general job monitoring connections
                        await self.broadcast_to_type('job_monitoring', WebSocketMessage(
                            type='job_status_update',
                            data={
                                'job_run_id': job_id,
                                'status': job_metrics.status,
                                'metrics': asdict(job_metrics)
                            }
                        ))
                        
                        # Broadcast to job-specific subscribers
                        await self.broadcast_job_update(job_id, job_metrics)
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in job status monitoring: {str(e)}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _monitor_queue_metrics(self):
        """Monitor queue metrics and broadcast updates"""
        last_metrics = {}
        
        while self.is_running:
            try:
                queue_metrics = await monitoring_service.get_queue_metrics()
                
                current_metrics = {
                    q.queue_name: (q.pending_tasks, q.active_tasks, q.worker_count)
                    for q in queue_metrics
                }
                
                # Check if metrics changed significantly
                if current_metrics != last_metrics:
                    last_metrics = current_metrics
                    
                    await self.broadcast_to_type('queue_monitoring', WebSocketMessage(
                        type='queue_metrics_update',
                        data=[asdict(q) for q in queue_metrics]
                    ))
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in queue metrics monitoring: {str(e)}")
                await asyncio.sleep(10)
    
    async def _monitor_worker_health(self):
        """Monitor worker health and broadcast updates"""
        last_workers = {}
        
        while self.is_running:
            try:
                worker_metrics = await monitoring_service.get_worker_metrics()
                
                current_workers = {
                    w.hostname: (w.status, w.active_tasks, w.processed_tasks)
                    for w in worker_metrics
                }
                
                # Check if worker status changed
                if current_workers != last_workers:
                    last_workers = current_workers
                    
                    await self.broadcast_to_type('worker_monitoring', WebSocketMessage(
                        type='worker_health_update',
                        data=[asdict(w) for w in worker_metrics]
                    ))
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in worker health monitoring: {str(e)}")
                await asyncio.sleep(15)
    
    async def _monitor_system_health(self):
        """Monitor overall system health and broadcast updates"""
        last_health = None
        
        while self.is_running:
            try:
                health_summary = await monitoring_service.get_system_health_summary()
                
                # Check if health status changed
                current_health = health_summary.get('overall_health')
                if current_health != last_health:
                    last_health = current_health
                    
                    await self.broadcast_to_type('system_health', WebSocketMessage(
                        type='system_health_update',
                        data=health_summary
                    ))
                
                await asyncio.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                logger.error(f"Error in system health monitoring: {str(e)}")
                await asyncio.sleep(20)
    
    async def send_job_started_notification(self, job_run_id: int, job_name: str):
        """Send notification when a job starts"""
        message = WebSocketMessage(
            type='job_started',
            data={
                'job_run_id': job_run_id,
                'job_name': job_name,
                'message': f'Job "{job_name}" (Run #{job_run_id}) has started execution'
            }
        )
        
        await self.broadcast_to_type('job_monitoring', message)
        
        # Also send to job-specific subscribers
        if job_run_id in self.job_subscriptions:
            await self.broadcast_job_update(job_run_id, await monitoring_service.get_job_run_status(job_run_id))
    
    async def send_job_completed_notification(self, job_run_id: int, job_name: str, status: str):
        """Send notification when a job completes"""
        message = WebSocketMessage(
            type='job_completed',
            data={
                'job_run_id': job_run_id,
                'job_name': job_name,
                'status': status,
                'message': f'Job "{job_name}" (Run #{job_run_id}) has {status}'
            }
        )
        
        await self.broadcast_to_type('job_monitoring', message)
        
        # Also send to job-specific subscribers
        if job_run_id in self.job_subscriptions:
            job_metrics = await monitoring_service.get_job_run_status(job_run_id)
            if job_metrics:
                await self.broadcast_job_update(job_run_id, job_metrics)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        return {
            'total_connections': sum(len(conns) for conns in self.connections.values()),
            'connections_by_type': {
                conn_type: len(conns) for conn_type, conns in self.connections.items()
            },
            'job_subscriptions': len(self.job_subscriptions),
            'monitoring_tasks_running': len([t for t in self.monitoring_tasks if not t.done()]),
            'is_monitoring_active': self.is_running
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()