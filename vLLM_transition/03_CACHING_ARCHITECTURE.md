# Caching Architecture Guide

## 🎯 Goal
Achieve 99% latency reduction for repeated queries through intelligent caching, targeting 0.1-0.5 second response times.

## 📊 Caching Opportunity Analysis

### Query Pattern Analysis

Based on typical infrastructure operations, we expect:

| Query Type | Frequency | Cacheable | Cache TTL |
|------------|-----------|-----------|-----------|
| "List all servers" | 15% | ✅ Yes | 5 min |
| "Show production assets" | 12% | ✅ Yes | 5 min |
| "Status of [specific asset]" | 20% | ✅ Yes | 1 min |
| "Show logs for [asset]" | 10% | ❌ No | - |
| "Restart [service]" | 8% | ❌ No | - |
| "What is [asset] doing?" | 10% | ⚠️ Partial | 30 sec |
| Other queries | 25% | ⚠️ Varies | Varies |

**Estimated cache hit rate:** 30-50% (conservative estimate)

### Performance Impact

| Scenario | Current (Optimized) | With Cache | Improvement |
|----------|---------------------|------------|-------------|
| Cache hit | 3-5s | 0.1s | 97-98% faster |
| Cache miss | 3-5s | 3-5s | No change |
| **Average (40% hit rate)** | **3-5s** | **2-3s** | **33-40% faster** |

**Key insight:** Even with modest 40% hit rate, average latency improves significantly.

## 🏗️ Caching Architecture

### Three-Layer Caching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Intent Cache (Redis)                              │
│  - Caches: Intent classification + entity extraction        │
│  - TTL: 1 hour                                               │
│  - Hit rate: 30-40%                                          │
│  - Savings: Skip 2 LLM calls (2-3 seconds)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Asset Context Cache (Redis + In-Memory)           │
│  - Caches: Asset metadata from database                     │
│  - TTL: 5 minutes                                            │
│  - Hit rate: 60-80%                                          │
│  - Savings: Skip database queries (0.5-1 second)            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Tool Result Cache (Redis)                         │
│  - Caches: Tool execution results (read-only ops)           │
│  - TTL: 30 seconds - 5 minutes (varies by tool)             │
│  - Hit rate: 20-30%                                          │
│  - Savings: Skip tool execution (1-10 seconds)              │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Layer 1: Intent Cache

### Purpose
Cache intent classification and entity extraction results to skip LLM calls for repeated queries.

### Implementation

#### Redis Schema

```
Key: intent:{query_hash}
Value: {
  "intent": "ASSET_DISCOVERY",
  "entities": {"asset_types": ["server"], "environments": ["production"]},
  "confidence": 0.95,
  "risk": "LOW",
  "timestamp": 1234567890
}
TTL: 3600 seconds (1 hour)
```

#### Code Implementation

**File:** `pipeline/stages/stage_a/intent_cache.py` (new file)

```python
import redis
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime

class IntentCache:
    """
    Redis-backed cache for intent classification results
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = 3600  # 1 hour
        self.hit_count = 0
        self.miss_count = 0
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for better cache hits
        
        Examples:
          "List all servers" → "list all servers"
          "Show  me   servers" → "show me servers"
        """
        query = query.lower().strip()
        query = ' '.join(query.split())  # Collapse whitespace
        return query
    
    def _hash_query(self, query: str) -> str:
        """Generate cache key from query"""
        normalized = self._normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached intent classification result
        
        Returns:
            Cached result or None if not found
        """
        key = f"intent:{self._hash_query(query)}"
        
        try:
            cached = self.redis.get(key)
            if cached:
                self.hit_count += 1
                result = json.loads(cached)
                return result
            else:
                self.miss_count += 1
                return None
        except Exception as e:
            print(f"Cache get error: {e}")
            self.miss_count += 1
            return None
    
    def set(self, query: str, result: Dict[str, Any]):
        """
        Cache intent classification result
        
        Args:
            query: User query
            result: Classification result with intent, entities, confidence, risk
        """
        key = f"intent:{self._hash_query(query)}"
        
        try:
            # Add timestamp
            result["timestamp"] = datetime.now().timestamp()
            
            # Cache with TTL
            self.redis.setex(
                key,
                self.ttl,
                json.dumps(result)
            )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def invalidate(self, query: str):
        """Invalidate cached result for specific query"""
        key = f"intent:{self._hash_query(query)}"
        self.redis.delete(key)
    
    def clear_all(self):
        """Clear all intent cache entries"""
        for key in self.redis.scan_iter("intent:*"):
            self.redis.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total if total > 0 else 0
        
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "total": total,
            "hit_rate": hit_rate,
            "size": self.redis.dbsize()
        }
```

