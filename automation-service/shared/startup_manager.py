"""
Bulletproof Startup Manager
Handles service dependencies, retries, and graceful startup
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import asyncpg
import redis.asyncio as redis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class ServiceState(Enum):
    PENDING = "pending"
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"

@dataclass
class DependencyCheck:
    name: str
    check_func: Callable[[], bool]
    timeout: int = 30
    retry_interval: int = 2
    critical: bool = True
    description: str = ""

@dataclass
class ServiceDependency:
    name: str
    url: str
    endpoint: str = "/health"
    timeout: int = 30
    retry_interval: int = 2
    critical: bool = True
    expected_status: int = 200

class StartupManager:
    """Manages service startup with dependency checking and retries"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.state = ServiceState.PENDING
        self.dependencies: List[ServiceDependency] = []
        self.custom_checks: List[DependencyCheck] = []
        self.startup_time = None
        self.last_error = None
        
    def add_service_dependency(self, name: str, url: str, endpoint: str = "/health", 
                             timeout: int = 30, critical: bool = True):
        """Add a service dependency"""
        self.dependencies.append(ServiceDependency(
            name=name,
            url=url,
            endpoint=endpoint,
            timeout=timeout,
            critical=critical
        ))
        
    def add_custom_check(self, name: str, check_func: Callable, timeout: int = 30, 
                        critical: bool = True, description: str = ""):
        """Add a custom dependency check"""
        self.custom_checks.append(DependencyCheck(
            name=name,
            check_func=check_func,
            timeout=timeout,
            critical=critical,
            description=description
        ))
    
    async def wait_for_dependencies(self) -> bool:
        """Wait for all dependencies to be ready"""
        logger.info(f"[{self.service_name}] Waiting for dependencies...")
        self.state = ServiceState.STARTING
        
        # Check service dependencies
        for dep in self.dependencies:
            if not await self._wait_for_service(dep):
                if dep.critical:
                    self.state = ServiceState.FAILED
                    return False
                else:
                    logger.warning(f"[{self.service_name}] Non-critical dependency {dep.name} failed")
        
        # Check custom dependencies
        for check in self.custom_checks:
            if not await self._wait_for_custom_check(check):
                if check.critical:
                    self.state = ServiceState.FAILED
                    return False
                else:
                    logger.warning(f"[{self.service_name}] Non-critical check {check.name} failed")
        
        logger.info(f"[{self.service_name}] All dependencies ready!")
        return True
    
    async def _wait_for_service(self, dep: ServiceDependency) -> bool:
        """Wait for a specific service to be ready"""
        logger.info(f"[{self.service_name}] Checking dependency: {dep.name} at {dep.url}")
        
        start_time = time.time()
        timeout_time = start_time + dep.timeout
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            while time.time() < timeout_time:
                try:
                    url = f"{dep.url}{dep.endpoint}"
                    async with session.get(url) as response:
                        if response.status == dep.expected_status:
                            elapsed = time.time() - start_time
                            logger.info(f"[{self.service_name}] ✅ {dep.name} ready (took {elapsed:.1f}s)")
                            return True
                        else:
                            logger.debug(f"[{self.service_name}] {dep.name} returned status {response.status}")
                            
                except Exception as e:
                    logger.debug(f"[{self.service_name}] {dep.name} not ready: {e}")
                
                await asyncio.sleep(dep.retry_interval)
        
        elapsed = time.time() - start_time
        logger.error(f"[{self.service_name}] ❌ {dep.name} failed to become ready after {elapsed:.1f}s")
        self.last_error = f"Dependency {dep.name} timeout"
        return False
    
    async def _wait_for_custom_check(self, check: DependencyCheck) -> bool:
        """Wait for a custom check to pass"""
        logger.info(f"[{self.service_name}] Running custom check: {check.name}")
        
        start_time = time.time()
        timeout_time = start_time + check.timeout
        
        while time.time() < timeout_time:
            try:
                if await self._run_check_safely(check.check_func):
                    elapsed = time.time() - start_time
                    logger.info(f"[{self.service_name}] ✅ {check.name} passed (took {elapsed:.1f}s)")
                    return True
            except Exception as e:
                logger.debug(f"[{self.service_name}] {check.name} check failed: {e}")
            
            await asyncio.sleep(check.retry_interval)
        
        elapsed = time.time() - start_time
        logger.error(f"[{self.service_name}] ❌ {check.name} failed after {elapsed:.1f}s")
        self.last_error = f"Custom check {check.name} timeout"
        return False
    
    async def _run_check_safely(self, check_func: Callable) -> bool:
        """Run a check function safely, handling both sync and async"""
        try:
            if asyncio.iscoroutinefunction(check_func):
                return await check_func()
            else:
                return check_func()
        except Exception as e:
            logger.debug(f"Check function failed: {e}")
            return False
    
    def mark_ready(self):
        """Mark service as ready"""
        self.state = ServiceState.HEALTHY
        self.startup_time = time.time()
        logger.info(f"[{self.service_name}] 🚀 Service is ready!")
    
    def mark_unhealthy(self, error: str = None):
        """Mark service as unhealthy"""
        self.state = ServiceState.UNHEALTHY
        self.last_error = error
        logger.error(f"[{self.service_name}] Service marked unhealthy: {error}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current startup status"""
        return {
            "service": self.service_name,
            "state": self.state.value,
            "startup_time": self.startup_time,
            "last_error": self.last_error,
            "dependencies": [
                {
                    "name": dep.name,
                    "url": dep.url,
                    "critical": dep.critical
                }
                for dep in self.dependencies
            ]
        }

# Convenience functions for common dependency checks
async def check_postgres(host: str, port: int, database: str, user: str, password: str) -> bool:
    """Check if PostgreSQL is ready"""
    try:
        conn = await asyncpg.connect(
            host=host, port=port, database=database, 
            user=user, password=password, timeout=5
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True
    except Exception:
        return False

async def check_redis(url: str) -> bool:
    """Check if Redis is ready"""
    try:
        r = redis.from_url(url, socket_timeout=5)
        await r.ping()
        await r.close()
        return True
    except Exception:
        return False

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    import os
    return os.path.exists(filepath)

def check_env_var(var_name: str) -> bool:
    """Check if environment variable is set"""
    import os
    return os.getenv(var_name) is not None