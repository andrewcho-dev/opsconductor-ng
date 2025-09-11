#!/usr/bin/env python3
"""
OpsConductor API Gateway
Central entry point for all API requests with routing, authentication, and rate limiting
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

# Add shared to path
sys.path.append('/app/shared')
from base_service import HealthCheck

logger = structlog.get_logger("api-gateway")

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

SERVICE_ROUTES = {
    # Identity Service
    "/api/v1/auth": "IDENTITY_SERVICE_URL",
    "/api/v1/users": "IDENTITY_SERVICE_URL",
    "/api/v1/roles": "IDENTITY_SERVICE_URL",
    
    # Asset Service
    "/api/v1/targets": "ASSET_SERVICE_URL",
    "/api/v1/credentials": "ASSET_SERVICE_URL",
    "/api/v1/discovery": "ASSET_SERVICE_URL",
    
    # Automation Service
    "/api/v1/jobs": "AUTOMATION_SERVICE_URL",
    "/api/v1/runs": "AUTOMATION_SERVICE_URL",  # Map runs to executions
    "/api/v1/schedules": "AUTOMATION_SERVICE_URL",
    "/api/v1/workflows": "AUTOMATION_SERVICE_URL",
    "/api/v1/executions": "AUTOMATION_SERVICE_URL",
    "/api/v1/libraries": "AUTOMATION_SERVICE_URL",
    
    # Communication Service
    "/api/v1/notifications": "COMMUNICATION_SERVICE_URL",
    "/api/v1/templates": "COMMUNICATION_SERVICE_URL",
    "/api/v1/channels": "COMMUNICATION_SERVICE_URL",
    "/api/v1/audit": "COMMUNICATION_SERVICE_URL",
}

# Routes that don't require authentication
PUBLIC_ROUTES = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/health"
}

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    def __init__(self, gateway):
        self.gateway = gateway
    
    async def is_allowed(self, key: str, limit: int = 10000, window: int = 60) -> bool:
        """Check if request is within rate limit"""
        try:
            current = await self.gateway.redis.get(f"rate_limit:{key}")
            if current is None:
                await self.gateway.redis.setex(f"rate_limit:{key}", window, 1)
                return True
            
            if int(current) >= limit:
                return False
            
            await self.gateway.redis.incr(f"rate_limit:{key}")
            return True
        except Exception as e:
            logger.error("Rate limiting error", error=str(e))
            return True  # Allow request if rate limiting fails

# ============================================================================
# API GATEWAY SERVICE
# ============================================================================

class APIGateway:
    def __init__(self):
        self.app = FastAPI(
            title="OpsConductor API Gateway",
            description="Central API Gateway for OpsConductor services",
            version="1.0.0"
        )
        self.http_client: Optional[httpx.AsyncClient] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.service_urls: Dict[str, str] = {}
        self.redis = None
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    async def on_startup(self):
        """Initialize HTTP client and service URLs"""
        # Initialize Redis connection
        import redis.asyncio as redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(self)
        
        # Load service URLs
        for route, env_var in SERVICE_ROUTES.items():
            url = os.getenv(env_var)
            if url:
                self.service_urls[route] = url
                logger.info("Service route configured", route=route, url=url)
            else:
                logger.warning("Service URL not configured", route=route, env_var=env_var)
    
    async def on_shutdown(self):
        """Close HTTP client and Redis connection"""
        if self.http_client:
            await self.http_client.aclose()
        if self.redis:
            await self.redis.close()
    
    async def get_health_checks(self) -> list[HealthCheck]:
        """Check health of downstream services"""
        checks = []
        
        # Group routes by service URL to avoid duplicate health checks
        service_urls = {}
        for route, url in self.service_urls.items():
            if url not in service_urls:
                service_urls[url] = []
            service_urls[url].append(route)
        
        # Check each unique service once
        for url, routes in service_urls.items():
            start_time = time.time()
            try:
                response = await self.http_client.get(f"{url}/health", timeout=5.0)
                response_time = (time.time() - start_time) * 1000
                
                # Determine service name from URL
                service_name = url.split('://')[-1].split(':')[0].replace('-service', '').replace('_', '-')
                
                if response.status_code == 200:
                    checks.append(HealthCheck(
                        name=service_name,
                        status="healthy",
                        response_time_ms=response_time
                    ))
                else:
                    checks.append(HealthCheck(
                        name=service_name,
                        status="unhealthy",
                        details={"status_code": response.status_code}
                    ))
            except Exception as e:
                # Determine service name from URL
                service_name = url.split('://')[-1].split(':')[0].replace('-service', '').replace('_', '-')
                checks.append(HealthCheck(
                    name=service_name,
                    status="unhealthy",
                    details={"error": str(e)}
                ))
        
        return checks
    
    def _setup_routes(self):
        """Setup API Gateway routes"""
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            checks = await self.get_health_checks()
            
            # Check Redis connection
            redis_healthy = True
            try:
                await self.redis.ping()
            except Exception:
                redis_healthy = False
            
            checks.append(HealthCheck(
                name="redis",
                status="healthy" if redis_healthy else "unhealthy"
            ))
            
            overall_status = "healthy" if all(check.status == "healthy" for check in checks) else "unhealthy"
            
            return {
                "service": "api-gateway",
                "status": overall_status,
                "version": "1.0.0",
                "timestamp": time.time(),
                "checks": [check.dict() for check in checks]
            }
        
        @self.app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        async def proxy_request(request: Request, path: str):
            """Proxy requests to appropriate services"""
            
            # Rate limiting
            client_ip = request.client.host
            if not await self.rate_limiter.is_allowed(f"ip:{client_ip}"):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # Authentication check (skip for public routes)
            full_path = f"/{path}"
            user_info = None
            
            if full_path not in PUBLIC_ROUTES and not any(full_path.startswith(route) for route in PUBLIC_ROUTES):
                # Extract token from Authorization header
                auth_header = request.headers.get("authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Missing or invalid authorization header"
                    )
                
                # Validate token with Identity Service
                try:
                    identity_service_url = self.service_urls.get("/api/v1/auth")
                    if not identity_service_url:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Identity service not available"
                        )
                    
                    # Call identity service to validate token and get user info
                    response = await self.http_client.get(
                        f"{identity_service_url}/auth/me",
                        headers={"authorization": auth_header}
                    )
                    
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token"
                        )
                    
                    user_info = response.json()
                    
                except httpx.RequestError:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Authentication service unavailable"
                    )
            
            # Find matching service with special route mappings
            service_url = None
            service_path = path
            
            # Special route mappings
            if path.startswith("api/v1/runs"):
                # Map /api/v1/runs/* to /api/v1/executions/*
                service_url = self.service_urls.get("/api/v1/executions")
                service_path = path.replace("api/v1/runs", "api/v1/executions", 1)
            elif path.startswith("api/v1/jobs/") and path.endswith("/run"):
                # Map /api/v1/jobs/{id}/run to POST /api/v1/jobs/{id}/run (automation service)
                service_url = self.service_urls.get("/api/v1/jobs")
                service_path = path  # Keep the path as is
            else:
                # Standard route matching
                for route_prefix, url in self.service_urls.items():
                    if path.startswith(route_prefix.lstrip("/")):
                        service_url = url
                        break
            
            if not service_url:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No service found for path: /{path}"
                )
            
            # Build target URL - strip /api/v1 prefix for service calls
            if service_path.startswith("api/v1/"):
                service_path = service_path[7:]  # Remove "api/v1/" prefix
            target_url = f"{service_url}/{service_path}"
            
            # Prepare request
            headers = dict(request.headers)
            headers.pop("host", None)  # Remove host header
            
            # Add request ID if not present
            if "x-request-id" not in headers:
                headers["x-request-id"] = f"gw_{int(time.time() * 1000)}"
            
            # Add user information to headers for authenticated requests
            if user_info:
                headers["x-user-id"] = str(user_info.get("id"))
                headers["x-username"] = user_info.get("username", "")
                headers["x-user-email"] = user_info.get("email", "")
                headers["x-is-admin"] = str(user_info.get("is_admin", False)).lower()
                headers["x-authenticated"] = "true"
            else:
                headers["x-authenticated"] = "false"
            
            try:
                # Forward request
                if request.method == "GET":
                    response = await self.http_client.get(
                        target_url,
                        params=request.query_params,
                        headers=headers
                    )
                elif request.method == "POST":
                    body = await request.body()
                    response = await self.http_client.post(
                        target_url,
                        content=body,
                        params=request.query_params,
                        headers=headers
                    )
                elif request.method == "PUT":
                    body = await request.body()
                    response = await self.http_client.put(
                        target_url,
                        content=body,
                        params=request.query_params,
                        headers=headers
                    )
                elif request.method == "DELETE":
                    response = await self.http_client.delete(
                        target_url,
                        params=request.query_params,
                        headers=headers
                    )
                elif request.method == "PATCH":
                    body = await request.body()
                    response = await self.http_client.patch(
                        target_url,
                        content=body,
                        params=request.query_params,
                        headers=headers
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        detail=f"Method {request.method} not allowed"
                    )
                
                # Return response
                response_headers = dict(response.headers)
                response_headers.pop("content-length", None)  # Let FastAPI handle this
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response_headers,
                    media_type=response.headers.get("content-type")
                )
                
            except httpx.TimeoutException:
                logger.error("Service timeout", service_url=service_url, path=path)
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Service timeout"
                )
            except httpx.ConnectError:
                logger.error("Service unavailable", service_url=service_url, path=path)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service unavailable"
                )
            except Exception as e:
                logger.error("Proxy error", error=str(e), service_url=service_url, path=path)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Gateway error"
                )

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main application entry point"""
    gateway = APIGateway()
    
    # Setup startup and shutdown events
    @gateway.app.on_event("startup")
    async def startup():
        await gateway.on_startup()
    
    @gateway.app.on_event("shutdown")
    async def shutdown():
        await gateway.on_shutdown()
    
    # Run the application
    import uvicorn
    config = uvicorn.Config(
        gateway.app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())