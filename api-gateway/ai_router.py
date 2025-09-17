"""
OpsConductor AI Router
Intelligent routing and load balancing for AI services
"""
import asyncio
import time
import json
import random
import structlog
import httpx
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict
import redis.asyncio as redis

logger = structlog.get_logger()

class AIServiceType(Enum):
    """Types of AI services"""
    GENERAL = "general"          # General AI queries
    INFRASTRUCTURE = "infrastructure"  # Infrastructure-specific
    AUTOMATION = "automation"      # Automation workflows
    ANALYTICS = "analytics"       # Data analysis
    VISION = "vision"            # Computer vision (future)

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"    # Normal operation
    OPEN = "open"       # Service is failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker for service protection"""
    
    def __init__(
        self,
        failure_threshold: int = 10,  # Increased from 5 to 10
        timeout: float = 30.0,        # Reduced from 60 to 30 seconds
        half_open_requests: int = 5   # Increased from 3 to 5
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_requests = half_open_requests
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_count = 0
    
    def record_success(self):
        """Record successful request"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_count += 1
            if self.half_open_count >= self.half_open_requests:
                # Service recovered
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.half_open_count = 0
                logger.info("Circuit breaker closed (service recovered)")
        else:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened (failures: {self.failure_count})")
    
    def can_request(self) -> bool:
        """Check if request can be made"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time and \
               time.time() - self.last_failure_time > self.timeout:
                # Try half-open state
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_count = 0
                logger.info("Circuit breaker half-open (testing recovery)")
                return True
            return False
        
        # Half-open state
        return self.half_open_count < self.half_open_requests
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.half_open_count = 0
        self.last_failure_time = None

class ServiceEndpoint:
    """Represents an AI service endpoint"""
    
    def __init__(self, name: str, url: str, service_type: AIServiceType):
        self.name = name
        self.url = url
        self.service_type = service_type
        self.circuit_breaker = CircuitBreaker()
        
        # Performance metrics
        self.request_count = 0
        self.success_count = 0
        self.total_response_time = 0.0
        self.last_check_time = None
        self.is_healthy = True
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        if self.success_count == 0:
            return 0.0
        return self.total_response_time / self.success_count
    
    def record_request(self, success: bool, response_time: float):
        """Record request metrics"""
        self.request_count += 1
        
        if success:
            self.success_count += 1
            self.total_response_time += response_time
            self.circuit_breaker.record_success()
        else:
            self.circuit_breaker.record_failure()

class LoadBalancer:
    """Load balancer for AI services"""
    
    def __init__(self):
        self.endpoints: List[ServiceEndpoint] = []
        self.current_index = 0
    
    def add_endpoint(self, endpoint: ServiceEndpoint):
        """Add service endpoint"""
        self.endpoints.append(endpoint)
    
    def get_endpoint(self, strategy: str = "round_robin") -> Optional[ServiceEndpoint]:
        """Get next endpoint based on strategy"""
        available_endpoints = [
            ep for ep in self.endpoints
            if ep.is_healthy and ep.circuit_breaker.can_request()
        ]
        
        if not available_endpoints:
            return None
        
        if strategy == "round_robin":
            endpoint = available_endpoints[self.current_index % len(available_endpoints)]
            self.current_index += 1
            return endpoint
        
        elif strategy == "least_response_time":
            return min(available_endpoints, key=lambda ep: ep.avg_response_time)
        
        elif strategy == "weighted_random":
            # Weight by success rate
            weights = [ep.success_rate + 0.1 for ep in available_endpoints]  # +0.1 to avoid 0
            return random.choices(available_endpoints, weights=weights)[0]
        
        else:
            return available_endpoints[0]

class AIRouter:
    """Main AI request router"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.load_balancers: Dict[AIServiceType, LoadBalancer] = {}
        
        # Initialize service endpoints
        self._initialize_endpoints()
        
        # Request cache
        self.cache_ttl = 300  # 5 minutes
        self.request_cache = {}
        
        # Metrics
        self.metrics = defaultdict(lambda: {
            "total_requests": 0,
            "cache_hits": 0,
            "failures": 0,
            "total_response_time": 0.0
        })
    
    def _initialize_endpoints(self):
        """Initialize AI service endpoints"""
        # Main AI Command service
        ai_command = ServiceEndpoint(
            name="ai_command",
            url="http://ai-command:3005",
            service_type=AIServiceType.GENERAL
        )
        
        # AI Orchestrator
        ai_orchestrator = ServiceEndpoint(
            name="ai_orchestrator",
            url="http://ai-orchestrator:3000",
            service_type=AIServiceType.AUTOMATION
        )
        
        # Initialize load balancers
        for service_type in AIServiceType:
            self.load_balancers[service_type] = LoadBalancer()
        
        # Add endpoints to load balancers
        self.load_balancers[AIServiceType.GENERAL].add_endpoint(ai_command)
        self.load_balancers[AIServiceType.AUTOMATION].add_endpoint(ai_orchestrator)
        
        # AI Command can handle multiple types
        self.load_balancers[AIServiceType.INFRASTRUCTURE].add_endpoint(ai_command)
        self.load_balancers[AIServiceType.ANALYTICS].add_endpoint(ai_command)
    
    async def route_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route AI request to appropriate service"""
        start_time = time.time()
        
        try:
            # Extract query and determine service type
            query = request_data.get("query", "")
            service_type = self._determine_service_type(query)
            
            # Check cache
            cache_key = self._generate_cache_key(request_data)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                self.metrics[service_type]["cache_hits"] += 1
                return cached_response
            
            # Get endpoint
            load_balancer = self.load_balancers.get(service_type)
            if not load_balancer:
                return {
                    "success": False,
                    "error": f"No load balancer for service type: {service_type}"
                }
            
            endpoint = load_balancer.get_endpoint()
            if not endpoint:
                return {
                    "success": False,
                    "error": f"No available endpoints for service type: {service_type}"
                }
            
            # Make request
            response = await self._make_request(endpoint, request_data)
            
            # Record metrics
            response_time = time.time() - start_time
            success = response.get("success", False)
            
            endpoint.record_request(success, response_time)
            self.metrics[service_type]["total_requests"] += 1
            self.metrics[service_type]["total_response_time"] += response_time
            
            if not success:
                self.metrics[service_type]["failures"] += 1
            
            # Cache successful responses
            if success:
                await self._cache_response(cache_key, response)
            
            # Add routing metadata
            response["_routing"] = {
                "service": endpoint.name,
                "service_type": service_type.value,
                "response_time": response_time,
                "cached": False
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return {
                "success": False,
                "error": f"Routing failed: {str(e)}"
            }
    
    def _determine_service_type(self, query: str) -> AIServiceType:
        """Determine which service type should handle the query"""
        query_lower = query.lower()
        
        # Check for specific patterns
        if any(word in query_lower for word in ["workflow", "automation", "schedule", "job"]):
            return AIServiceType.AUTOMATION
        
        if any(word in query_lower for word in ["target", "server", "infrastructure", "host"]):
            return AIServiceType.INFRASTRUCTURE
        
        if any(word in query_lower for word in ["analyze", "predict", "trend", "metric"]):
            return AIServiceType.ANALYTICS
        
        # NLP tasks (translate, summarize, extract) now handled by ai_command via GENERAL
        # No separate NLP service needed - Ollama can handle these tasks
        
        # Default to general
        return AIServiceType.GENERAL
    
    async def _make_request(
        self,
        endpoint: ServiceEndpoint,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make request to AI service"""
        try:
            # Prepare request - use correct endpoint path for ai-command service
            if "ai-command" in endpoint.url:
                url = f"{endpoint.url}/ai/chat"
                # Transform request for ai-command service (expects 'message' not 'query')
                if "query" in request_data and "message" not in request_data:
                    request_data["message"] = request_data.pop("query")
            else:
                url = f"{endpoint.url}/ai/process"
            
            # Add routing context
            request_data["_context"] = {
                "routed_from": "ai_router",
                "service_type": endpoint.service_type.value,
                "timestamp": time.time()
            }
            
            # Make request
            response = await self.http_client.post(
                url,
                json=request_data,
                timeout=25.0
            )
            
            if response.status_code == 200:
                result = response.json()
                # Mark as successful if we got a 200 response
                result["success"] = True
                return result
            else:
                return {
                    "success": False,
                    "error": f"Service returned {response.status_code}"
                }
                
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        # Use query and key parameters for cache key
        key_parts = [
            request_data.get("query", ""),
            str(request_data.get("user_id", "anonymous")),
            str(request_data.get("context_id", ""))
        ]
        
        key_string = "|".join(key_parts)
        return f"ai_cache:{hash(key_string)}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    response = json.loads(cached)
                    response["_routing"] = response.get("_routing", {})
                    response["_routing"]["cached"] = True
                    return response
            except Exception as e:
                logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def _cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache response"""
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(response)
                )
            except Exception as e:
                logger.warning(f"Cache set error: {e}")
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services"""
        health_status = {}
        
        for service_type, load_balancer in self.load_balancers.items():
            for endpoint in load_balancer.endpoints:
                try:
                    # Check health endpoint
                    response = await self.http_client.get(
                        f"{endpoint.url}/health",
                        timeout=5.0
                    )
                    
                    endpoint.is_healthy = response.status_code == 200
                    endpoint.last_check_time = time.time()
                    
                    health_status[endpoint.name] = {
                        "status": "healthy" if endpoint.is_healthy else "unhealthy",
                        "url": endpoint.url,
                        "service_type": endpoint.service_type.value,
                        "circuit_breaker": endpoint.circuit_breaker.state.value,
                        "success_rate": endpoint.success_rate,
                        "avg_response_time": endpoint.avg_response_time,
                        "request_count": endpoint.request_count
                    }
                    
                except Exception as e:
                    endpoint.is_healthy = False
                    health_status[endpoint.name] = {
                        "status": "unavailable",
                        "error": str(e),
                        "url": endpoint.url,
                        "service_type": endpoint.service_type.value
                    }
        
        return health_status
    
    async def reset_circuit_breaker(self, service_name: str):
        """Reset circuit breaker for a service"""
        for load_balancer in self.load_balancers.values():
            for endpoint in load_balancer.endpoints:
                if endpoint.name == service_name:
                    endpoint.circuit_breaker.reset()
                    logger.info(f"Circuit breaker reset for {service_name}")
                    return
        
        raise ValueError(f"Service {service_name} not found")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get routing metrics"""
        metrics_summary = {
            "by_service_type": {},
            "total": {
                "requests": 0,
                "cache_hits": 0,
                "failures": 0,
                "avg_response_time": 0.0
            }
        }
        
        total_requests = 0
        total_response_time = 0.0
        
        for service_type, metrics in self.metrics.items():
            if metrics["total_requests"] > 0:
                avg_response_time = metrics["total_response_time"] / metrics["total_requests"]
                cache_hit_rate = metrics["cache_hits"] / metrics["total_requests"]
                failure_rate = metrics["failures"] / metrics["total_requests"]
                
                metrics_summary["by_service_type"][service_type.value] = {
                    "requests": metrics["total_requests"],
                    "cache_hit_rate": cache_hit_rate,
                    "failure_rate": failure_rate,
                    "avg_response_time": avg_response_time
                }
                
                metrics_summary["total"]["requests"] += metrics["total_requests"]
                metrics_summary["total"]["cache_hits"] += metrics["cache_hits"]
                metrics_summary["total"]["failures"] += metrics["failures"]
                total_response_time += metrics["total_response_time"]
        
        if metrics_summary["total"]["requests"] > 0:
            metrics_summary["total"]["avg_response_time"] = (
                total_response_time / metrics_summary["total"]["requests"]
            )
        
        return metrics_summary
    
    async def submit_feedback(
        self,
        interaction_id: str,
        user_id: str,
        rating: int,
        comment: Optional[str] = None,
        correction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit feedback for an interaction"""
        feedback_data = {
            "interaction_id": interaction_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "correction": correction,
            "timestamp": time.time()
        }
        
        # Store in Redis
        if self.redis_client:
            feedback_key = f"ai:feedback:{interaction_id}"
            await self.redis_client.setex(
                feedback_key,
                86400 * 7,  # 7 days
                json.dumps(feedback_data)
            )
        
        # Forward to learning system if available
        # This would integrate with the learning orchestrator
        
        return {
            "feedback_id": f"fb_{interaction_id}",
            "stored": True
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()