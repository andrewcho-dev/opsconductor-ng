"""
Service Monitor - Simple Service Mesh-like Monitoring
Provides service discovery, health monitoring, and circuit breaker functionality
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import redis.asyncio as redis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker tripped
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class ServiceInfo:
    name: str
    url: str
    status: ServiceStatus
    last_check: float
    response_time_ms: float
    error_count: int
    success_count: int
    version: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # Failures before opening circuit
    recovery_timeout: int = 30      # Seconds before trying half-open
    success_threshold: int = 3      # Successes needed to close circuit
    timeout: int = 5               # Request timeout in seconds

class CircuitBreaker:
    """Circuit breaker for service calls"""
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig):
        self.service_name = service_name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.next_attempt_time = 0
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute a function call through the circuit breaker"""
        if self.state == CircuitState.OPEN:
            if time.time() < self.next_attempt_time:
                raise Exception(f"Circuit breaker OPEN for {self.service_name}")
            else:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker CLOSED for {self.service_name}")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.next_attempt_time = time.time() + self.config.recovery_timeout
            logger.warning(f"Circuit breaker OPEN for {self.service_name}")
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.next_attempt_time = time.time() + self.config.recovery_timeout
            logger.warning(f"Circuit breaker OPEN for {self.service_name} after {self.failure_count} failures")

class ServiceMonitor:
    """Service discovery and health monitoring"""
    
    def __init__(self, redis_url: str, service_name: str):
        self.redis_url = redis_url
        self.service_name = service_name
        self.redis_client = None
        self.services: Dict[str, ServiceInfo] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.monitoring_task = None
        self.check_interval = 30  # seconds
        
    async def initialize(self):
        """Initialize the service monitor"""
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info(f"Service monitor initialized for {self.service_name}")
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def close(self):
        """Close the service monitor"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
    
    async def register_service(self, name: str, url: str, metadata: Dict[str, Any] = None):
        """Register a service for monitoring"""
        service_info = ServiceInfo(
            name=name,
            url=url,
            status=ServiceStatus.UNKNOWN,
            last_check=0,
            response_time_ms=0,
            error_count=0,
            success_count=0,
            metadata=metadata or {}
        )
        
        self.services[name] = service_info
        
        # Create circuit breaker
        self.circuit_breakers[name] = CircuitBreaker(
            name, CircuitBreakerConfig()
        )
        
        # Store in Redis for service discovery
        await self._store_service_info(service_info)
        logger.info(f"Registered service: {name} at {url}")
    
    async def get_service_url(self, service_name: str) -> Optional[str]:
        """Get URL for a service (with circuit breaker check)"""
        if service_name in self.services:
            service = self.services[service_name]
            circuit = self.circuit_breakers[service_name]
            
            if circuit.state == CircuitState.OPEN:
                logger.warning(f"Service {service_name} circuit is OPEN")
                return None
            
            return service.url
        
        # Try to discover from Redis
        service_info = await self._get_service_info(service_name)
        if service_info:
            return service_info.url
        
        return None
    
    async def call_service(self, service_name: str, endpoint: str, method: str = "GET", 
                          data: Any = None, timeout: int = 30) -> Any:
        """Make a call to another service through circuit breaker"""
        url = await self.get_service_url(service_name)
        if not url:
            raise Exception(f"Service {service_name} not available")
        
        circuit = self.circuit_breakers.get(service_name)
        if not circuit:
            raise Exception(f"No circuit breaker for {service_name}")
        
        async def make_request():
            full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                if method.upper() == "GET":
                    async with session.get(full_url) as response:
                        return await response.json()
                elif method.upper() == "POST":
                    async with session.post(full_url, json=data) as response:
                        return await response.json()
                # Add more methods as needed
        
        return await circuit.call(make_request)
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_all_services(self):
        """Check health of all registered services"""
        tasks = []
        for service_name in self.services:
            tasks.append(self._check_service_health(service_name))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service_health(self, service_name: str):
        """Check health of a specific service"""
        service = self.services[service_name]
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                health_url = f"{service.url.rstrip('/')}/health"
                async with session.get(health_url) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        service.status = ServiceStatus.HEALTHY
                        service.success_count += 1
                        service.error_count = max(0, service.error_count - 1)
                    else:
                        service.status = ServiceStatus.DEGRADED
                        service.error_count += 1
                    
                    service.response_time_ms = response_time
                    service.last_check = time.time()
                    
                    # Try to get version info
                    try:
                        health_data = await response.json()
                        service.version = health_data.get('version', 'unknown')
                    except:
                        pass
        
        except Exception as e:
            service.status = ServiceStatus.UNHEALTHY
            service.error_count += 1
            service.response_time_ms = (time.time() - start_time) * 1000
            service.last_check = time.time()
            logger.debug(f"Health check failed for {service_name}: {e}")
        
        # Update Redis
        await self._store_service_info(service)
        
        # Update circuit breaker
        circuit = self.circuit_breakers[service_name]
        if service.status == ServiceStatus.HEALTHY:
            circuit.failure_count = max(0, circuit.failure_count - 1)
        else:
            circuit.failure_count += 1
    
    async def _store_service_info(self, service: ServiceInfo):
        """Store service info in Redis"""
        try:
            key = f"service:{service.name}"
            data = asdict(service)
            data['status'] = service.status.value  # Convert enum to string
            await self.redis_client.setex(key, 300, json.dumps(data))  # 5 minute TTL
        except Exception as e:
            logger.error(f"Failed to store service info for {service.name}: {e}")
    
    async def _get_service_info(self, service_name: str) -> Optional[ServiceInfo]:
        """Get service info from Redis"""
        try:
            key = f"service:{service_name}"
            data = await self.redis_client.get(key)
            if data:
                service_data = json.loads(data)
                service_data['status'] = ServiceStatus(service_data['status'])
                return ServiceInfo(**service_data)
        except Exception as e:
            logger.error(f"Failed to get service info for {service_name}: {e}")
        return None
    
    async def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Get all known services"""
        # Return local services plus any from Redis
        all_services = self.services.copy()
        
        try:
            keys = await self.redis_client.keys("service:*")
            for key in keys:
                service_name = key.decode().split(":", 1)[1]
                if service_name not in all_services:
                    service_info = await self._get_service_info(service_name)
                    if service_info:
                        all_services[service_name] = service_info
        except Exception as e:
            logger.error(f"Failed to get services from Redis: {e}")
        
        return all_services
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        status = {}
        for name, circuit in self.circuit_breakers.items():
            status[name] = {
                "state": circuit.state.value,
                "failure_count": circuit.failure_count,
                "success_count": circuit.success_count,
                "next_attempt_time": circuit.next_attempt_time
            }
        return status