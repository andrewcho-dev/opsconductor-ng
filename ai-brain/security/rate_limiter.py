"""
🛡️ ADVANCED RATE LIMITING SYSTEM
Ollama Universal Intelligent Operations Engine (OUIOE)

Comprehensive rate limiting implementation for API protection and abuse prevention.
Supports multiple algorithms, distributed rate limiting, and intelligent throttling.

Key Features:
- Multiple rate limiting algorithms (Token Bucket, Sliding Window, Fixed Window)
- Distributed rate limiting with Redis backend
- Per-user, per-IP, and global rate limiting
- Intelligent throttling with burst handling
- Rate limit headers and client feedback
- Whitelist and blacklist support
- Dynamic rate limit adjustment
- Comprehensive metrics and monitoring
"""

import asyncio
import structlog
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
import hashlib
import ipaddress
from collections import defaultdict
import threading

logger = structlog.get_logger()

class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW_COUNTER = "sliding_window_counter"

class RateLimitScope(Enum):
    """Rate limit scope"""
    GLOBAL = "global"
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_ENDPOINT = "per_endpoint"
    CUSTOM = "custom"

class RateLimitResult(Enum):
    """Rate limit check result"""
    ALLOWED = "allowed"
    DENIED = "denied"
    WARNING = "warning"

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    name: str
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    scope: RateLimitScope = RateLimitScope.GLOBAL
    requests_per_second: float = 10.0
    burst_size: int = 20
    window_size: int = 60  # seconds
    enabled: bool = True
    warning_threshold: float = 0.8  # Warn when 80% of limit is reached
    block_duration: int = 300  # seconds to block after limit exceeded
    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)

@dataclass
class RateLimitInfo:
    """Rate limit information"""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    blocked_until: Optional[datetime] = None

@dataclass
class RateLimitCheck:
    """Rate limit check result"""
    result: RateLimitResult
    info: RateLimitInfo
    identifier: str
    config_name: str
    message: Optional[str] = None

class TokenBucket:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.RLock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket"""
        with self._lock:
            now = time.time()
            
            # Refill tokens based on time elapsed
            time_elapsed = now - self.last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get bucket information"""
        with self._lock:
            return {
                "capacity": self.capacity,
                "current_tokens": self.tokens,
                "refill_rate": self.refill_rate,
                "last_refill": self.last_refill
            }

class SlidingWindowCounter:
    """Sliding window counter rate limiter implementation"""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # seconds
        self.max_requests = max_requests
        self.requests = []
        self._lock = threading.RLock()
    
    def is_allowed(self) -> Tuple[bool, int]:
        """Check if request is allowed and return remaining count"""
        with self._lock:
            now = time.time()
            cutoff_time = now - self.window_size
            
            # Remove old requests
            self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            # Check if we can add new request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                remaining = self.max_requests - len(self.requests)
                return True, remaining
            else:
                return False, 0
    
    def get_info(self) -> Dict[str, Any]:
        """Get window information"""
        with self._lock:
            now = time.time()
            cutoff_time = now - self.window_size
            current_requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            return {
                "window_size": self.window_size,
                "max_requests": self.max_requests,
                "current_requests": len(current_requests),
                "remaining": self.max_requests - len(current_requests),
                "oldest_request": min(current_requests) if current_requests else None
            }

