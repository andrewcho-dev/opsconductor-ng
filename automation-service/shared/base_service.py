"""
Base Service Foundation
Provides common functionality for all OpsConductor services
"""

import os
import sys
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
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

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
    def __init__(self, name: str, version: str = "1.0.0", port: int = 3000, lifespan=None):
        self.name = name
        self.version = version
        self.port = port
        self.start_time = datetime.now(timezone.utc)
        
        # Initialize components
        self.db = DatabasePool()
        self.redis = RedisClient()
        
        # Use custom lifespan if provided, otherwise use default
        app_lifespan = lifespan if lifespan is not None else self.lifespan
        
        # Create FastAPI app with lifespan
        self.app = FastAPI(
            title=f"OpsConductor {name.title()} Service",
            version=version,
            description=f"OpsConductor {name} service API",
            lifespan=app_lifespan
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
        """Service startup logic"""
        # Initialize database
        database_url = self._get_database_url()
        schema = os.getenv("DB_SCHEMA", "public")
        await self.db.initialize(database_url, schema)
        
        # Initialize Redis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        await self.redis.initialize(redis_url)
        
        # Service-specific startup
        await self.on_startup()
    
    async def _shutdown(self):
        """Service shutdown logic"""
        # Service-specific shutdown
        await self.on_shutdown()
        
        # Close connections
        await self.db.close()
        await self.redis.close()
    
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
        user = os.getenv("DB_USER", "opsconductor")
        password = os.getenv("DB_PASSWORD", "opsconductor_secure_2024")
        
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
        
        # Request logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = asyncio.get_event_loop().time()
            
            # Add request ID
            request_id = request.headers.get("X-Request-ID", f"req_{int(start_time * 1000)}")
            
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
                duration = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Log response
                self.logger.info(
                    "Request completed",
                    method=request.method,
                    url=str(request.url),
                    status_code=response.status_code,
                    duration_ms=duration,
                    request_id=request_id
                )
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                return response
                
            except Exception as e:
                duration = (asyncio.get_event_loop().time() - start_time) * 1000
                self.logger.error(
                    "Request failed",
                    method=request.method,
                    url=str(request.url),
                    error=str(e),
                    duration_ms=duration,
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
            
            # Redis health
            redis_check = await self.redis.health_check()
            checks.append(redis_check)
            
            # Service-specific health checks
            service_checks = await self.get_health_checks()
            checks.extend(service_checks)
            
            # Overall status
            overall_status = "healthy"
            if any(check.status == "unhealthy" for check in checks):
                overall_status = "unhealthy"
            elif any(check.status == "degraded" for check in checks):
                overall_status = "degraded"
            
            # Calculate uptime
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            
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