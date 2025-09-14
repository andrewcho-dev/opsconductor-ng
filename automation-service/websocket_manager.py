#!/usr/bin/env python3
"""
WebSocket Manager for Real-time Job Monitoring
Provides real-time updates to frontend clients
"""

import json
import asyncio
import logging
from typing import Dict, Set, List, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import asdict
try:
    from .celery_monitor import monitor, TaskInfo, WorkerInfo, QueueInfo
except ImportError:
    # Fallback for direct execution
    from celery_monitor import monitor, TaskInfo, WorkerInfo, QueueInfo

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active connections by connection ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Subscriptions by topic
        self.subscriptions: Dict[str, Set[str]] = {
            "tasks": set(),
            "workers": set(), 
            "queues": set(),
            "jobs": set(),
            "system": set()
        }
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict] = {}
        
        # Broadcasting task
        self.broadcast_task = None
        self.broadcasting = False
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info(f"WebSocket connection established: {connection_id}")
        
        # Send initial data
        await self._send_initial_data(websocket)
        
        # Start broadcasting if this is the first connection
        if len(self.active_connections) == 1 and not self.broadcasting:
            await self.start_broadcasting()
            
    async def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
            
        # Remove from all subscriptions
        for topic_subscribers in self.subscriptions.values():
            topic_subscribers.discard(connection_id)
            
        logger.info(f"WebSocket connection closed: {connection_id}")
        
        # Stop broadcasting if no connections remain
        if not self.active_connections and self.broadcasting:
            await self.stop_broadcasting()
            
    async def subscribe(self, connection_id: str, topics: List[str]):
        """Subscribe a connection to specific topics"""
        for topic in topics:
            if topic in self.subscriptions:
                self.subscriptions[topic].add(connection_id)
                logger.debug(f"Connection {connection_id} subscribed to {topic}")
                
    async def unsubscribe(self, connection_id: str, topics: List[str]):
        """Unsubscribe a connection from specific topics"""
        for topic in topics:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(connection_id)
                logger.debug(f"Connection {connection_id} unsubscribed from {topic}")
                
    async def send_personal_message(self, message: Dict, connection_id: str):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                await self.disconnect(connection_id)
                
    async def broadcast_to_topic(self, message: Dict, topic: str):
        """Broadcast a message to all subscribers of a topic"""
        if topic not in self.subscriptions:
            return
            
        subscribers = self.subscriptions[topic].copy()
        disconnected = []
        
        for connection_id in subscribers:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected.append(connection_id)
                    
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)
            
    async def broadcast_to_all(self, message: Dict):
        """Broadcast a message to all active connections"""
        disconnected = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
                
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)
            
    async def start_broadcasting(self):
        """Start the background broadcasting task"""
        if self.broadcasting:
            return
            
        self.broadcasting = True
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("Started WebSocket broadcasting")
        
    async def stop_broadcasting(self):
        """Stop the background broadcasting task"""
        self.broadcasting = False
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped WebSocket broadcasting")
        
    async def _send_initial_data(self, websocket: WebSocket):
        """Send initial data to a newly connected client"""
        try:
            # Get current monitoring stats
            stats = await monitor.get_monitoring_stats()
            active_tasks = await monitor.get_active_tasks()
            workers = await monitor.get_worker_info()
            queues = await monitor.get_queue_info()
            
            initial_data = {
                "type": "initial_data",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "stats": stats,
                    "active_tasks": [self._serialize_task(task) for task in active_tasks],
                    "workers": [self._serialize_worker(worker) for worker in workers],
                    "queues": [self._serialize_queue(queue) for queue in queues]
                }
            }
            
            await websocket.send_text(json.dumps(initial_data))
            
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            
    async def _broadcast_loop(self):
        """Main broadcasting loop for real-time updates"""
        last_stats = {}
        last_tasks = {}
        last_workers = {}
        last_queues = {}
        
        while self.broadcasting:
            try:
                # Get current data
                current_stats = await monitor.get_monitoring_stats()
                current_tasks = {task.task_id: task for task in await monitor.get_active_tasks()}
                current_workers = {worker.hostname: worker for worker in await monitor.get_worker_info()}
                current_queues = {queue.name: queue for queue in await monitor.get_queue_info()}
                
                # Check for changes and broadcast updates
                
                # Stats updates
                if current_stats != last_stats:
                    await self.broadcast_to_topic({
                        "type": "stats_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": current_stats
                    }, "system")
                    last_stats = current_stats
                    
                # Task updates
                for task_id, task in current_tasks.items():
                    if task_id not in last_tasks or self._task_changed(last_tasks.get(task_id), task):
                        await self.broadcast_to_topic({
                            "type": "task_update",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": self._serialize_task(task)
                        }, "tasks")
                        
                # Worker updates
                for hostname, worker in current_workers.items():
                    if hostname not in last_workers or self._worker_changed(last_workers.get(hostname), worker):
                        await self.broadcast_to_topic({
                            "type": "worker_update", 
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": self._serialize_worker(worker)
                        }, "workers")
                        
                # Queue updates
                for queue_name, queue in current_queues.items():
                    if queue_name not in last_queues or self._queue_changed(last_queues.get(queue_name), queue):
                        await self.broadcast_to_topic({
                            "type": "queue_update",
                            "timestamp": datetime.utcnow().isoformat(), 
                            "data": self._serialize_queue(queue)
                        }, "queues")
                        
                # Update last known state
                last_tasks = current_tasks
                last_workers = current_workers
                last_queues = current_queues
                
                # Wait before next update
                await asyncio.sleep(1)  # 1 second update interval
                
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
                
    def _serialize_task(self, task: TaskInfo) -> Dict:
        """Serialize TaskInfo for JSON transmission"""
        data = asdict(task)
        # Convert datetime objects to ISO strings
        for field in ['received', 'started', 'succeeded', 'failed', 'retried', 'revoked', 'eta', 'expires']:
            if data[field]:
                data[field] = data[field].isoformat()
        return data
        
    def _serialize_worker(self, worker: WorkerInfo) -> Dict:
        """Serialize WorkerInfo for JSON transmission"""
        data = asdict(worker)
        if data['last_heartbeat']:
            data['last_heartbeat'] = data['last_heartbeat'].isoformat()
        return data
        
    def _serialize_queue(self, queue: QueueInfo) -> Dict:
        """Serialize QueueInfo for JSON transmission"""
        return asdict(queue)
        
    def _task_changed(self, old_task: TaskInfo, new_task: TaskInfo) -> bool:
        """Check if task has meaningful changes"""
        if not old_task:
            return True
        return (old_task.state != new_task.state or 
                old_task.runtime != new_task.runtime or
                old_task.retries != new_task.retries)
                
    def _worker_changed(self, old_worker: WorkerInfo, new_worker: WorkerInfo) -> bool:
        """Check if worker has meaningful changes"""
        if not old_worker:
            return True
        return (old_worker.status != new_worker.status or
                old_worker.active_tasks != new_worker.active_tasks or
                old_worker.processed_tasks != new_worker.processed_tasks)
                
    def _queue_changed(self, old_queue: QueueInfo, new_queue: QueueInfo) -> bool:
        """Check if queue has meaningful changes"""
        if not old_queue:
            return True
        return old_queue.length != new_queue.length
        
    async def handle_client_message(self, connection_id: str, message: Dict):
        """Handle incoming messages from clients"""
        try:
            msg_type = message.get("type")
            
            if msg_type == "subscribe":
                topics = message.get("topics", [])
                await self.subscribe(connection_id, topics)
                await self.send_personal_message({
                    "type": "subscription_confirmed",
                    "topics": topics
                }, connection_id)
                
            elif msg_type == "unsubscribe":
                topics = message.get("topics", [])
                await self.unsubscribe(connection_id, topics)
                await self.send_personal_message({
                    "type": "unsubscription_confirmed", 
                    "topics": topics
                }, connection_id)
                
            elif msg_type == "ping":
                # Update last ping time
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()
                await self.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, connection_id)
                
            elif msg_type == "cancel_task":
                task_id = message.get("task_id")
                if task_id:
                    success = await monitor.cancel_task(task_id, terminate=message.get("terminate", False))
                    await self.send_personal_message({
                        "type": "task_action_result",
                        "action": "cancel",
                        "task_id": task_id,
                        "success": success
                    }, connection_id)
                    
            elif msg_type == "retry_task":
                task_id = message.get("task_id")
                if task_id:
                    success = await monitor.retry_task(task_id)
                    await self.send_personal_message({
                        "type": "task_action_result",
                        "action": "retry",
                        "task_id": task_id,
                        "success": success
                    }, connection_id)
                    
        except Exception as e:
            logger.error(f"Error handling client message from {connection_id}: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": str(e)
            }, connection_id)

# Global connection manager
connection_manager = ConnectionManager()