#### Integration with Stage A

**File:** `pipeline/stages/stage_a/classifier.py`

```python
from pipeline.stages.stage_a.intent_cache import IntentCache

class IntentClassifier:
    def __init__(self, config: Dict[str, Any]):
        self.llm_client = LLMClient(config)
        self.cache = IntentCache()  # Add cache
    
    async def classify(self, query: str) -> Dict[str, Any]:
        """
        Classify user intent with caching
        """
        # Check cache first
        cached = self.cache.get(query)
        if cached:
            self.logger.info(f"Intent cache HIT for query: {query[:50]}...")
            return cached
        
        self.logger.info(f"Intent cache MISS for query: {query[:50]}...")
        
        # Cache miss - perform classification
        result = await self._classify_uncached(query)
        
        # Cache result
        self.cache.set(query, result)
        
        return result
    
    async def _classify_uncached(self, query: str) -> Dict[str, Any]:
        """Original classification logic (without cache)"""
        # ... existing classification code ...
```

### Cache Warming

Pre-populate cache with common queries on startup:

**File:** `pipeline/stages/stage_a/cache_warmer.py` (new file)

```python
class CacheWarmer:
    """Pre-populate intent cache with common queries"""
    
    COMMON_QUERIES = [
        "list all servers",
        "show production assets",
        "list databases",
        "show all applications",
        "list servers in production",
        "show staging servers",
        "list all assets",
        "show infrastructure",
        "list virtual machines",
        "show containers"
    ]
    
    def __init__(self, classifier: IntentClassifier):
        self.classifier = classifier
    
    async def warm_cache(self):
        """Warm cache with common queries"""
        print("Warming intent cache...")
        
        for query in self.COMMON_QUERIES:
            try:
                await self.classifier.classify(query)
                print(f"  ✓ Cached: {query}")
            except Exception as e:
                print(f"  ✗ Failed: {query} ({e})")
        
        print(f"Cache warming complete. Stats: {self.classifier.cache.get_stats()}")
```

## 🔧 Layer 2: Enhanced Asset Context Cache

### Current State

**File:** `pipeline/integration/asset_service_context.py`

Currently has basic in-memory caching with 60-second TTL:

```python
class AssetServiceContext:
    def __init__(self):
        self._cache = {}
        self.cache_ttl = 60  # seconds
```

### Enhancement Strategy

1. **Increase TTL:** 60s → 300s (5 minutes)
2. **Add Redis backing:** Persist across requests
3. **Add cache warming:** Pre-load frequently accessed assets

### Implementation

**File:** `pipeline/integration/asset_service_context.py`

