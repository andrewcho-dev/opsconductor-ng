"""
Base Service Foundation
Provides common functionality for all OpsConductor services
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
import structlog

# Import our new startup and monitoring components
from startup_manager import StartupManager, check_postgres, check_redis
from service_monitor import ServiceMonitor

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# ============================================================================
# MODELS
# ============================================================================

class HealthCheck(BaseModel):
    name: str
    status: str  # "healthy", "unhealthy", "degraded"
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None

class HealthResponse(BaseModel):
    service: str
    status: str
    version: str
    timestamp: str
    checks: List[HealthCheck]
    uptime_seconds: Optional[float] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: Optional[str] = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: str

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Global metrics registry to prevent duplicates
_GLOBAL_METRICS = {}

class ServiceMetrics:
    """Prometheus metrics for OpsConductor services"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.enabled = PROMETHEUS_AVAILABLE
        
        if not self.enabled:
            logger.warning("Prometheus client not available, metrics disabled")
            return
        
        # Use global metrics to prevent duplicates
        global _GLOBAL_METRICS
        
        # HTTP metrics
        if 'http_requests_total' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['http_requests_total'] = Counter(
                'opsconductor_http_requests_total',
                'Total HTTP requests',
                ['service', 'method', 'endpoint', 'status_code']
            )
        self.http_requests_total = _GLOBAL_METRICS['http_requests_total']
        
        if 'http_request_duration' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['http_request_duration'] = Histogram(
                'opsconductor_http_request_duration_seconds',
                'HTTP request duration in seconds',
                ['service', 'method', 'endpoint'],
                buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            )
        self.http_request_duration = _GLOBAL_METRICS['http_request_duration']
        
        # Service health metrics
        if 'service_health' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['service_health'] = Gauge(
                'opsconductor_service_health',
                'Service health status (1=healthy, 0=unhealthy)',
                ['service', 'component']
            )
        self.service_health = _GLOBAL_METRICS['service_health']
        
        if 'service_uptime' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['service_uptime'] = Gauge(
                'opsconductor_service_uptime_seconds',
                'Service uptime in seconds',
                ['service']
            )
        self.service_uptime = _GLOBAL_METRICS['service_uptime']
        
        # Database metrics
        if 'db_connections_active' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['db_connections_active'] = Gauge(
                'opsconductor_db_connections_active',
                'Active database connections',
                ['service']
            )
        self.db_connections_active = _GLOBAL_METRICS['db_connections_active']
        
        if 'db_query_duration' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['db_query_duration'] = Histogram(
                'opsconductor_db_query_duration_seconds',
                'Database query duration in seconds',
                ['service', 'operation'],
                buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
            )
        self.db_query_duration = _GLOBAL_METRICS['db_query_duration']
        
        # Redis metrics
        if 'redis_operations_total' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['redis_operations_total'] = Counter(
                'opsconductor_redis_operations_total',
                'Total Redis operations',
                ['service', 'operation', 'status']
            )
        self.redis_operations_total = _GLOBAL_METRICS['redis_operations_total']
        
        if 'redis_operation_duration' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['redis_operation_duration'] = Histogram(
                'opsconductor_redis_operation_duration_seconds',
                'Redis operation duration in seconds',
                ['service', 'operation'],
                buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
            )
        self.redis_operation_duration = _GLOBAL_METRICS['redis_operation_duration']
        
        # Service info
        if 'service_info' not in _GLOBAL_METRICS:
            _GLOBAL_METRICS['service_info'] = Info(
                'opsconductor_service_info',
                'Service information',
                ['service']
            )
        self.service_info = _GLOBAL_METRICS['service_info']
        
        # Set service info
        self.service_info.labels(service=service_name).info({
            'version': os.getenv('SERVICE_VERSION', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'build_date': os.getenv('BUILD_DATE', 'unknown')
        })
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if not self.enabled:
            return
        
        self.http_requests_total.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        self.http_request_duration.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def update_service_health(self, component: str, healthy: bool):
        """Update service health metrics"""
        if not self.enabled:
            return
        
        self.service_health.labels(
            service=self.service_name,
            component=component
        ).set(1 if healthy else 0)
    
    def update_uptime(self, uptime_seconds: float):
        """Update service uptime"""
        if not self.enabled:
            return
        
        self.service_uptime.labels(service=self.service_name).set(uptime_seconds)
    
    def record_db_query(self, operation: str, duration: float):
        """Record database query metrics"""
        if not self.enabled:
            return
        
        self.db_query_duration.labels(
            service=self.service_name,
            operation=operation
        ).observe(duration)
    
    def record_redis_operation(self, operation: str, duration: float, success: bool):
        """Record Redis operation metrics"""
        if not self.enabled:
            return
        
        status = "success" if success else "error"
        self.redis_operations_total.labels(
            service=self.service_name,
            operation=operation,
            status=status
        ).inc()
        
        self.redis_operation_duration.labels(
            service=self.service_name,
            operation=operation
        ).observe(duration)

# ============================================================================
# DATABASE CONNECTION POOL
# ============================================================================

class DatabasePool:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self, database_url: str, schema: str = "public"):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'search_path': schema,
                    'application_name': 'opsconductor'
                }
            )
            logger.info("Database pool initialized", schema=schema)
        except Exception as e:
            logger.error("Failed to initialize database pool", error=str(e))
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    async def health_check(self) -> HealthCheck:
        """Check database health"""
        start_time = asyncio.get_event_loop().time()
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return HealthCheck(
                name="database",
                status="healthy",
                response_time_ms=response_time
            )
        except Exception as e:
            return HealthCheck(
                name="database",
                status="unhealthy",
                details={"error": str(e)}
            )

