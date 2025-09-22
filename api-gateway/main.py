#!/usr/bin/env python3
"""
OpsConductor API Gateway
Central entry point for all API requests with routing, authentication, and rate limiting
"""

import os
import sys
import asyncio
import time
import json
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

# Import AI Router
try:
    from ai_router import AIRouter
    AI_ROUTER_AVAILABLE = True
except ImportError:
    AI_ROUTER_AVAILABLE = False
    logger.warning("AI Router not available")

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

SERVICE_ROUTES = {
    # Identity Service
    "/api/v1/auth": "IDENTITY_SERVICE_URL",
    "/api/v1/users": "IDENTITY_SERVICE_URL",
    "/api/v1/roles": "IDENTITY_SERVICE_URL",
    "/api/v1/available-roles": "IDENTITY_SERVICE_URL",
    
    # Asset Service
    "/api/v1/assets": "ASSET_SERVICE_URL",
    "/api/v1/metadata": "ASSET_SERVICE_URL",
    
    # Automation Service
    "/api/v1/jobs": "AUTOMATION_SERVICE_URL",
    "/api/v1/runs": "AUTOMATION_SERVICE_URL",  # Map runs to executions
    "/api/v1/schedules": "AUTOMATION_SERVICE_URL",
    "/api/v1/workflows": "AUTOMATION_SERVICE_URL",
    "/api/v1/executions": "AUTOMATION_SERVICE_URL",
    "/api/v1/automation": "AUTOMATION_SERVICE_URL",  # Direct automation service endpoints

    "/api/v1/tasks": "AUTOMATION_SERVICE_URL",  # Direct Celery task status
    
    # Communication Service
    "/api/v1/templates": "COMMUNICATION_SERVICE_URL",
    "/api/v1/channels": "COMMUNICATION_SERVICE_URL",
    "/api/v1/notifications": "COMMUNICATION_SERVICE_URL",
    "/api/v1/audit": "COMMUNICATION_SERVICE_URL",
    
    # Network Analyzer Service
    "/api/v1/network": "NETWORK_ANALYZER_SERVICE_URL",
    "/api/v1/analysis": "NETWORK_ANALYZER_SERVICE_URL",
    "/api/v1/monitoring": "NETWORK_ANALYZER_SERVICE_URL",
    "/api/v1/remote": "NETWORK_ANALYZER_SERVICE_URL",
    
    # AI Services
    "/api/v1/ai": "AI_SERVICE_URL",  # AI Orchestrator
    "/api/v1/ai-overview": "AI_OVERVIEW_SERVICE_URL",  # AI Overview Service
    "/api/v1/vector": "VECTOR_SERVICE_URL",  # Vector Service
    "/api/v1/llm": "LLM_SERVICE_URL",  # LLM Service
}