```python
import redis
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

class AssetServiceContext:
    """
    Enhanced asset context cache with Redis backing
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        # In-memory cache (L1)
        self._memory_cache = {}
        self.memory_ttl = 60  # 1 minute
        
        # Redis cache (L2)
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.redis_ttl = 300  # 5 minutes
        
        # Statistics
        self.memory_hits = 0
        self.redis_hits = 0
        self.misses = 0
    
    def get_asset_context(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get asset context with two-level caching
        
        L1: In-memory cache (60s TTL, fastest)
        L2: Redis cache (300s TTL, fast)
        L3: Database query (slowest)
        """
        # Check L1 (memory)
        if asset_id in self._memory_cache:
            cached, timestamp = self._memory_cache[asset_id]
            if datetime.now() - timestamp < timedelta(seconds=self.memory_ttl):
                self.memory_hits += 1
                return cached
        
        # Check L2 (Redis)
        redis_key = f"asset:{asset_id}"
        try:
            cached = self.redis.get(redis_key)
            if cached:
                self.redis_hits += 1
                result = json.loads(cached)
                
                # Populate L1
                self._memory_cache[asset_id] = (result, datetime.now())
                
                return result
        except Exception as e:
            print(f"Redis cache error: {e}")
        
        # Cache miss - query database
        self.misses += 1
        result = self._query_asset_database(asset_id)
        
        if result:
            # Cache in both layers
            self._memory_cache[asset_id] = (result, datetime.now())
            try:
                self.redis.setex(redis_key, self.redis_ttl, json.dumps(result))
            except Exception as e:
                print(f"Redis cache set error: {e}")
        
        return result
    
    def get_assets_by_filter(
        self,
        asset_type: Optional[str] = None,
        environment: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get multiple assets with caching
        """
        # Generate cache key from filter
        filter_key = f"filter:{asset_type}:{environment}:{','.join(tags or [])}"
        redis_key = f"assets:{hashlib.md5(filter_key.encode()).hexdigest()}"
        
        # Check Redis cache
        try:
            cached = self.redis.get(redis_key)
            if cached:
                self.redis_hits += 1
                return json.loads(cached)
        except Exception as e:
            print(f"Redis cache error: {e}")
        
        # Cache miss - query database
        self.misses += 1
        results = self._query_assets_by_filter(asset_type, environment, tags)
        
        # Cache results (shorter TTL for list queries)
        try:
            self.redis.setex(redis_key, 60, json.dumps(results))
        except Exception as e:
            print(f"Redis cache set error: {e}")
        
        return results
    
    def invalidate_asset(self, asset_id: str):
        """Invalidate cached asset context"""
        # Clear L1
        if asset_id in self._memory_cache:
            del self._memory_cache[asset_id]
        
        # Clear L2
        redis_key = f"asset:{asset_id}"
        self.redis.delete(redis_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.memory_hits + self.redis_hits + self.misses
        hit_rate = (self.memory_hits + self.redis_hits) / total if total > 0 else 0
        
        return {
            "memory_hits": self.memory_hits,
            "redis_hits": self.redis_hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
            "memory_size": len(self._memory_cache),
            "redis_size": self.redis.dbsize()
        }
```

## 🔧 Layer 3: Tool Result Cache

### Purpose
Cache results of read-only tool executions (e.g., "list servers", "get status").

### Implementation

**File:** `pipeline/stages/stage_c/tool_result_cache.py` (new file)

```python
import redis
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime

class ToolResultCache:
    """
    Cache results of read-only tool executions
    """
    
    # Tool-specific TTLs
    TTL_CONFIG = {
        "list_assets": 300,          # 5 minutes
        "get_asset_status": 60,      # 1 minute
        "get_asset_details": 120,    # 2 minutes
        "list_servers": 300,         # 5 minutes
        "get_health_status": 30,     # 30 seconds
        "get_metrics": 60,           # 1 minute
        "default": 120               # 2 minutes
    }
    
    # Tools that should NOT be cached (write operations)
    UNCACHEABLE_TOOLS = {
        "restart_service",
        "deploy_application",
        "update_configuration",
        "delete_asset",
        "execute_command",
        "run_script"
    }
    
    def __init__(self, redis_url: str = "redis://localhost:6379/2"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key from tool name and parameters"""
        # Sort parameters for consistent hashing
        param_str = json.dumps(parameters, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"tool:{tool_name}:{param_hash}"
    
    def is_cacheable(self, tool_name: str) -> bool:
        """Check if tool results can be cached"""
        return tool_name not in self.UNCACHEABLE_TOOLS
    
    def get(self, tool_name: str, parameters: Dict[str, Any]) -> Optional[Any]:
        """Get cached tool result"""
        if not self.is_cacheable(tool_name):
            return None
        
        key = self._generate_cache_key(tool_name, parameters)
        
        try:
            cached = self.redis.get(key)
            if cached:
                self.hit_count += 1
                return json.loads(cached)
            else:
                self.miss_count += 1
                return None
        except Exception as e:
            print(f"Tool cache get error: {e}")
            self.miss_count += 1
            return None
    
    def set(self, tool_name: str, parameters: Dict[str, Any], result: Any):
        """Cache tool result"""
        if not self.is_cacheable(tool_name):
            return
        
        key = self._generate_cache_key(tool_name, parameters)
        ttl = self.TTL_CONFIG.get(tool_name, self.TTL_CONFIG["default"])
        
        try:
            self.redis.setex(key, ttl, json.dumps(result))
        except Exception as e:
            print(f"Tool cache set error: {e}")
    
    def invalidate_tool(self, tool_name: str):
        """Invalidate all cached results for a specific tool"""
        pattern = f"tool:{tool_name}:*"
        for key in self.redis.scan_iter(pattern):
            self.redis.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total if total > 0 else 0
        
        return {
            "hits": self.hit_count,
            "misses": self.miss_count,
            "total": total,
            "hit_rate": hit_rate,
            "size": self.redis.dbsize()
        }
```