# ============================================================================
# REDIS CONNECTION
# ============================================================================

class RedisClient:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        
    async def initialize(self, redis_url: str):
        """Initialize Redis connection"""
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            await self.client.ping()
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error("Failed to initialize Redis client", error=str(e))
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis client closed")
    
    async def health_check(self) -> HealthCheck:
        """Check Redis health"""
        start_time = asyncio.get_event_loop().time()
        try:
            await self.client.ping()
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return HealthCheck(
                name="redis",
                status="healthy",
                response_time_ms=response_time
            )
        except Exception as e:
            return HealthCheck(
                name="redis",
                status="unhealthy",
                details={"error": str(e)}
            )

# ============================================================================
# BASE SERVICE CLASS
# ============================================================================

class BaseService:
    def __init__(self, name: str, version: str = "1.0.0", port: int = 3000):
        self.name = name
        self.version = version
        self.port = port
        self.start_time = datetime.now(timezone.utc)
        
        # Initialize components
        self.db = DatabasePool()
        self.redis = RedisClient()
        self.metrics = ServiceMetrics(name)
        
        # Initialize startup manager and service monitor
        self.startup_manager = StartupManager(name)
        self.service_monitor = None
        
        # Create FastAPI app with lifespan
        self.app = FastAPI(
            title=f"OpsConductor {name.title()} Service",
            version=version,
            description=f"OpsConductor {name} service API",
            lifespan=self.lifespan
        )
        
        # Add middleware
        self._setup_middleware()
        
        # Add common routes
        self._setup_common_routes()
        
        # Setup logging
        self.logger = structlog.get_logger(service=name)
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Service lifespan management"""
        # Startup
        await self._startup()
        self.logger.info("Service started", port=self.port)
        
        yield
        
        # Shutdown
        await self._shutdown()
        self.logger.info("Service stopped")
    
    async def _startup(self):
        """Service startup logic with bulletproof dependency checking"""
        self.logger.info("Starting service with bulletproof startup...")
        
        # Setup dependencies
        await self._setup_dependencies()
        
        # Wait for dependencies
        if not await self.startup_manager.wait_for_dependencies():
            raise Exception(f"Failed to start {self.name}: dependencies not ready")
        
        # Initialize database
        database_url = self._get_database_url()
        schema = os.getenv("DB_SCHEMA", "public")
        await self.db.initialize(database_url, schema)
        
        # Initialize Redis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        await self.redis.initialize(redis_url)
        
        # Initialize service monitor
        self.service_monitor = ServiceMonitor(redis_url, self.name)
        await self.service_monitor.initialize()
        
        # Register this service - use container name for internal communication
        service_url = f"http://{self.name}:{self.port}"
        await self.service_monitor.register_service(
            self.name, 
            service_url,
            {"version": self.version, "started_at": self.start_time.isoformat()}
        )
        
        # Service-specific startup
        await self.on_startup()
        
        # Mark as ready
        self.startup_manager.mark_ready()
    
    async def _shutdown(self):
        """Service shutdown logic"""
        # Service-specific shutdown
        await self.on_shutdown()
        
        # Close service monitor
        if self.service_monitor:
            await self.service_monitor.close()
        
        # Close connections
        await self.db.close()
        await self.redis.close()
    
    async def _setup_dependencies(self):
        """Setup common dependencies - override in subclasses for service-specific deps"""
        # Database dependency - use Docker service name
        db_host = os.getenv("DB_HOST", "postgres")
        db_port = int(os.getenv("DB_PORT", "5432"))
        db_name = os.getenv("DB_NAME", "opsconductor")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres123")
        
        async def postgres_check():
            return await check_postgres(db_host, db_port, db_name, db_user, db_password)
        
        self.startup_manager.add_custom_check(
            "postgres",
            postgres_check,
            timeout=60,
            critical=True,
            description="PostgreSQL database connection"
        )
        
        # Redis dependency - use Docker service name
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        async def redis_check():
            return await check_redis(redis_url)
        
        self.startup_manager.add_custom_check(
            "redis",
            redis_check,
            timeout=30,
            critical=True,
            description="Redis connection"
        )
        
        # Call service-specific dependency setup
        await self.setup_service_dependencies()
    
    async def setup_service_dependencies(self):
        """Override in subclasses to add service-specific dependencies"""
        pass
    
    async def on_startup(self):
        """Override in subclasses for service-specific startup logic"""
        pass
    
    async def on_shutdown(self):
        """Override in subclasses for service-specific shutdown logic"""
        pass
    
    def _get_database_url(self) -> str:
        """Build database URL from environment variables"""
        host = os.getenv("DB_HOST", "postgres")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "opsconductor")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres123")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    def _setup_middleware(self):
        """Setup common middleware"""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Trusted hosts
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )
        
        # Request logging and metrics middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = asyncio.get_event_loop().time()
            
            # Add request ID
            request_id = request.headers.get("X-Request-ID", f"req_{int(start_time * 1000)}")
            
            # Extract endpoint for metrics (remove query params and normalize)
            endpoint = request.url.path
            if endpoint.startswith("/"):
                endpoint = endpoint[1:] if len(endpoint) > 1 else "root"
            
            # Log request
            self.logger.info(
                "Request started",
                method=request.method,
                url=str(request.url),
                request_id=request_id
            )
            
            # Process request
            try:
                response = await call_next(request)
                duration_seconds = asyncio.get_event_loop().time() - start_time
                duration_ms = duration_seconds * 1000
                
                # Record metrics
                self.metrics.record_http_request(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    duration=duration_seconds
                )
                
                # Log response
                self.logger.info(
                    "Request completed",
                    method=request.method,
                    url=str(request.url),
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    request_id=request_id
                )
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                return response
                
            except Exception as e:
                duration_seconds = asyncio.get_event_loop().time() - start_time
                duration_ms = duration_seconds * 1000
                
                # Record error metrics (assume 500 status)
                self.metrics.record_http_request(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=500,
                    duration=duration_seconds
                )
                
                self.logger.error(
                    "Request failed",
                    method=request.method,
                    url=str(request.url),
                    error=str(e),
                    duration_ms=duration_ms,
                    request_id=request_id
                )
                raise
    
    def _setup_common_routes(self):
        """Setup common routes for all services"""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            checks = []
            
            # Database health
            db_check = await self.db.health_check()
            checks.append(db_check)
            self.metrics.update_service_health("database", db_check.status == "healthy")
            
            # Redis health
            redis_check = await self.redis.health_check()
            checks.append(redis_check)
            self.metrics.update_service_health("redis", redis_check.status == "healthy")
            
            # Service-specific health checks
            service_checks = await self.get_health_checks()
            checks.extend(service_checks)
            
            # Update service-specific health metrics
            for check in service_checks:
                self.metrics.update_service_health(check.name, check.status == "healthy")
            
            # Overall status
            overall_status = "healthy"
            if any(check.status == "unhealthy" for check in checks):
                overall_status = "unhealthy"
            elif any(check.status == "degraded" for check in checks):
                overall_status = "degraded"
            
            # Calculate uptime
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            self.metrics.update_uptime(uptime)
            self.metrics.update_service_health("overall", overall_status == "healthy")
            
            return HealthResponse(
                service=self.name,
                status=overall_status,
                version=self.version,
                timestamp=datetime.now(timezone.utc).isoformat(),
                checks=checks,
                uptime_seconds=uptime
            )
        
        @self.app.get("/info")
        async def service_info():
            """Service information endpoint"""
            return {
                "service": self.name,
                "version": self.version,
                "started_at": self.start_time.isoformat(),
                "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds()
            }
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            if not PROMETHEUS_AVAILABLE:
                return JSONResponse(
                    status_code=503,
                    content={"error": "Metrics not available", "message": "Prometheus client not installed"}
                )
            
            # Generate metrics
            metrics_data = generate_latest()
            return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
        
        @self.app.get("/ready")
        async def readiness_check():
            """Kubernetes-style readiness probe"""
            if self.startup_manager.state.value in ["healthy", "starting"]:
                return {"status": "ready", "service": self.name}
            else:
                raise HTTPException(
                    status_code=503,
                    detail={"status": "not ready", "service": self.name, "error": self.startup_manager.last_error}
                )
        
        @self.app.get("/live")
        async def liveness_check():
            """Kubernetes-style liveness probe"""
            return {"status": "alive", "service": self.name, "uptime": (datetime.now(timezone.utc) - self.start_time).total_seconds()}
        
        @self.app.get("/startup-status")
        async def startup_status():
            """Detailed startup status"""
            return self.startup_manager.get_status()
        
        @self.app.get("/services")
        async def service_discovery():
            """Service discovery endpoint"""
            if self.service_monitor:
                services = await self.service_monitor.get_all_services()
                return {
                    "services": {
                        name: {
                            "url": service.url,
                            "status": service.status.value,
                            "last_check": service.last_check,
                            "response_time_ms": service.response_time_ms,
                            "version": service.version
                        }
                        for name, service in services.items()
                    }
                }
            return {"services": {}}
        
        @self.app.get("/circuit-breakers")
        async def circuit_breaker_status():
            """Circuit breaker status"""
            if self.service_monitor:
                return self.service_monitor.get_circuit_breaker_status()
            return {}
        
        # Global exception handler
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            """Global exception handler"""
            request_id = request.headers.get("X-Request-ID", "unknown")
            
            self.logger.error(
                "Unhandled exception",
                error=str(exc),
                request_id=request_id,
                url=str(request.url),
                method=request.method
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    error="internal_server_error",
                    message="An internal server error occurred",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    request_id=request_id
                ).dict()
            )
    
    async def get_health_checks(self) -> List[HealthCheck]:
        """Override in subclasses for service-specific health checks"""
        return []
    
    def create_success_response(self, message: str, data: Any = None) -> SuccessResponse:
        """Create a standardized success response"""
        return SuccessResponse(
            message=message,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def run(self):
        """Run the service"""
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_error_response(error: str, message: str, details: Dict[str, Any] = None) -> ErrorResponse:
    """Create a standardized error response"""
    return ErrorResponse(
        error=error,
        message=message,
        details=details,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

async def get_database_connection(pool: asyncpg.Pool):
    """Get database connection from pool"""
    async with pool.acquire() as conn:
        yield conn