"""
Cache Manager for OpsConductor Pipeline

Provides intelligent caching with Redis backend for Stage A, B, and C.
Implements graceful degradation - cache failures never break the pipeline.
"""

import json
import logging
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Intelligent caching manager for OpsConductor pipeline stages.
    
    Features:
    - Redis-backed in-memory caching
    - Automatic TTL management
    - Graceful degradation on failures
    - Cache statistics tracking
    - Pattern-based invalidation
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", enabled: bool = True):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            enabled: Whether caching is enabled (default: True)
        """
        self.enabled = enabled
        self.redis_url = redis_url
        self.redis_client = None
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0,
            "errors": 0
        }
        
        # Initialize Redis connection
        if self.enabled:
            self._connect()
    
    def _connect(self) -> None:
        """Establish Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Cache Manager connected to Redis: {self.redis_url}")
        except RedisError as e:
            logger.warning(f"⚠️ Cache Manager: Redis connection failed: {e}")
            logger.warning("⚠️ Cache Manager: Running without cache (graceful degradation)")
            self.redis_client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """
        Generate cache key from prefix and data.
        
        Args:
            prefix: Key prefix (e.g., "stage_a", "stage_c")
            data: Data to hash for key generation
            
        Returns:
            Cache key string
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        hash_value = hashlib.sha256(sorted_data.encode()).hexdigest()[:16]
        return f"opsconductor:{prefix}:{hash_value}"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/error
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                self.stats["hits"] += 1
                logger.debug(f"✅ Cache HIT: {key}")
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                logger.debug(f"❌ Cache MISS: {key}")
                return None
        except (RedisError, json.JSONDecodeError) as e:
            self.stats["errors"] += 1
            logger.warning(f"⚠️ Cache GET error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            self.stats["sets"] += 1
            logger.debug(f"✅ Cache SET: {key} (TTL: {ttl}s)")
            return True
        except (RedisError, TypeError, ValueError) as e:
            self.stats["errors"] += 1
            logger.warning(f"⚠️ Cache SET error for {key}: {e}")
            return False
    
    def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "stage_a:*", "*")
            
        Returns:
            Number of keys invalidated
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            # Add prefix if not present
            if not pattern.startswith("opsconductor:"):
                pattern = f"opsconductor:{pattern}"
            
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                self.stats["invalidations"] += count
                logger.info(f"✅ Cache INVALIDATE: {count} keys matching {pattern}")
                return count
            return 0
        except RedisError as e:
            self.stats["errors"] += 1
            logger.warning(f"⚠️ Cache INVALIDATE error for {pattern}: {e}")
            return 0
    
    def invalidate_all(self) -> int:
        """
        Invalidate all OpsConductor cache entries.
        
        Returns:
            Number of keys invalidated
        """
        return self.invalidate("opsconductor:*")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            "enabled": self.enabled,
            "connected": self.redis_client is not None,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "invalidations": self.stats["invalidations"],
            "errors": self.stats["errors"],
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 1)
        }
    
    def get_redis_info(self) -> Dict[str, Any]:
        """
        Get Redis server information.
        
        Returns:
            Dictionary with Redis stats or empty dict if not connected
        """
        if not self.enabled or not self.redis_client:
            return {}
        
        try:
            info = self.redis_client.info("stats")
            memory = self.redis_client.info("memory")
            return {
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "used_memory_human": memory.get("used_memory_human", "0B"),
                "maxmemory_human": memory.get("maxmemory_human", "0B")
            }
        except RedisError as e:
            logger.warning(f"⚠️ Cache: Failed to get Redis info: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check cache health status.
        
        Returns:
            Health status dictionary
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Caching is disabled"
            }
        
        if not self.redis_client:
            return {
                "status": "unhealthy",
                "message": "Redis connection failed"
            }
        
        try:
            self.redis_client.ping()
            return {
                "status": "healthy",
                "message": "Cache is operational"
            }
        except RedisError as e:
            return {
                "status": "unhealthy",
                "message": f"Redis ping failed: {e}"
            }
    
    def generate_stage_a_key(self, user_request: str) -> str:
        """
        Generate cache key for Stage A (Intent + Entities + Confidence + Risk).
        
        Args:
            user_request: User's natural language request
            
        Returns:
            Cache key string
        """
        return self._generate_key("stage_a", {"request": user_request.strip().lower()})
    
    def generate_stage_b_key(self, capabilities: list, context: Dict[str, Any]) -> str:
        """
        Generate cache key for Stage B (Tool Selection).
        
        Args:
            capabilities: Required capabilities list
            context: Selection context
            
        Returns:
            Cache key string
        """
        return self._generate_key("stage_b", {
            "capabilities": sorted(capabilities),
            "risk": context.get("risk_level", "unknown")
        })
    
    def generate_stage_c_key(self, action: str, entities: list, tools: list) -> str:
        """
        Generate cache key for Stage C (Planning).
        
        Args:
            action: Intent action
            entities: Extracted entities
            tools: Selected tools
            
        Returns:
            Cache key string
        """
        return self._generate_key("stage_c", {
            "action": action,
            "entities": sorted([f"{e.get('type', '')}:{e.get('value', '')}" for e in entities]),
            "tools": sorted(tools)
        })