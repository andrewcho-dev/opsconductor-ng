#!/usr/bin/env python3
"""
Advanced Health Monitoring System
Provides comprehensive health checks, metrics collection, and alerting
"""

import asyncio
import aiohttp
import asyncpg
import aioredis
import time
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class ServiceType(Enum):
    DATABASE = "database"
    CACHE = "cache"
    HTTP_SERVICE = "http_service"
    MESSAGE_QUEUE = "message_queue"
    EXTERNAL_API = "external_api"

@dataclass
class HealthMetrics:
    """Health metrics for a service"""
    response_time: float
    status_code: Optional[int] = None
    error_rate: float = 0.0
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    connections: Optional[int] = None
    custom_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    service_name: str
    status: HealthStatus
    metrics: HealthMetrics
    timestamp: datetime
    error_message: Optional[str] = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

class HealthChecker:
    """Base class for health checkers"""
    
    def __init__(self, name: str, service_type: ServiceType, timeout: float = 10.0):
        self.name = name
        self.service_type = service_type
        self.timeout = timeout
        self.history: List[HealthCheckResult] = []
        self.max_history = 100

    async def check(self) -> HealthCheckResult:
        """Perform health check - override in subclasses"""
        raise NotImplementedError

    def add_to_history(self, result: HealthCheckResult):
        """Add result to history"""
        self.history.append(result)
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_error_rate(self, window_minutes: int = 5) -> float:
        """Calculate error rate over time window"""
        if not self.history:
            return 0.0
        
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_checks = [h for h in self.history if h.timestamp > cutoff]
        
        if not recent_checks:
            return 0.0
        
        errors = sum(1 for h in recent_checks if h.status != HealthStatus.HEALTHY)
        return errors / len(recent_checks)

    def get_avg_response_time(self, window_minutes: int = 5) -> float:
        """Calculate average response time over time window"""
        if not self.history:
            return 0.0
        
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_checks = [h for h in self.history if h.timestamp > cutoff]
        
        if not recent_checks:
            return 0.0
        
        total_time = sum(h.metrics.response_time for h in recent_checks)
        return total_time / len(recent_checks)

class HttpHealthChecker(HealthChecker):
    """Health checker for HTTP services"""
    
    def __init__(self, name: str, url: str, expected_status: int = 200, **kwargs):
        super().__init__(name, ServiceType.HTTP_SERVICE, **kwargs)
        self.url = url
        self.expected_status = expected_status

    async def check(self) -> HealthCheckResult:
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(self.url) as response:
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    
                    status = HealthStatus.HEALTHY if response.status == self.expected_status else HealthStatus.UNHEALTHY
                    
                    # Try to get response body for additional info
                    try:
                        body = await response.text()
                        details = {"response_body": body[:500]}  # Limit body size
                    except:
                        details = {}
                    
                    metrics = HealthMetrics(
                        response_time=response_time,
                        status_code=response.status
                    )
                    
                    result = HealthCheckResult(
                        service_name=self.name,
                        status=status,
                        metrics=metrics,
                        timestamp=datetime.now(),
                        details=details
                    )
                    
        except asyncio.TimeoutError:
            response_time = self.timeout * 1000
            result = HealthCheckResult(
                service_name=self.name,
                status=HealthStatus.UNHEALTHY,
                metrics=HealthMetrics(response_time=response_time),
                timestamp=datetime.now(),
                error_message="Request timeout"
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service_name=self.name,
                status=HealthStatus.UNHEALTHY,
                metrics=HealthMetrics(response_time=response_time),
                timestamp=datetime.now(),
                error_message=str(e)
            )
        
        self.add_to_history(result)
        return result

