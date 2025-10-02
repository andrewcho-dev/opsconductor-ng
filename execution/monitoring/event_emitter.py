"""
Event Emitter - Real-time execution event emission
Emits execution events for SSE/WebSocket/long-polling consumption
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# MODELS
# ============================================================================

class EventType(str, Enum):
    """Event types for execution events"""
    # Execution events
    EXECUTION_CREATED = "execution.created"
    EXECUTION_QUEUED = "execution.queued"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_CANCELLED = "execution.cancelled"
    EXECUTION_TIMEOUT = "execution.timeout"
    
    # Step events
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"
    STEP_FAILED = "step.failed"
    STEP_PROGRESS = "step.progress"
    
    # Approval events
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    
    # System events
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ALERT = "system.alert"


class ExecutionEvent(BaseModel):
    """Execution event for real-time updates"""
    event_id: str = Field(default_factory=lambda: str(UUID))
    event_type: EventType
    execution_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Event data
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Optional fields
    step_id: Optional[UUID] = None
    user_id: Optional[int] = None
    message: Optional[str] = None
    
    # Metadata
    trace_id: Optional[UUID] = None


# ============================================================================
# EVENT EMITTER
# ============================================================================

class EventEmitter:
    """
    Emits real-time execution events
    
    Features:
    - Event subscription by execution ID
    - Event subscription by event type
    - Broadcast to all subscribers
    - Event history buffer
    - SSE/WebSocket ready
    - Async event handlers
    """
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self._event_buffer: List[ExecutionEvent] = []
        self._subscribers: Dict[UUID, Set[Callable]] = {}  # execution_id -> callbacks
        self._type_subscribers: Dict[EventType, Set[Callable]] = {}  # event_type -> callbacks
        self._global_subscribers: Set[Callable] = set()  # All events
        self._lock = asyncio.Lock()
        logger.info("EventEmitter initialized")
    
    async def emit(self, event: ExecutionEvent):
        """
        Emit an event to all subscribers
        
        Args:
            event: ExecutionEvent to emit
        """
        try:
            # Add to buffer
            async with self._lock:
                self._event_buffer.append(event)
                if len(self._event_buffer) > self.buffer_size:
                    self._event_buffer.pop(0)
            
            # Notify subscribers
            await self._notify_subscribers(event)
            
            logger.debug(f"Emitted event: {event.event_type} for execution {event.execution_id}")
            
        except Exception as e:
            logger.error(f"Error emitting event: {e}", exc_info=True)
    
    async def emit_execution_created(self, execution_id: UUID, user_id: Optional[int] = None, **data):
        """Emit execution created event"""
        event = ExecutionEvent(
            event_type=EventType.EXECUTION_CREATED,
            execution_id=execution_id,
            user_id=user_id,
            data=data,
        )
        await self.emit(event)
    
    async def emit_execution_started(self, execution_id: UUID, **data):
        """Emit execution started event"""
        event = ExecutionEvent(
            event_type=EventType.EXECUTION_STARTED,
            execution_id=execution_id,
            data=data,
        )
        await self.emit(event)
    
    async def emit_execution_completed(self, execution_id: UUID, duration_ms: int, **data):
        """Emit execution completed event"""
        event = ExecutionEvent(
            event_type=EventType.EXECUTION_COMPLETED,
            execution_id=execution_id,
            data={"duration_ms": duration_ms, **data},
        )
        await self.emit(event)
    
    async def emit_execution_failed(self, execution_id: UUID, error: str, **data):
        """Emit execution failed event"""
        event = ExecutionEvent(
            event_type=EventType.EXECUTION_FAILED,
            execution_id=execution_id,
            message=error,
            data=data,
        )
        await self.emit(event)
    
    async def emit_step_started(self, execution_id: UUID, step_id: UUID, step_name: str, **data):
        """Emit step started event"""
        event = ExecutionEvent(
            event_type=EventType.STEP_STARTED,
            execution_id=execution_id,
            step_id=step_id,
            data={"step_name": step_name, **data},
        )
        await self.emit(event)
    
    async def emit_step_completed(self, execution_id: UUID, step_id: UUID, duration_ms: int, **data):
        """Emit step completed event"""
        event = ExecutionEvent(
            event_type=EventType.STEP_COMPLETED,
            execution_id=execution_id,
            step_id=step_id,
            data={"duration_ms": duration_ms, **data},
        )
        await self.emit(event)
    
    async def emit_step_failed(self, execution_id: UUID, step_id: UUID, error: str, **data):
        """Emit step failed event"""
        event = ExecutionEvent(
            event_type=EventType.STEP_FAILED,
            execution_id=execution_id,
            step_id=step_id,
            message=error,
            data=data,
        )
        await self.emit(event)
    
    async def emit_step_progress(self, execution_id: UUID, step_id: UUID, progress_percent: int, **data):
        """Emit step progress event"""
        event = ExecutionEvent(
            event_type=EventType.STEP_PROGRESS,
            execution_id=execution_id,
            step_id=step_id,
            data={"progress_percent": progress_percent, **data},
        )
        await self.emit(event)
    
    async def subscribe(
        self,
        callback: Callable[[ExecutionEvent], None],
        execution_id: Optional[UUID] = None,
        event_type: Optional[EventType] = None,
    ):
        """
        Subscribe to events
        
        Args:
            callback: Async callback function to call on event
            execution_id: Optional execution ID to filter by
            event_type: Optional event type to filter by
        """
        async with self._lock:
            if execution_id:
                if execution_id not in self._subscribers:
                    self._subscribers[execution_id] = set()
                self._subscribers[execution_id].add(callback)
                logger.debug(f"Subscribed to execution {execution_id}")
            elif event_type:
                if event_type not in self._type_subscribers:
                    self._type_subscribers[event_type] = set()
                self._type_subscribers[event_type].add(callback)
                logger.debug(f"Subscribed to event type {event_type}")
            else:
                self._global_subscribers.add(callback)
                logger.debug("Subscribed to all events")
    
    async def unsubscribe(
        self,
        callback: Callable[[ExecutionEvent], None],
        execution_id: Optional[UUID] = None,
        event_type: Optional[EventType] = None,
    ):
        """
        Unsubscribe from events
        
        Args:
            callback: Callback to remove
            execution_id: Optional execution ID
            event_type: Optional event type
        """
        async with self._lock:
            if execution_id and execution_id in self._subscribers:
                self._subscribers[execution_id].discard(callback)
                if not self._subscribers[execution_id]:
                    del self._subscribers[execution_id]
            elif event_type and event_type in self._type_subscribers:
                self._type_subscribers[event_type].discard(callback)
                if not self._type_subscribers[event_type]:
                    del self._type_subscribers[event_type]
            else:
                self._global_subscribers.discard(callback)
    
    async def get_events(
        self,
        execution_id: Optional[UUID] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[ExecutionEvent]:
        """
        Get events from buffer
        
        Args:
            execution_id: Optional execution ID filter
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        async with self._lock:
            events = self._event_buffer.copy()
        
        # Filter by execution_id
        if execution_id:
            events = [e for e in events if e.execution_id == execution_id]
        
        # Filter by event_type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Limit
        if len(events) > limit:
            events = events[-limit:]
        
        return events
    
    async def clear_buffer(self):
        """Clear event buffer"""
        async with self._lock:
            self._event_buffer.clear()
    
    async def _notify_subscribers(self, event: ExecutionEvent):
        """Notify all relevant subscribers"""
        callbacks = set()
        
        async with self._lock:
            # Execution-specific subscribers
            if event.execution_id in self._subscribers:
                callbacks.update(self._subscribers[event.execution_id])
            
            # Event type subscribers
            if event.event_type in self._type_subscribers:
                callbacks.update(self._type_subscribers[event.event_type])
            
            # Global subscribers
            callbacks.update(self._global_subscribers)
        
        # Call all callbacks
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}", exc_info=True)