# Routes that don't require authentication
# All API routes are public for internal service communication
# Authentication is only required at the user login level
PUBLIC_ROUTES = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/health",
    "/api/v1/"  # This will match all API routes as public
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
        self.ai_router: Optional[AIRouter] = None
        
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
        
        # Initialize AI Router if available
        if AI_ROUTER_AVAILABLE:
            try:
                self.ai_router = AIRouter(redis_client=self.redis)
                logger.info("AI Router initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize AI Router", error=str(e))
                self.ai_router = None
        
        # Initialize AI Monitoring Dashboard
        try:
            from ai_monitoring import AIMonitoringDashboard
            self.ai_dashboard = AIMonitoringDashboard(redis_client=self.redis)
            # Start monitoring in background with longer interval
            asyncio.create_task(self.ai_dashboard.start_monitoring(interval=60))
            logger.info("AI Monitoring Dashboard initialized")
        except Exception as e:
            logger.warning(f"AI Monitoring Dashboard not available: {e}")
            self.ai_dashboard = None
        
        # Load service URLs
        for route, env_var in SERVICE_ROUTES.items():
            url = os.getenv(env_var)
            if url:
                self.service_urls[route] = url
                logger.info("Service route configured", route=route, url=url)
            else:
                logger.warning("Service URL not configured", route=route, env_var=env_var)
    
    async def on_shutdown(self):
        """Close HTTP client, Redis connection, and AI router"""
        if self.http_client:
            await self.http_client.aclose()
        if self.ai_router:
            await self.ai_router.cleanup()
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
                
                # Determine service name from URL - keep full service names for clarity
                service_name = url.split('://')[-1].split(':')[0].replace('_', '-')
                
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
                # Determine service name from URL - keep full service names for clarity
                service_name = url.split('://')[-1].split(':')[0].replace('_', '-')
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
            
            # Check PostgreSQL connection
            postgres_healthy = True
            try:
                import asyncpg
                conn = await asyncpg.connect(
                    host=os.getenv('POSTGRES_HOST', 'postgres'),
                    port=int(os.getenv('POSTGRES_PORT', '5432')),
                    user=os.getenv('POSTGRES_USER', 'postgres'),
                    password=os.getenv('POSTGRES_PASSWORD', 'postgres123'),
                    database=os.getenv('POSTGRES_DB', 'opsconductor'),
                    timeout=5.0
                )
                await conn.execute('SELECT 1')
                await conn.close()
            except Exception:
                postgres_healthy = False
            
            checks.append(HealthCheck(
                name="postgres",
                status="healthy" if postgres_healthy else "unhealthy"
            ))
            
            # Check ChromaDB connection
            chromadb_healthy = True
            try:
                response = await self.http_client.get("http://chromadb:8000/api/v1/heartbeat", timeout=5.0)
                chromadb_healthy = response.status_code == 200
            except Exception:
                chromadb_healthy = False
            
            checks.append(HealthCheck(
                name="chromadb",
                status="healthy" if chromadb_healthy else "unhealthy"
            ))
            
            # Check Ollama connection
            ollama_healthy = True
            try:
                response = await self.http_client.get("http://ollama:11434/api/tags", timeout=5.0)
                ollama_healthy = response.status_code == 200
            except Exception:
                ollama_healthy = False
            
            checks.append(HealthCheck(
                name="ollama",
                status="healthy" if ollama_healthy else "unhealthy"
            ))
            

            
            # Check Frontend (React app)
            frontend_healthy = True
            try:
                response = await self.http_client.get("http://frontend:3000", timeout=5.0)
                frontend_healthy = response.status_code in [200, 301, 302]
            except Exception:
                frontend_healthy = False
            
            checks.append(HealthCheck(
                name="frontend",
                status="healthy" if frontend_healthy else "unhealthy"
            ))
            
            # Check Celery Monitor (Flower)
            celery_monitor_healthy = True
            try:
                response = await self.http_client.get("http://celery-monitor:5555", timeout=5.0)
                celery_monitor_healthy = response.status_code in [200, 401]  # 401 is OK (auth required)
            except Exception:
                celery_monitor_healthy = False
            
            checks.append(HealthCheck(
                name="celery-monitor",
                status="healthy" if celery_monitor_healthy else "unhealthy"
            ))
            
            # Check Celery Workers through Redis/Celery inspection
            try:
                # Check if workers are registered in Celery
                worker_stats = await self.redis.get("celery-worker-stats")
                
                # Check worker-1
                worker1_healthy = True
                try:
                    # Simple check - if Redis is accessible and workers are in the system
                    # This is a basic check; in production you'd want more sophisticated monitoring
                    worker1_key = await self.redis.get("worker-1-heartbeat")
                    # If no specific heartbeat, assume healthy if Redis is working
                    worker1_healthy = True
                except Exception:
                    worker1_healthy = False
                
                checks.append(HealthCheck(
                    name="worker-1",
                    status="healthy" if worker1_healthy else "unhealthy"
                ))
                
                # Check worker-2
                worker2_healthy = True
                try:
                    worker2_key = await self.redis.get("worker-2-heartbeat")
                    worker2_healthy = True
                except Exception:
                    worker2_healthy = False
                
                checks.append(HealthCheck(
                    name="worker-2",
                    status="healthy" if worker2_healthy else "unhealthy"
                ))
                
                # Check scheduler (Celery Beat)
                scheduler_healthy = True
                try:
                    scheduler_key = await self.redis.get("celery-beat-heartbeat")
                    scheduler_healthy = True
                except Exception:
                    scheduler_healthy = False
                
                checks.append(HealthCheck(
                    name="scheduler",
                    status="healthy" if scheduler_healthy else "unhealthy"
                ))
                
            except Exception as e:
                # If we can't check workers, mark them as unknown
                logger.warning("Could not check worker status", error=str(e))
                checks.extend([
                    HealthCheck(name="worker-1", status="unknown"),
                    HealthCheck(name="worker-2", status="unknown"),
                    HealthCheck(name="scheduler", status="unknown")
                ])
            

            
            overall_status = "healthy" if all(check.status == "healthy" for check in checks) else "unhealthy"
            
            return {
                "service": "api-gateway",
                "status": overall_status,
                "version": "1.0.0",
                "timestamp": time.time(),
                "checks": [check.model_dump() for check in checks]
            }
        
        # Unified AI endpoint
        @self.app.post("/api/v1/ai/chat")
        async def unified_ai_chat(request: Request):
            """Unified AI chat endpoint with intelligent routing"""
            if not self.ai_router:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI Router not available"
                )
            
            try:
                # Get request body
                body = await request.json()
                
                # Extract user info from headers if available
                user_info = {}
                if request.headers.get("x-user-id"):
                    user_info = {
                        "id": request.headers.get("x-user-id"),
                        "username": request.headers.get("x-username", ""),
                        "email": request.headers.get("x-user-email", ""),
                        "role": request.headers.get("x-user-role", "viewer")
                    }
                
                # Add user context to request
                if user_info:
                    body["user_id"] = user_info.get("id", "anonymous")
                    body["user_context"] = user_info
                
                # Route through AI router
                response = await self.ai_router.route_request(body)
                
                return JSONResponse(content=response)
                
            except Exception as e:
                logger.error("AI chat error", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI processing failed: {str(e)}"
                )
        
        # AI service health endpoint
        @self.app.get("/api/v1/ai/health")
        async def ai_health():
            """Get health status of all AI services"""
            if not self.ai_router:
                return {
                    "status": "unavailable",
                    "message": "AI Router not initialized"
                }
            
            try:
                health_status = await self.ai_router.get_service_health()
                
                # Determine overall status
                all_healthy = all(
                    s.get("status") == "healthy" 
                    for s in health_status.values()
                )
                
                return {
                    "status": "healthy" if all_healthy else "degraded",
                    "services": health_status,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error("AI health check failed", error=str(e))
                return {
                    "status": "error",
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        # Circuit breaker reset endpoint (admin only)
        @self.app.post("/api/v1/ai/circuit-breaker/reset/{service_name}")
        async def reset_circuit_breaker(service_name: str, request: Request):
            """Reset circuit breaker for a specific AI service (admin only)"""
            # Check if user is admin
            user_role = request.headers.get("x-user-role", "")
            if user_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can reset circuit breakers"
                )
            
            if not self.ai_router:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI Router not available"
                )
            
            try:
                await self.ai_router.reset_circuit_breaker(service_name)
                return {
                    "success": True,
                    "message": f"Circuit breaker for {service_name} has been reset"
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to reset circuit breaker: {str(e)}"
                )
        
        # AI Monitoring Dashboard endpoints
        @self.app.get("/api/v1/ai/monitoring/dashboard")
        async def get_ai_dashboard():
            """Get AI monitoring dashboard data"""
            if not self.ai_dashboard:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI Monitoring Dashboard not available"
                )
            
            try:
                dashboard_data = await self.ai_dashboard.get_dashboard_data()
                return JSONResponse(content=dashboard_data)
            except Exception as e:
                logger.error(f"Failed to get dashboard data: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get dashboard data: {str(e)}"
                )
        
        @self.app.get("/api/v1/ai/monitoring/service/{service_name}")
        async def get_service_monitoring(service_name: str):
            """Get detailed monitoring data for a specific AI service"""
            if not self.ai_dashboard:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI Monitoring Dashboard not available"
                )
            
            try:
                service_data = await self.ai_dashboard.get_service_details(service_name)
                return JSONResponse(content=service_data)
            except Exception as e:
                logger.error(f"Failed to get service data: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get service data: {str(e)}"
                )
        
        @self.app.post("/api/v1/ai/monitoring/health-check")
        async def trigger_ai_health_check(request: Request):
            """Manually trigger health check of all AI services (admin only)"""
            # Check if user is admin
            user_role = request.headers.get("x-user-role", "")
            if user_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can trigger health checks"
                )
            
            if not self.ai_dashboard:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI Monitoring Dashboard not available"
                )
            
            try:
                results = await self.ai_dashboard.trigger_health_check()
                return JSONResponse(content=results)
            except Exception as e:
                logger.error(f"Failed to trigger health check: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to trigger health check: {str(e)}"
                )
        
        # AI Feedback endpoint
        @self.app.post("/api/v1/ai/feedback")
        async def submit_ai_feedback(request: Request):
            """Submit feedback for an AI interaction"""
            try:
                body = await request.json()
                
                # Extract required fields
                interaction_id = body.get("interaction_id")
                rating = body.get("rating")  # 1-5 scale
                
                if not interaction_id or rating is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="interaction_id and rating are required"
                    )
                
                # Get user info from headers
                user_id = request.headers.get("x-user-id", "anonymous")
                
                # Forward to learning system if available
                if self.ai_router and hasattr(self.ai_router, 'submit_feedback'):
                    result = await self.ai_router.submit_feedback(
                        interaction_id=interaction_id,
                        user_id=user_id,
                        rating=rating,
                        comment=body.get("comment"),
                        correction=body.get("correction")
                    )
                    return JSONResponse(content={
                        "success": True,
                        "message": "Feedback submitted successfully",
                        "feedback_id": result.get("feedback_id")
                    })
                else:
                    # Store feedback in Redis for later processing
                    if self.redis:
                        feedback_data = {
                            "interaction_id": interaction_id,
                            "user_id": user_id,
                            "rating": rating,
                            "comment": body.get("comment"),
                            "correction": body.get("correction"),
                            "timestamp": time.time()
                        }
                        
                        feedback_key = f"ai:feedback:{interaction_id}"
                        await self.redis.setex(
                            feedback_key,
                            86400 * 7,  # 7 days TTL
                            json.dumps(feedback_data)
                        )
                        
                        return JSONResponse(content={
                            "success": True,
                            "message": "Feedback stored for processing"
                        })
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Feedback system not available"
                        )
                        
            except Exception as e:
                logger.error(f"Failed to submit feedback: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to submit feedback: {str(e)}"
                )
        
        @self.app.websocket("/{path:path}")
        async def proxy_websocket(websocket, path: str):
            """Proxy WebSocket connections to appropriate services"""
            return await self._proxy_websocket(websocket, path)
        
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
                    
                    auth_response = response.json()
                    user_info = auth_response.get("data", {}) if auth_response.get("success") else {}
                    
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
            elif path.startswith("api/v1/automation/monitoring/"):
                # Map /api/v1/automation/monitoring/* to /monitoring/*
                service_url = self.service_urls.get("/api/v1/automation")
                service_path = path.replace("api/v1/automation/", "", 1)
            else:
                # Standard route matching - fix the logic here
                for route_prefix, url in self.service_urls.items():
                    # Remove leading slash from route_prefix for comparison
                    stripped_prefix = route_prefix.lstrip("/")
                    # Check if path starts with the stripped prefix
                    if path.startswith(stripped_prefix):
                        service_url = url
                        break
            
            if not service_url:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No service found for path: /{path}"
                )
            
            # Build target URL - strip /api/v1/ prefix for service calls
            # Services expect paths without the /api/v1/ prefix
            if service_path.startswith("api/v1/"):
                service_path = service_path[7:]  # Remove "api/v1/" prefix
            elif service_path.startswith("/api/v1/"):
                service_path = service_path[8:]  # Remove "/api/v1/" prefix
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
                headers["x-user-role"] = user_info.get("role", "viewer")
                headers["x-user-permissions"] = ",".join(user_info.get("permissions", []))
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

    async def _proxy_websocket(self, websocket, path: str):
        """Proxy WebSocket connections to backend services"""
        from fastapi import WebSocket, WebSocketDisconnect
        import websockets
        import asyncio
        
        # Find matching service
        service_url = None
        service_path = path
        
        # Special route mappings for WebSocket
        if path.startswith("api/v1/automation/monitoring/"):
            # Map /api/v1/automation/monitoring/* to /monitoring/*
            service_url = self.service_urls.get("/api/v1/automation")
            service_path = path.replace("api/v1/automation/", "", 1)
        else:
            # Standard route matching
            for route_prefix, url in self.service_urls.items():
                if path.startswith(route_prefix.lstrip("/")):
                    service_url = url
                    break
        
        if not service_url:
            await websocket.close(code=1000, reason="No service found")
            return
        
        # Build target WebSocket URL
        if service_path.startswith("api/v1/"):
            service_path = service_path[7:]  # Remove "api/v1/" prefix
        
        # Convert HTTP URL to WebSocket URL
        ws_url = service_url.replace("http://", "ws://").replace("https://", "wss://")
        target_url = f"{ws_url}/{service_path}"
        
        await websocket.accept()
        
        try:
            # Connect to backend WebSocket
            async with websockets.connect(target_url) as backend_ws:
                # Create tasks for bidirectional communication
                async def forward_to_backend():
                    try:
                        while True:
                            data = await websocket.receive_text()
                            await backend_ws.send(data)
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        logger.error(f"Error forwarding to backend: {e}")
                
                async def forward_to_client():
                    try:
                        async for message in backend_ws:
                            await websocket.send_text(message)
                    except Exception as e:
                        logger.error(f"Error forwarding to client: {e}")
                
                # Run both tasks concurrently
                await asyncio.gather(
                    forward_to_backend(),
                    forward_to_client(),
                    return_exceptions=True
                )
        
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}")
            await websocket.close(code=1011, reason="Backend error")

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