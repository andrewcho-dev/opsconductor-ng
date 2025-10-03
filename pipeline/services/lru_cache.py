"""
LRU Cache Implementation for Tool Catalog
Provides memory-bounded caching with automatic eviction
"""

import threading
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) cache with TTL support
    
    Features:
    - Automatic eviction of least recently used items when max_size is reached
    - Time-to-live (TTL) support for cache entries
    - Thread-safe operations
    - Memory-bounded (prevents unbounded growth)
    - O(1) get/set operations
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds (0 = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # OrderedDict maintains insertion order and provides O(1) move_to_end
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._timestamps: Dict[str, datetime] = {}
        self._ttls: Dict[str, int] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0
        
        logger.info(f"LRUCache initialized: max_size={max_size}, default_ttl={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            # Check if key exists
            if key not in self._cache:
                self._misses += 1
                return None
            
            # Check if expired
            if self._is_expired(key):
                self._remove(key)
                self._expirations += 1
                self._misses += 1
                return None
            
            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        with self._lock:
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = value
                self._cache.move_to_end(key)
                self._timestamps[key] = datetime.now()
                self._ttls[key] = ttl if ttl is not None else self.default_ttl
                return
            
            # Check if we need to evict
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Add new entry
            self._cache[key] = value
            self._timestamps[key] = datetime.now()
            self._ttls[key] = ttl if ttl is not None else self.default_ttl
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._ttls.clear()
            logger.info("Cache cleared")
    
    def clear_pattern(self, pattern: str):
        """
        Clear cache entries matching pattern
        
        Args:
            pattern: String pattern to match in keys
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._remove(key)
            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching '{pattern}'")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [k for k in self._cache.keys() if self._is_expired(k)]
            for key in expired_keys:
                self._remove(key)
                self._expirations += 1
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
                "evictions": self._evictions,
                "expirations": self._expirations,
                "total_requests": total_requests
            }
    
    def reset_stats(self):
        """Reset cache statistics"""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0
    
    # Private methods
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self._timestamps:
            return True
        
        ttl = self._ttls.get(key, self.default_ttl)
        if ttl == 0:  # No expiration
            return False
        
        age = datetime.now() - self._timestamps[key]
        return age.total_seconds() >= ttl
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self._cache:
            return
        
        # OrderedDict maintains order, first item is LRU
        lru_key = next(iter(self._cache))
        self._remove(lru_key)
        self._evictions += 1
        logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    def _remove(self, key: str):
        """Remove key from all cache structures"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._ttls.pop(key, None)
    
    def __len__(self) -> int:
        """Return number of items in cache"""
        with self._lock:
            return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (doesn't check expiration)"""
        with self._lock:
            return key in self._cache
    
    def __repr__(self) -> str:
        """String representation"""
        stats = self.get_stats()
        return (f"LRUCache(size={stats['size']}/{stats['max_size']}, "
                f"hit_rate={stats['hit_rate']}%, "
                f"hits={stats['hits']}, misses={stats['misses']})")


# Global cache instance for tool catalog
_tool_cache: Optional[LRUCache] = None


def get_tool_cache(max_size: int = 1000, default_ttl: int = 300) -> LRUCache:
    """
    Get or create global tool cache instance
    
    Args:
        max_size: Maximum cache size (only used on first call)
        default_ttl: Default TTL in seconds (only used on first call)
        
    Returns:
        LRUCache instance
    """
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = LRUCache(max_size=max_size, default_ttl=default_ttl)
    return _tool_cache