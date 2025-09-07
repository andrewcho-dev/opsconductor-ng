"""
Shared application lifecycle utilities for all services
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from .logging import get_logger
from .database import cleanup_database_pool

logger = get_logger("shared.lifecycle")

def create_startup_handler(
    service_name: str,
    version: str = "1.0.0",
    custom_startup: Optional[Callable[[], Awaitable[None]]] = None
) -> Callable[[], Awaitable[None]]:
    """
    Create a standard startup event handler
    
    Args:
        service_name: Name of the service
        version: Service version
        custom_startup: Optional custom startup function
        
    Returns:
        Async startup handler function
    """
    async def startup_handler() -> None:
        """Standard startup event handler"""
        logger.info(f"Starting {service_name} v{version}")
        
        # Run custom startup logic if provided
        if custom_startup:
            try:
                await custom_startup()
                logger.info(f"Custom startup completed for {service_name}")
            except Exception as e:
                logger.error(f"Custom startup failed for {service_name}: {e}")
                raise
        
        logger.info(f"{service_name} startup completed successfully")
    
    return startup_handler

def create_shutdown_handler(
    service_name: str,
    custom_shutdown: Optional[Callable[[], Awaitable[None]]] = None
) -> Callable[[], Awaitable[None]]:
    """
    Create a standard shutdown event handler
    
    Args:
        service_name: Name of the service
        custom_shutdown: Optional custom shutdown function
        
    Returns:
        Async shutdown handler function
    """
    async def shutdown_handler() -> None:
        """Standard shutdown event handler"""
        logger.info(f"Shutting down {service_name}")
        
        # Run custom shutdown logic if provided
        if custom_shutdown:
            try:
                await custom_shutdown()
                logger.info(f"Custom shutdown completed for {service_name}")
            except Exception as e:
                logger.error(f"Custom shutdown failed for {service_name}: {e}")
        
        # Always cleanup database connections
        try:
            cleanup_database_pool()
            logger.info("Database connections cleaned up")
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
        
        logger.info(f"{service_name} shutdown completed")
    
    return shutdown_handler

def create_lifespan_handler(
    service_name: str,
    version: str = "1.0.0",
    custom_startup: Optional[Callable[[], Awaitable[None]]] = None,
    custom_shutdown: Optional[Callable[[], Awaitable[None]]] = None
):
    """
    Create a lifespan context manager for FastAPI
    
    Args:
        service_name: Name of the service
        version: Service version
        custom_startup: Optional custom startup function
        custom_shutdown: Optional custom shutdown function
        
    Returns:
        Async context manager for lifespan events
    """
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def lifespan(app):
        # Startup
        startup_handler = create_startup_handler(service_name, version, custom_startup)
        await startup_handler()
        
        yield
        
        # Shutdown
        shutdown_handler = create_shutdown_handler(service_name, custom_shutdown)
        await shutdown_handler()
    
    return lifespan

# Common worker management utilities
class WorkerManager:
    """Base class for managing background workers"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = get_logger(f"{service_name}.worker")
        self.is_running = False
        self.worker_task = None
    
    async def start_worker(self) -> Dict[str, Any]:
        """Start the background worker"""
        if self.is_running:
            return {"status": "already_running", "message": "Worker is already running"}
        
        try:
            import asyncio
            self.worker_task = asyncio.create_task(self._worker_loop())
            self.is_running = True
            self.logger.info(f"{self.service_name} worker started")
            return {"status": "started", "message": "Worker started successfully"}
        except Exception as e:
            self.logger.error(f"Failed to start {self.service_name} worker: {e}")
            return {"status": "error", "message": f"Failed to start worker: {str(e)}"}
    
    async def stop_worker(self) -> Dict[str, Any]:
        """Stop the background worker"""
        if not self.is_running:
            return {"status": "not_running", "message": "Worker is not running"}
        
        try:
            self.is_running = False
            if self.worker_task:
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
                self.worker_task = None
            
            self.logger.info(f"{self.service_name} worker stopped")
            return {"status": "stopped", "message": "Worker stopped successfully"}
        except Exception as e:
            self.logger.error(f"Failed to stop {self.service_name} worker: {e}")
            return {"status": "error", "message": f"Failed to stop worker: {str(e)}"}
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get current worker status"""
        return {
            "running": self.is_running,
            "task_active": self.worker_task is not None and not self.worker_task.done(),
            "service": self.service_name
        }
    
    async def _worker_loop(self):
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement _worker_loop method")