#### Integration with Stage C

**File:** `pipeline/stages/stage_c/executor.py`

```python
from pipeline.stages.stage_c.tool_result_cache import ToolResultCache

class ToolExecutor:
    def __init__(self, config: Dict[str, Any]):
        self.tools = self._load_tools(config)
        self.cache = ToolResultCache()  # Add cache
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        Execute tool with caching
        """
        # Check cache first
        cached = self.cache.get(tool_name, parameters)
        if cached is not None:
            self.logger.info(f"Tool cache HIT: {tool_name}")
            return cached
        
        self.logger.info(f"Tool cache MISS: {tool_name}")
        
        # Cache miss - execute tool
        result = await self._execute_tool_uncached(tool_name, parameters)
        
        # Cache result
        self.cache.set(tool_name, parameters, result)
        
        return result
```

## 🔧 Redis Setup

### Installation

```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify installation
redis-cli ping
# Expected output: PONG
```

### Configuration

**File:** `/etc/redis/redis.conf`

```conf
# Memory limit (adjust based on available RAM)
maxmemory 2gb

# Eviction policy (remove least recently used keys when memory limit reached)
maxmemory-policy allkeys-lru

# Persistence (optional - disable for pure cache)
save ""
appendonly no

# Network
bind 127.0.0.1
port 6379

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

Restart Redis:
```bash
sudo systemctl restart redis-server
```

### Python Client

```bash
pip install redis
```

## 📊 Cache Invalidation Strategy

### When to Invalidate

| Event | Invalidate |
|-------|-----------|
| Asset created | Asset context cache for that asset |
| Asset updated | Asset context cache for that asset |
| Asset deleted | Asset context cache for that asset + list caches |
| Configuration changed | Tool result cache for affected tools |
| Manual refresh requested | All caches |

### Implementation

**File:** `pipeline/integration/cache_manager.py` (new file)

```python
class CacheManager:
    """
    Centralized cache management
    """
    
    def __init__(self):
        self.intent_cache = IntentCache()
        self.asset_cache = AssetServiceContext()
        self.tool_cache = ToolResultCache()
    
    def invalidate_asset(self, asset_id: str):
        """Invalidate all caches related to an asset"""
        self.asset_cache.invalidate_asset(asset_id)
        self.tool_cache.invalidate_tool("get_asset_status")
        self.tool_cache.invalidate_tool("get_asset_details")
    
    def invalidate_all(self):
        """Invalidate all caches (nuclear option)"""
        self.intent_cache.clear_all()
        self.asset_cache.redis.flushdb()
        self.tool_cache.redis.flushdb()
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get statistics from all cache layers"""
        return {
            "intent_cache": self.intent_cache.get_stats(),
            "asset_cache": self.asset_cache.get_stats(),
            "tool_cache": self.tool_cache.get_stats()
        }
```

## 📊 Monitoring & Metrics

### Cache Dashboard

**File:** `pipeline/monitoring/cache_dashboard.py` (new file)

```python
from flask import Flask, jsonify
from pipeline.integration.cache_manager import CacheManager

app = Flask(__name__)
cache_manager = CacheManager()

@app.route("/cache/stats")
def cache_stats():
    """Get cache statistics"""
    return jsonify(cache_manager.get_global_stats())

@app.route("/cache/invalidate/<asset_id>", methods=["POST"])
def invalidate_asset(asset_id: str):
    """Invalidate caches for specific asset"""
    cache_manager.invalidate_asset(asset_id)
    return jsonify({"status": "ok", "invalidated": asset_id})

@app.route("/cache/clear", methods=["POST"])
def clear_all():
    """Clear all caches"""
    cache_manager.invalidate_all()
    return jsonify({"status": "ok", "message": "All caches cleared"})

if __name__ == "__main__":
    app.run(port=5001)
```

Run dashboard:
```bash
python pipeline/monitoring/cache_dashboard.py
```

Access:
```bash
# Get stats
curl http://localhost:5001/cache/stats

# Invalidate asset
curl -X POST http://localhost:5001/cache/invalidate/web-server-01

# Clear all
curl -X POST http://localhost:5001/cache/clear
```

## 📊 Expected Results

### Performance Improvement

| Scenario | Before Caching | After Caching | Improvement |
|----------|----------------|---------------|-------------|
| **Cache hit (intent)** | 3-5s | 0.5-1s | 80-90% faster |
| **Cache hit (full pipeline)** | 25s | 5s | 80% faster |
| **Cache miss** | 3-5s | 3-5s | No change |
| **Average (40% hit rate)** | 3-5s | 2-3s | 33-40% faster |

### Cache Hit Rates (Projected)

| Cache Layer | Expected Hit Rate | Savings per Hit |
|-------------|-------------------|-----------------|
| Intent Cache | 30-40% | 2-3 seconds |
| Asset Context Cache | 60-80% | 0.5-1 second |
| Tool Result Cache | 20-30% | 1-10 seconds |

### Cost Reduction

- **LLM API calls:** 30-40% reduction (intent cache)
- **Database queries:** 60-80% reduction (asset cache)
- **Tool executions:** 20-30% reduction (tool cache)

## ✅ Implementation Checklist

### Phase 3.1: Redis Setup
- [ ] Install Redis server
- [ ] Configure Redis (memory limit, eviction policy)
- [ ] Install Python redis client
- [ ] Test Redis connection

### Phase 3.2: Intent Cache
- [ ] Create `intent_cache.py`
- [ ] Integrate with `classifier.py`
- [ ] Implement query normalization
- [ ] Create cache warmer
- [ ] Test cache hit/miss scenarios

### Phase 3.3: Enhanced Asset Cache
- [ ] Update `asset_service_context.py`
- [ ] Implement two-level caching (memory + Redis)
- [ ] Increase TTL to 5 minutes
- [ ] Test cache performance

### Phase 3.4: Tool Result Cache
- [ ] Create `tool_result_cache.py`
- [ ] Integrate with `executor.py`
- [ ] Configure tool-specific TTLs
- [ ] Test cacheable vs uncacheable tools

### Phase 3.5: Cache Management
- [ ] Create `cache_manager.py`
- [ ] Implement invalidation logic
- [ ] Create cache dashboard
- [ ] Test invalidation scenarios

### Phase 3.6: Monitoring
- [ ] Set up cache statistics collection
- [ ] Create monitoring dashboard
- [ ] Track hit rates over time
- [ ] Optimize TTLs based on real data

## 🎯 Next Steps

After implementing caching:

1. **Monitor cache hit rates** for 1 week
2. **Tune TTLs** based on actual usage patterns
3. **Optimize cache warming** for common queries
4. **Document final performance** in `04_PERFORMANCE_TRANSFORMATION_SUMMARY.md`

---

**Status:** Ready for Implementation  
**Estimated Time:** 6-8 hours  
**Risk Level:** Low (caching is additive, doesn't break existing functionality)  
**Next Document:** `04_PERFORMANCE_TRANSFORMATION_SUMMARY.md`