class PostgresHealthChecker(HealthChecker):
    """Health checker for PostgreSQL"""
    
    def __init__(self, name: str, host: str, port: int, database: str, user: str, password: str, **kwargs):
        super().__init__(name, ServiceType.DATABASE, **kwargs)
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    async def check(self) -> HealthCheckResult:
        start_time = time.time()
        
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                timeout=self.timeout
            )
            
            # Test query
            await conn.fetchval("SELECT 1")
            
            # Get connection stats
            stats = await conn.fetch("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections
                FROM pg_stat_activity
            """)
            
            await conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            metrics = HealthMetrics(
                response_time=response_time,
                connections=stats[0]['total_connections'] if stats else None,
                custom_metrics={
                    'active_connections': stats[0]['active_connections'] if stats else None
                }
            )
            
            result = HealthCheckResult(
                service_name=self.name,
                status=HealthStatus.HEALTHY,
                metrics=metrics,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service_name=self.name,
                status=HealthStatus.UNHEALTHY,
                metrics=HealthMetrics(response_time=response_time),
                timestamp=datetime.now(),
                error_message=str(e)
            )
        
        self.add_to_history(result)
        return result

class RedisHealthChecker(HealthChecker):
    """Health checker for Redis"""
    
    def __init__(self, name: str, url: str, **kwargs):
        super().__init__(name, ServiceType.CACHE, **kwargs)
        self.url = url

    async def check(self) -> HealthCheckResult:
        start_time = time.time()
        
        try:
            redis = aioredis.from_url(self.url, socket_timeout=self.timeout)
            
            # Test ping
            await redis.ping()
            
            # Get info
            info = await redis.info()
            
            await redis.close()
            
            response_time = (time.time() - start_time) * 1000
            
            metrics = HealthMetrics(
                response_time=response_time,
                memory_usage=info.get('used_memory_human'),
                connections=info.get('connected_clients'),
                custom_metrics={
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'uptime_seconds': info.get('uptime_in_seconds', 0)
                }
            )
            
            result = HealthCheckResult(
                service_name=self.name,
                status=HealthStatus.HEALTHY,
                metrics=metrics,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service_name=self.name,
                status=HealthStatus.UNHEALTHY,
                metrics=HealthMetrics(response_time=response_time),
                timestamp=datetime.now(),
                error_message=str(e)
            )
        
        self.add_to_history(result)
        return result

class HealthMonitor:
    """Main health monitoring system"""
    
    def __init__(self):
        self.checkers: Dict[str, HealthChecker] = {}
        self.running = False
        self.check_interval = 30  # seconds
        self.alert_callbacks: List[Callable] = []

    def add_checker(self, checker: HealthChecker):
        """Add a health checker"""
        self.checkers[checker.name] = checker
        logger.info(f"Added health checker for {checker.name}")

    def add_http_service(self, name: str, url: str, expected_status: int = 200, timeout: float = 10.0):
        """Add HTTP service health check"""
        checker = HttpHealthChecker(name, url, expected_status, timeout=timeout)
        self.add_checker(checker)

    def add_postgres(self, name: str, host: str, port: int, database: str, user: str, password: str, timeout: float = 10.0):
        """Add PostgreSQL health check"""
        checker = PostgresHealthChecker(name, host, port, database, user, password, timeout=timeout)
        self.add_checker(checker)

    def add_redis(self, name: str, url: str, timeout: float = 10.0):
        """Add Redis health check"""
        checker = RedisHealthChecker(name, url, timeout=timeout)
        self.add_checker(checker)

    def add_alert_callback(self, callback: Callable[[HealthCheckResult], None]):
        """Add callback for health alerts"""
        self.alert_callbacks.append(callback)

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Check all services"""
        results = {}
        
        tasks = []
        for name, checker in self.checkers.items():
            tasks.append(checker.check())
        
        if tasks:
            check_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(check_results):
                checker_name = list(self.checkers.keys())[i]
                
                if isinstance(result, Exception):
                    # Handle checker exceptions
                    results[checker_name] = HealthCheckResult(
                        service_name=checker_name,
                        status=HealthStatus.UNKNOWN,
                        metrics=HealthMetrics(response_time=0),
                        timestamp=datetime.now(),
                        error_message=f"Checker error: {str(result)}"
                    )
                else:
                    results[checker_name] = result
                    
                    # Trigger alerts for unhealthy services
                    if result.status != HealthStatus.HEALTHY:
                        for callback in self.alert_callbacks:
                            try:
                                callback(result)
                            except Exception as e:
                                logger.error(f"Alert callback error: {e}")
        
        return results

    async def start_monitoring(self):
        """Start continuous monitoring"""
        self.running = True
        logger.info("Starting health monitoring")
        
        while self.running:
            try:
                await self.check_all()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)  # Short delay before retry

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Stopping health monitoring")

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        if not self.checkers:
            return {
                "status": "unknown",
                "total_services": 0,
                "healthy_services": 0,
                "unhealthy_services": 0,
                "degraded_services": 0,
                "avg_response_time": 0
            }
        
        latest_results = {}
        for name, checker in self.checkers.items():
            if checker.history:
                latest_results[name] = checker.history[-1]
        
        if not latest_results:
            return {
                "status": "unknown",
                "total_services": len(self.checkers),
                "healthy_services": 0,
                "unhealthy_services": 0,
                "degraded_services": 0,
                "avg_response_time": 0
            }
        
        healthy = sum(1 for r in latest_results.values() if r.status == HealthStatus.HEALTHY)
        unhealthy = sum(1 for r in latest_results.values() if r.status == HealthStatus.UNHEALTHY)
        degraded = sum(1 for r in latest_results.values() if r.status == HealthStatus.DEGRADED)
        
        avg_response_time = sum(r.metrics.response_time for r in latest_results.values()) / len(latest_results)
        
        # Determine overall system status
        if unhealthy > 0:
            overall_status = "unhealthy"
        elif degraded > 0:
            overall_status = "degraded"
        elif healthy == len(latest_results):
            overall_status = "healthy"
        else:
            overall_status = "unknown"
        
        return {
            "status": overall_status,
            "total_services": len(self.checkers),
            "healthy_services": healthy,
            "unhealthy_services": unhealthy,
            "degraded_services": degraded,
            "avg_response_time": round(avg_response_time, 2),
            "last_check": max(r.timestamp for r in latest_results.values()).isoformat()
        }

    def get_service_details(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific service"""
        if service_name not in self.checkers:
            return None
        
        checker = self.checkers[service_name]
        
        if not checker.history:
            return {
                "name": service_name,
                "type": checker.service_type.value,
                "status": "unknown",
                "history": []
            }
        
        latest = checker.history[-1]
        
        return {
            "name": service_name,
            "type": checker.service_type.value,
            "status": latest.status.value,
            "latest_check": latest.to_dict(),
            "error_rate_5min": checker.get_error_rate(5),
            "avg_response_time_5min": checker.get_avg_response_time(5),
            "history": [h.to_dict() for h in checker.history[-10:]]  # Last 10 checks
        }

# Example alert callback
def log_alert(result: HealthCheckResult):
    """Simple logging alert callback"""
    logger.warning(f"HEALTH ALERT: {result.service_name} is {result.status.value} - {result.error_message}")

# Example usage
async def setup_monitoring():
    """Setup example monitoring configuration"""
    monitor = HealthMonitor()
    
    # Get host IP from environment for external access
    host_ip = os.getenv('HOST_IP', '127.0.0.1')
    
    # Add services - use host IP for external access
    monitor.add_http_service("identity-service", f"http://{host_ip}:3001/health")
    monitor.add_http_service("kong-gateway", f"http://{host_ip}:8000")
    monitor.add_http_service("keycloak", f"http://{host_ip}:8080/health/ready")
    
    # For database connections, use host IP for external access
    monitor.add_postgres("postgres", host_ip, 5432, "opsconductor", "postgres", "postgres123")
    monitor.add_redis("redis", f"redis://{host_ip}:6379/0")
    
    # Add alert callback
    monitor.add_alert_callback(log_alert)
    
    return monitor