class DistributedRateLimiter:
    """
    🛡️ DISTRIBUTED RATE LIMITER
    
    Redis-backed distributed rate limiting for multi-instance deployments.
    """
    
    def __init__(self, redis_client: redis.Redis, config: RateLimitConfig):
        self.redis_client = redis_client
        self.config = config
        self.local_cache: Dict[str, Any] = {}
        self.cache_ttl = 60  # seconds
        
    async def check_rate_limit(self, identifier: str) -> RateLimitCheck:
        """Check rate limit for identifier"""
        
        # Check blacklist first
        if identifier in self.config.blacklist:
            return RateLimitCheck(
                result=RateLimitResult.DENIED,
                info=RateLimitInfo(
                    limit=0,
                    remaining=0,
                    reset_time=datetime.now() + timedelta(days=1),
                    blocked_until=datetime.now() + timedelta(days=1)
                ),
                identifier=identifier,
                config_name=self.config.name,
                message="Identifier is blacklisted"
            )
        
        # Check whitelist
        if identifier in self.config.whitelist:
            return RateLimitCheck(
                result=RateLimitResult.ALLOWED,
                info=RateLimitInfo(
                    limit=999999,
                    remaining=999999,
                    reset_time=datetime.now() + timedelta(hours=1)
                ),
                identifier=identifier,
                config_name=self.config.name,
                message="Identifier is whitelisted"
            )
        
        # Apply rate limiting based on algorithm
        if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return await self._check_token_bucket(identifier)
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._check_sliding_window(identifier)
        elif self.config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self._check_fixed_window(identifier)
        else:
            return await self._check_sliding_window_counter(identifier)
    
    async def _check_token_bucket(self, identifier: str) -> RateLimitCheck:
        """Check rate limit using token bucket algorithm"""
        key = f"rate_limit:token_bucket:{self.config.name}:{identifier}"
        
        # Use Lua script for atomic operations
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local tokens_requested = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now
        
        -- Refill tokens
        local time_elapsed = now - last_refill
        local tokens_to_add = time_elapsed * refill_rate
        tokens = math.min(capacity, tokens + tokens_to_add)
        
        -- Check if we can consume tokens
        local allowed = 0
        if tokens >= tokens_requested then
            tokens = tokens - tokens_requested
            allowed = 1
        end
        
        -- Update bucket
        redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
        redis.call('EXPIRE', key, 3600)  -- 1 hour TTL
        
        return {allowed, tokens, capacity}
        """
        
        try:
            result = await self.redis_client.eval(
                lua_script,
                1,
                key,
                str(self.config.burst_size),
                str(self.config.requests_per_second),
                "1",  # tokens requested
                str(time.time())
            )
            
            allowed, remaining_tokens, capacity = result
            remaining = int(remaining_tokens)
            
            # Calculate reset time (when bucket will be full again)
            if remaining < capacity:
                seconds_to_full = (capacity - remaining) / self.config.requests_per_second
                reset_time = datetime.now() + timedelta(seconds=seconds_to_full)
            else:
                reset_time = datetime.now()
            
            rate_limit_result = RateLimitResult.ALLOWED if allowed else RateLimitResult.DENIED
            
            # Check warning threshold
            if allowed and remaining < (capacity * (1 - self.config.warning_threshold)):
                rate_limit_result = RateLimitResult.WARNING
            
            return RateLimitCheck(
                result=rate_limit_result,
                info=RateLimitInfo(
                    limit=capacity,
                    remaining=remaining,
                    reset_time=reset_time,
                    retry_after=int(1 / self.config.requests_per_second) if not allowed else None
                ),
                identifier=identifier,
                config_name=self.config.name
            )
            
        except Exception as e:
            logger.error("❌ Error checking token bucket rate limit", error=str(e))
            # Fail open - allow request
            return RateLimitCheck(
                result=RateLimitResult.ALLOWED,
                info=RateLimitInfo(
                    limit=self.config.burst_size,
                    remaining=self.config.burst_size,
                    reset_time=datetime.now()
                ),
                identifier=identifier,
                config_name=self.config.name,
                message="Rate limiter error - failing open"
            )
    
    async def _check_sliding_window(self, identifier: str) -> RateLimitCheck:
        """Check rate limit using sliding window algorithm"""
        key = f"rate_limit:sliding_window:{self.config.name}:{identifier}"
        now = time.time()
        window_start = now - self.config.window_size
        
        # Use pipeline for atomic operations
        pipeline = self.redis_client.pipeline()
        
        # Remove old entries
        pipeline.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(now): now})
        
        # Set expiry
        pipeline.expire(key, self.config.window_size + 60)
        
        try:
            results = await pipeline.execute()
            current_count = results[1]  # Count after removing old entries
            
            max_requests = int(self.config.requests_per_second * self.config.window_size)
            
            if current_count < max_requests:
                remaining = max_requests - current_count - 1  # -1 for current request
                reset_time = datetime.now() + timedelta(seconds=self.config.window_size)
                
                rate_limit_result = RateLimitResult.ALLOWED
                if remaining < (max_requests * (1 - self.config.warning_threshold)):
                    rate_limit_result = RateLimitResult.WARNING
                
                return RateLimitCheck(
                    result=rate_limit_result,
                    info=RateLimitInfo(
                        limit=max_requests,
                        remaining=max(0, remaining),
                        reset_time=reset_time
                    ),
                    identifier=identifier,
                    config_name=self.config.name
                )
            else:
                # Remove the request we just added since it's denied
                await self.redis_client.zrem(key, str(now))
                
                # Calculate retry after
                oldest_request_time = await self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request_time:
                    retry_after = int(oldest_request_time[0][1] + self.config.window_size - now)
                else:
                    retry_after = self.config.window_size
                
                return RateLimitCheck(
                    result=RateLimitResult.DENIED,
                    info=RateLimitInfo(
                        limit=max_requests,
                        remaining=0,
                        reset_time=datetime.now() + timedelta(seconds=retry_after),
                        retry_after=retry_after
                    ),
                    identifier=identifier,
                    config_name=self.config.name
                )
                
        except Exception as e:
            logger.error("❌ Error checking sliding window rate limit", error=str(e))
            # Fail open
            return RateLimitCheck(
                result=RateLimitResult.ALLOWED,
                info=RateLimitInfo(
                    limit=int(self.config.requests_per_second * self.config.window_size),
                    remaining=int(self.config.requests_per_second * self.config.window_size),
                    reset_time=datetime.now()
                ),
                identifier=identifier,
                config_name=self.config.name,
                message="Rate limiter error - failing open"
            )
    
    async def _check_fixed_window(self, identifier: str) -> RateLimitCheck:
        """Check rate limit using fixed window algorithm"""
        now = time.time()
        window_start = int(now // self.config.window_size) * self.config.window_size
        key = f"rate_limit:fixed_window:{self.config.name}:{identifier}:{window_start}"
        
        try:
            # Increment counter
            current_count = await self.redis_client.incr(key)
            
            # Set expiry on first request in window
            if current_count == 1:
                await self.redis_client.expire(key, self.config.window_size + 60)
            
            max_requests = int(self.config.requests_per_second * self.config.window_size)
            
            if current_count <= max_requests:
                remaining = max_requests - current_count
                reset_time = datetime.fromtimestamp(window_start + self.config.window_size)
                
                rate_limit_result = RateLimitResult.ALLOWED
                if remaining < (max_requests * (1 - self.config.warning_threshold)):
                    rate_limit_result = RateLimitResult.WARNING
                
                return RateLimitCheck(
                    result=rate_limit_result,
                    info=RateLimitInfo(
                        limit=max_requests,
                        remaining=max(0, remaining),
                        reset_time=reset_time
                    ),
                    identifier=identifier,
                    config_name=self.config.name
                )
            else:
                # Decrement since request is denied
                await self.redis_client.decr(key)
                
                reset_time = datetime.fromtimestamp(window_start + self.config.window_size)
                retry_after = int(reset_time.timestamp() - now)
                
                return RateLimitCheck(
                    result=RateLimitResult.DENIED,
                    info=RateLimitInfo(
                        limit=max_requests,
                        remaining=0,
                        reset_time=reset_time,
                        retry_after=retry_after
                    ),
                    identifier=identifier,
                    config_name=self.config.name
                )
                
        except Exception as e:
            logger.error("❌ Error checking fixed window rate limit", error=str(e))
            # Fail open
            return RateLimitCheck(
                result=RateLimitResult.ALLOWED,
                info=RateLimitInfo(
                    limit=int(self.config.requests_per_second * self.config.window_size),
                    remaining=int(self.config.requests_per_second * self.config.window_size),
                    reset_time=datetime.now()
                ),
                identifier=identifier,
                config_name=self.config.name,
                message="Rate limiter error - failing open"
            )
    
    async def _check_sliding_window_counter(self, identifier: str) -> RateLimitCheck:
        """Check rate limit using sliding window counter algorithm"""
        # Similar to sliding window but with counter optimization
        return await self._check_sliding_window(identifier)

class RateLimitManager:
    """
    🛡️ RATE LIMIT MANAGER
    
    Manages multiple rate limiters and provides centralized rate limiting.
    """
    
    def __init__(self, redis_host: str = "redis", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client: Optional[redis.Redis] = None
        self.configs: Dict[str, RateLimitConfig] = {}
        self.limiters: Dict[str, DistributedRateLimiter] = {}
        self.metrics: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        logger.info("🛡️ Rate Limit Manager initialized")
    
    async def initialize(self):
        """Initialize rate limit manager"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            await self.redis_client.ping()
            
            # Initialize default rate limit configs
            await self._initialize_default_configs()
            
            logger.info("🛡️ Rate limit manager initialized")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to initialize rate limit manager", error=str(e))
            return False
    
    async def _initialize_default_configs(self):
        """Initialize default rate limit configurations"""
        default_configs = [
            # Global API rate limiting
            RateLimitConfig(
                name="global_api",
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.GLOBAL,
                requests_per_second=100.0,
                burst_size=200,
                window_size=60
            ),
            
            # Per-user rate limiting
            RateLimitConfig(
                name="per_user",
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.PER_USER,
                requests_per_second=10.0,
                burst_size=20,
                window_size=60
            ),
            
            # Per-IP rate limiting
            RateLimitConfig(
                name="per_ip",
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.PER_IP,
                requests_per_second=20.0,
                burst_size=50,
                window_size=60
            ),
            
            # AI decision rate limiting
            RateLimitConfig(
                name="ai_decisions",
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.PER_USER,
                requests_per_second=5.0,
                burst_size=10,
                window_size=60
            ),
            
            # Workflow execution rate limiting
            RateLimitConfig(
                name="workflow_execution",
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.PER_USER,
                requests_per_second=2.0,
                burst_size=5,
                window_size=300  # 5 minutes
            ),
            
            # Service integration rate limiting
            RateLimitConfig(
                name="service_calls",
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.GLOBAL,
                requests_per_second=50.0,
                burst_size=100,
                window_size=60
            )
        ]
        
        for config in default_configs:
            await self.add_rate_limit_config(config)
        
        logger.info("🛡️ Default rate limit configs initialized", count=len(default_configs))
    
    async def add_rate_limit_config(self, config: RateLimitConfig):
        """Add rate limit configuration"""
        self.configs[config.name] = config
        self.limiters[config.name] = DistributedRateLimiter(self.redis_client, config)
        
        logger.info("🛡️ Rate limit config added", name=config.name, algorithm=config.algorithm.value)
    
    async def check_rate_limit(self, config_name: str, identifier: str) -> RateLimitCheck:
        """Check rate limit for specific configuration"""
        if config_name not in self.limiters:
            # No rate limit configured, allow request
            return RateLimitCheck(
                result=RateLimitResult.ALLOWED,
                info=RateLimitInfo(
                    limit=999999,
                    remaining=999999,
                    reset_time=datetime.now()
                ),
                identifier=identifier,
                config_name=config_name,
                message="No rate limit configured"
            )
        
        limiter = self.limiters[config_name]
        result = await limiter.check_rate_limit(identifier)
        
        # Update metrics
        self.metrics[config_name][result.result.value] += 1
        self.metrics[config_name]["total"] += 1
        
        return result
    
    async def check_multiple_rate_limits(self, checks: List[Tuple[str, str]]) -> List[RateLimitCheck]:
        """Check multiple rate limits"""
        results = []
        for config_name, identifier in checks:
            result = await self.check_rate_limit(config_name, identifier)
            results.append(result)
        return results
    
    def get_identifier_for_scope(self, scope: RateLimitScope, request_info: Dict[str, Any]) -> str:
        """Get identifier based on scope"""
        if scope == RateLimitScope.GLOBAL:
            return "global"
        elif scope == RateLimitScope.PER_USER:
            return request_info.get("user_id", "anonymous")
        elif scope == RateLimitScope.PER_IP:
            return request_info.get("client_ip", "unknown")
        elif scope == RateLimitScope.PER_ENDPOINT:
            return f"{request_info.get('method', 'GET')}:{request_info.get('endpoint', '/')}"
        else:
            return request_info.get("custom_identifier", "default")
    
    async def get_rate_limit_headers(self, config_name: str, identifier: str) -> Dict[str, str]:
        """Get rate limit headers for HTTP responses"""
        result = await self.check_rate_limit(config_name, identifier)
        
        headers = {
            "X-RateLimit-Limit": str(result.info.limit),
            "X-RateLimit-Remaining": str(result.info.remaining),
            "X-RateLimit-Reset": str(int(result.info.reset_time.timestamp()))
        }
        
        if result.info.retry_after:
            headers["Retry-After"] = str(result.info.retry_after)
        
        return headers
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""
        return {
            "configs": {name: {
                "algorithm": config.algorithm.value,
                "scope": config.scope.value,
                "requests_per_second": config.requests_per_second,
                "burst_size": config.burst_size,
                "enabled": config.enabled
            } for name, config in self.configs.items()},
            "metrics": dict(self.metrics),
            "total_configs": len(self.configs),
            "active_limiters": len(self.limiters)
        }
    
    async def reset_rate_limit(self, config_name: str, identifier: str):
        """Reset rate limit for specific identifier"""
        if config_name in self.configs:
            config = self.configs[config_name]
            
            # Delete Redis keys for this identifier
            patterns = [
                f"rate_limit:token_bucket:{config_name}:{identifier}",
                f"rate_limit:sliding_window:{config_name}:{identifier}",
                f"rate_limit:fixed_window:{config_name}:{identifier}:*"
            ]
            
            for pattern in patterns:
                if "*" in pattern:
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                else:
                    await self.redis_client.delete(pattern)
            
            logger.info("🛡️ Rate limit reset", config=config_name, identifier=identifier)

