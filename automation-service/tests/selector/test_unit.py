"""
Unit tests for Selector v3.

Tests cache key normalization, TTL expiry, LRU eviction, and validation rules.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

import pytest

# Add automation-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from selector.v3 import (
    LRUTTLCache,
    normalize_cache_key,
    validate_k,
    validate_platforms,
    validate_query,
)


class TestCacheKeyNormalization:
    """Test cache key normalization matches v2 behavior."""
    
    def test_basic_normalization(self):
        """Test basic query and platform normalization."""
        key = normalize_cache_key("Windows Networking", 3, ["windows"])
        assert key == ("windows networking", 3, ("windows",))
    
    def test_case_insensitive(self):
        """Test case-insensitive normalization."""
        key1 = normalize_cache_key("LINUX", 5, ["LINUX"])
        key2 = normalize_cache_key("linux", 5, ["linux"])
        assert key1 == key2
    
    def test_whitespace_trimming(self):
        """Test whitespace is trimmed."""
        key = normalize_cache_key("  network scan  ", 3, ["  linux  ", "  windows  "])
        assert key == ("network scan", 3, ("linux", "windows"))
    
    def test_platform_sorting(self):
        """Test platforms are sorted."""
        key1 = normalize_cache_key("test", 3, ["windows", "linux"])
        key2 = normalize_cache_key("test", 3, ["linux", "windows"])
        assert key1 == key2
        assert key1[2] == ("linux", "windows")
    
    def test_empty_platforms(self):
        """Test empty platforms list."""
        key = normalize_cache_key("test", 3, [])
        assert key == ("test", 3, ())
    
    def test_empty_platform_strings_filtered(self):
        """Test empty platform strings are filtered out."""
        key = normalize_cache_key("test", 3, ["linux", "", "  ", "windows"])
        assert key == ("test", 3, ("linux", "windows"))


class TestValidation:
    """Test input validation rules."""
    
    def test_validate_query_empty(self):
        """Test empty query raises 400."""
        with pytest.raises(Exception) as exc_info:
            validate_query("")
        assert exc_info.value.status_code == 400
        assert "QUERY_EMPTY" in str(exc_info.value.detail)
    
    def test_validate_query_whitespace_only(self):
        """Test whitespace-only query raises 400."""
        with pytest.raises(Exception) as exc_info:
            validate_query("   ")
        assert exc_info.value.status_code == 400
    
    def test_validate_query_too_long(self):
        """Test query exceeding 200 chars raises 400."""
        long_query = "a" * 201
        with pytest.raises(Exception) as exc_info:
            validate_query(long_query)
        assert exc_info.value.status_code == 400
        assert "QUERY_TOO_LONG" in str(exc_info.value.detail)
    
    def test_validate_query_valid(self):
        """Test valid query passes."""
        result = validate_query("  network scan  ")
        assert result == "network scan"
    
    def test_validate_platforms_too_many(self):
        """Test more than 5 platforms raises 400."""
        platforms = ["linux", "windows", "macos", "freebsd", "solaris", "aix"]
        with pytest.raises(Exception) as exc_info:
            validate_platforms(platforms)
        assert exc_info.value.status_code == 400
        assert "TOO_MANY_PLATFORMS" in str(exc_info.value.detail)
    
    def test_validate_platforms_invalid_length(self):
        """Test platform with invalid length raises 400."""
        with pytest.raises(Exception) as exc_info:
            validate_platforms(["a" * 33])
        assert exc_info.value.status_code == 400
        assert "INVALID_PLATFORM_LENGTH" in str(exc_info.value.detail)
    
    def test_validate_platforms_valid(self):
        """Test valid platforms pass."""
        result = validate_platforms(["  linux  ", "windows", "", "  "])
        assert result == ["linux", "windows"]
    
    def test_validate_k_out_of_range_low(self):
        """Test k < 1 raises 400."""
        with pytest.raises(Exception) as exc_info:
            validate_k(0)
        assert exc_info.value.status_code == 400
        assert "K_OUT_OF_RANGE" in str(exc_info.value.detail)
    
    def test_validate_k_out_of_range_high(self):
        """Test k > 10 raises 400."""
        with pytest.raises(Exception) as exc_info:
            validate_k(11)
        assert exc_info.value.status_code == 400
    
    def test_validate_k_valid(self):
        """Test valid k values pass."""
        assert validate_k(1) == 1
        assert validate_k(5) == 5
        assert validate_k(10) == 10


@pytest.mark.asyncio
class TestLRUTTLCache:
    """Test LRU+TTL cache behavior."""
    
    async def test_basic_get_put(self):
        """Test basic cache get/put operations."""
        cache = LRUTTLCache(max_entries=10, ttl_sec=60)
        
        key = ("test", 3, ())
        value = {"results": []}
        
        # Put and get
        await cache.put(key, value)
        result = await cache.get(key)
        
        assert result == value
    
    async def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = LRUTTLCache(max_entries=10, ttl_sec=60)
        
        result = await cache.get(("nonexistent", 3, ()))
        assert result is None
    
    async def test_ttl_expiry(self):
        """Test entries expire after TTL."""
        cache = LRUTTLCache(max_entries=10, ttl_sec=1)
        
        key = ("test", 3, ())
        value = {"results": []}
        
        await cache.put(key, value)
        
        # Should be available immediately
        result = await cache.get(key)
        assert result == value
        
        # Wait for expiry
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await cache.get(key)
        assert result is None
    
    async def test_lru_evicts_oldest(self):
        """Test LRU evicts oldest entry when cache is full."""
        cache = LRUTTLCache(max_entries=3, ttl_sec=60)
        
        # Fill cache
        await cache.put(("key1", 3, ()), {"id": 1})
        await cache.put(("key2", 3, ()), {"id": 2})
        await cache.put(("key3", 3, ()), {"id": 3})
        
        # All should be present
        assert await cache.get(("key1", 3, ())) == {"id": 1}
        assert await cache.get(("key2", 3, ())) == {"id": 2}
        assert await cache.get(("key3", 3, ())) == {"id": 3}
        
        # Add one more - should evict key1 (oldest)
        await cache.put(("key4", 3, ()), {"id": 4})
        
        # key1 should be evicted
        assert await cache.get(("key1", 3, ())) is None
        
        # Others should still be present
        assert await cache.get(("key2", 3, ())) == {"id": 2}
        assert await cache.get(("key3", 3, ())) == {"id": 3}
        assert await cache.get(("key4", 3, ())) == {"id": 4}
    
    async def test_lru_updates_on_access(self):
        """Test accessing an entry moves it to end (most recent)."""
        cache = LRUTTLCache(max_entries=3, ttl_sec=60)
        
        # Fill cache
        await cache.put(("key1", 3, ()), {"id": 1})
        await cache.put(("key2", 3, ()), {"id": 2})
        await cache.put(("key3", 3, ()), {"id": 3})
        
        # Access key1 to make it most recent
        await cache.get(("key1", 3, ()))
        
        # Add one more - should evict key2 (now oldest)
        await cache.put(("key4", 3, ()), {"id": 4})
        
        # key2 should be evicted
        assert await cache.get(("key2", 3, ())) is None
        
        # key1 should still be present (was accessed)
        assert await cache.get(("key1", 3, ())) == {"id": 1}
    
    async def test_update_existing_key(self):
        """Test updating existing key refreshes TTL and value."""
        cache = LRUTTLCache(max_entries=10, ttl_sec=1)
        
        key = ("test", 3, ())
        
        # Put initial value
        await cache.put(key, {"version": 1})
        
        # Wait a bit
        await asyncio.sleep(0.5)
        
        # Update value (should refresh TTL)
        await cache.put(key, {"version": 2})
        
        # Wait past original TTL
        await asyncio.sleep(0.6)
        
        # Should still be available (TTL was refreshed)
        result = await cache.get(key)
        assert result == {"version": 2}
    
    async def test_concurrent_access(self):
        """Test cache is safe for concurrent access."""
        cache = LRUTTLCache(max_entries=100, ttl_sec=60)
        
        async def worker(worker_id: int):
            for i in range(10):
                key = (f"worker{worker_id}", i, ())
                value = {"worker": worker_id, "iteration": i}
                await cache.put(key, value)
                result = await cache.get(key)
                assert result == value
        
        # Run multiple workers concurrently
        await asyncio.gather(*[worker(i) for i in range(10)])
        
        # Verify cache size
        size = await cache.size()
        assert size == 100  # 10 workers * 10 iterations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])