"""
Hot Reload Service
Zero-downtime tool catalog updates

This service provides:
- Event-driven cache invalidation
- Webhook notifications for tool updates
- Periodic refresh mechanism
- Manual reload triggers
- Reload history tracking
"""

import logging
import threading
import time
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReloadTrigger(str, Enum):
    """Types of reload triggers"""
    MANUAL = "manual"
    API_UPDATE = "api_update"
    PERIODIC = "periodic"
    WEBHOOK = "webhook"
    STARTUP = "startup"


class ReloadEvent:
    """Represents a reload event"""
    
    def __init__(
        self,
        trigger: ReloadTrigger,
        tool_name: Optional[str] = None,
        triggered_by: Optional[str] = None,
        reason: Optional[str] = None
    ):
        self.trigger = trigger
        self.tool_name = tool_name
        self.triggered_by = triggered_by
        self.reason = reason
        self.timestamp = datetime.now()
        self.success = False
        self.error_message: Optional[str] = None
        self.duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trigger": self.trigger.value,
            "tool_name": self.tool_name,
            "triggered_by": self.triggered_by,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms
        }


class HotReloadService:
    """
    Service for managing hot reloads of tool catalog
    
    Features:
    - Event-driven cache invalidation
    - Webhook notifications
    - Periodic refresh
    - Manual reload triggers
    - Reload history tracking
    """
    
    def __init__(
        self,
        enable_periodic_refresh: bool = False,
        refresh_interval_seconds: int = 300,  # 5 minutes
        max_history_size: int = 100
    ):
        """
        Initialize hot reload service
        
        Args:
            enable_periodic_refresh: Enable background periodic refresh
            refresh_interval_seconds: Interval for periodic refresh (default: 5 minutes)
            max_history_size: Maximum number of reload events to keep in history
        """
        self.enable_periodic_refresh = enable_periodic_refresh
        self.refresh_interval_seconds = refresh_interval_seconds
        self.max_history_size = max_history_size
        
        # Reload history
        self._reload_history: List[ReloadEvent] = []
        self._history_lock = threading.Lock()
        
        # Registered reload handlers
        self._reload_handlers: List[Callable[[ReloadEvent], None]] = []
        self._handlers_lock = threading.Lock()
        
        # Periodic refresh thread
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        
        # Statistics
        self._total_reloads = 0
        self._successful_reloads = 0
        self._failed_reloads = 0
        
        logger.info(
            f"HotReloadService initialized "
            f"(periodic_refresh={enable_periodic_refresh}, "
            f"interval={refresh_interval_seconds}s)"
        )
    
    def start(self):
        """Start the hot reload service"""
        if self.enable_periodic_refresh and self._refresh_thread is None:
            self._stop_refresh.clear()
            self._refresh_thread = threading.Thread(
                target=self._periodic_refresh_loop,
                daemon=True,
                name="HotReloadPeriodicRefresh"
            )
            self._refresh_thread.start()
            logger.info("Periodic refresh thread started")
    
    def stop(self):
        """Stop the hot reload service"""
        if self._refresh_thread is not None:
            self._stop_refresh.set()
            self._refresh_thread.join(timeout=5)
            self._refresh_thread = None
            logger.info("Periodic refresh thread stopped")
    
    def register_reload_handler(self, handler: Callable[[ReloadEvent], None]):
        """
        Register a handler to be called on reload events
        
        Args:
            handler: Function that takes a ReloadEvent and performs reload
        """
        with self._handlers_lock:
            self._reload_handlers.append(handler)
            logger.info(f"Registered reload handler: {handler.__name__}")
    
    def unregister_reload_handler(self, handler: Callable[[ReloadEvent], None]):
        """
        Unregister a reload handler
        
        Args:
            handler: Handler to unregister
        """
        with self._handlers_lock:
            if handler in self._reload_handlers:
                self._reload_handlers.remove(handler)
                logger.info(f"Unregistered reload handler: {handler.__name__}")
    
    def trigger_reload(
        self,
        trigger: ReloadTrigger,
        tool_name: Optional[str] = None,
        triggered_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> ReloadEvent:
        """
        Trigger a reload event
        
        Args:
            trigger: Type of trigger
            tool_name: Specific tool to reload (None = all tools)
            triggered_by: User/system that triggered reload
            reason: Reason for reload
            
        Returns:
            ReloadEvent with results
        """
        event = ReloadEvent(
            trigger=trigger,
            tool_name=tool_name,
            triggered_by=triggered_by,
            reason=reason
        )
        
        start_time = time.time()
        
        try:
            # Call all registered handlers
            with self._handlers_lock:
                handlers = list(self._reload_handlers)
            
            if not handlers:
                logger.warning("No reload handlers registered")
                event.success = True  # No handlers = nothing to fail
            else:
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Reload handler {handler.__name__} failed: {e}")
                        event.error_message = str(e)
                        raise
                
                event.success = True
            
            self._successful_reloads += 1
            logger.info(
                f"Reload triggered successfully: {trigger.value} "
                f"(tool={tool_name}, by={triggered_by})"
            )
            
        except Exception as e:
            event.success = False
            event.error_message = str(e)
            self._failed_reloads += 1
            logger.error(f"Reload failed: {e}")
        
        finally:
            # Record duration
            duration_ms = int((time.time() - start_time) * 1000)
            event.duration_ms = duration_ms
            
            # Add to history
            self._add_to_history(event)
            self._total_reloads += 1
        
        return event
    
    def _add_to_history(self, event: ReloadEvent):
        """Add event to history"""
        with self._history_lock:
            self._reload_history.append(event)
            
            # Trim history if too large
            if len(self._reload_history) > self.max_history_size:
                self._reload_history = self._reload_history[-self.max_history_size:]
    
    def get_reload_history(
        self,
        limit: int = 50,
        trigger: Optional[ReloadTrigger] = None
    ) -> List[Dict[str, Any]]:
        """
        Get reload history
        
        Args:
            limit: Maximum number of events to return
            trigger: Filter by trigger type
            
        Returns:
            List of reload events as dictionaries
        """
        with self._history_lock:
            history = list(self._reload_history)
        
        # Filter by trigger if specified
        if trigger is not None:
            history = [e for e in history if e.trigger == trigger]
        
        # Return most recent events
        history = history[-limit:]
        history.reverse()  # Most recent first
        
        return [event.to_dict() for event in history]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get reload statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_reloads": self._total_reloads,
            "successful_reloads": self._successful_reloads,
            "failed_reloads": self._failed_reloads,
            "success_rate": (
                self._successful_reloads / self._total_reloads
                if self._total_reloads > 0
                else 0.0
            ),
            "handlers_registered": len(self._reload_handlers),
            "periodic_refresh_enabled": self.enable_periodic_refresh,
            "refresh_interval_seconds": self.refresh_interval_seconds
        }
    
    def _periodic_refresh_loop(self):
        """Background thread for periodic refresh"""
        logger.info("Periodic refresh loop started")
        
        while not self._stop_refresh.is_set():
            # Wait for interval or stop signal
            if self._stop_refresh.wait(timeout=self.refresh_interval_seconds):
                break  # Stop signal received
            
            # Trigger periodic reload
            try:
                self.trigger_reload(
                    trigger=ReloadTrigger.PERIODIC,
                    triggered_by="system",
                    reason="Periodic refresh"
                )
            except Exception as e:
                logger.error(f"Periodic refresh failed: {e}")
        
        logger.info("Periodic refresh loop stopped")


# Global instance
_hot_reload_service: Optional[HotReloadService] = None


def get_hot_reload_service(
    enable_periodic_refresh: bool = False,
    refresh_interval_seconds: int = 300
) -> HotReloadService:
    """
    Get or create the global hot reload service instance
    
    Args:
        enable_periodic_refresh: Enable background periodic refresh
        refresh_interval_seconds: Interval for periodic refresh
        
    Returns:
        HotReloadService instance
    """
    global _hot_reload_service
    
    if _hot_reload_service is None:
        _hot_reload_service = HotReloadService(
            enable_periodic_refresh=enable_periodic_refresh,
            refresh_interval_seconds=refresh_interval_seconds
        )
        _hot_reload_service.start()
    
    return _hot_reload_service