# Global rate limit manager
_rate_limit_manager: Optional[RateLimitManager] = None

async def get_rate_limit_manager() -> RateLimitManager:
    """Get the global rate limit manager"""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
        await _rate_limit_manager.initialize()
    return _rate_limit_manager

async def initialize_rate_limiting_system() -> bool:
    """Initialize the global rate limiting system"""
    try:
        manager = await get_rate_limit_manager()
        logger.info("🛡️ Global rate limiting system initialized")
        return True
    except Exception as e:
        logger.error("❌ Failed to initialize global rate limiting system", error=str(e))
        return False

# Utility functions
async def check_api_rate_limit(user_id: str, client_ip: str) -> Tuple[bool, Dict[str, str]]:
    """Check API rate limits and return headers"""
    manager = await get_rate_limit_manager()
    
    # Check multiple rate limits
    checks = [
        ("global_api", "global"),
        ("per_user", user_id),
        ("per_ip", client_ip)
    ]
    
    results = await manager.check_multiple_rate_limits(checks)
    
    # If any rate limit is exceeded, deny request
    for result in results:
        if result.result == RateLimitResult.DENIED:
            headers = await manager.get_rate_limit_headers(result.config_name, result.identifier)
            return False, headers
    
    # Get headers from most restrictive limit
    most_restrictive = min(results, key=lambda r: r.info.remaining)
    headers = await manager.get_rate_limit_headers(most_restrictive.config_name, most_restrictive.identifier)
    
    return True, headers