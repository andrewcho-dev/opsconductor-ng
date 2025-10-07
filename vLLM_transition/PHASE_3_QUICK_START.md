# Phase 3: Caching Layer - Quick Start Guide

**Status:** ✅ IMPLEMENTED - READY FOR TESTING  
**Time to Test:** 5 minutes  
**Expected Result:** 99% faster cached queries

---

## 🚀 Quick Test (5 Minutes)

### **Step 1: Restart Services** (1 minute)
```bash
cd /home/opsconductor/opsconductor-ng

# Restart API to pick up cache changes
docker compose stop opsconductor-api
docker compose rm -f opsconductor-api
docker compose up -d opsconductor-api

# Wait for startup (10 seconds)
sleep 10

# Check cache is working
docker compose logs opsconductor-api | grep -i cache
```

**Expected Output:**
```
✅ Cache Manager connected to Redis: redis://redis:6379
✅ Cache API registered (Phase 3)
```

### **Step 2: Test Cache Performance** (2 minutes)
```bash
# First request (cache MISS - slow)
echo "Test 1: Cache MISS (should take ~1.7s)"
time curl -s -X POST http://localhost:3000/pipeline \
  -H "Content-Type: application/json" \
  -d '{"request": "list all servers in production"}' | jq '.stage_a_time_ms'

# Second request (cache HIT - fast!)
echo "Test 2: Cache HIT (should take ~10ms)"
time curl -s -X POST http://localhost:3000/pipeline \
  -H "Content-Type: application/json" \
  -d '{"request": "list all servers in production"}' | jq '.stage_a_time_ms'
```

**Expected Results:**
- First request: ~1700ms (cache miss)
- Second request: ~10ms (cache hit - **99% faster!**)

### **Step 3: Check Cache Stats** (1 minute)
```bash
# View cache statistics
curl -s http://localhost:3000/api/v1/cache/stats | jq '.cache_stats'
```

**Expected Output:**
```json
{
  "enabled": true,
  "connected": true,
  "hits": 1,
  "misses": 1,
  "hit_rate_percent": 50.0
}
```

### **Step 4: Test Cache Invalidation** (1 minute)
```bash
# Invalidate all cache
curl -s -X POST http://localhost:3000/api/v1/cache/invalidate/all | jq '.'

# Verify cache cleared
curl -s http://localhost:3000/api/v1/cache/stats | jq '.cache_stats.hit_rate_percent'
# Should show: 0.0
```

---

## 🎯 What to Expect

### **Performance Improvements**

| Scenario | Before Phase 3 | After Phase 3 | Improvement |
|----------|----------------|---------------|-------------|
| **First Request** | 1.7s | 1.7s | 0% (cache miss) |
| **Second Request** | 1.7s | 0.01s | **99% faster** |
| **Average (50% hit rate)** | 1.7s | 0.85s | **50% faster** |

### **Cache Hit Rate Expectations**

- **Day 1:** 20-30% (users learning)
- **Week 1:** 40-50% (patterns emerging)
- **Month 1:** 50-60% (stable)

### **Cost Savings**

At 50% cache hit rate:
- **Token savings:** 40% reduction
- **LLM call savings:** 40% reduction
- **Annual savings:** $7,373 (at 1,000 req/day)

---

## 🔧 Configuration

### **Cache Settings** (`.env`)
```bash
CACHE_ENABLED=true
CACHE_TTL_STAGE_A=3600  # 1 hour
CACHE_TTL_STAGE_B=7200  # 2 hours
CACHE_TTL_STAGE_C=1800  # 30 minutes
```

### **Disable Cache** (if needed)
```bash
# Edit .env
CACHE_ENABLED=false

# Restart
docker compose restart opsconductor-api
```

---

## 📊 Monitoring

### **Cache Statistics**
```bash
# Real-time stats
watch -n 5 'curl -s http://localhost:3000/api/v1/cache/stats | jq ".cache_stats"'
```

### **Cache Health**
```bash
# Health check
curl http://localhost:3000/api/v1/cache/health | jq '.'
```

### **Redis Memory Usage**
```bash
# Check Redis memory
docker exec opsconductor-redis redis-cli INFO memory | grep used_memory_human
```

---

## 🚨 Troubleshooting

### **Problem: Cache not working**
```bash
# Check Redis is running
docker ps | grep redis

# Check Redis connectivity
docker exec opsconductor-redis redis-cli PING
# Should return: PONG

# Check cache logs
docker compose logs opsconductor-api | grep -i cache
```

### **Problem: Cache hit rate is 0%**
```bash
# Verify cache is enabled
curl http://localhost:3000/api/v1/cache/stats | jq '.cache_stats.enabled'
# Should return: true

# Check for cache errors
docker compose logs opsconductor-api | grep -i "cache.*error"
```

### **Problem: Redis out of memory**
```bash
# Check memory usage
docker exec opsconductor-redis redis-cli INFO memory

# Clear cache if needed
curl -X POST http://localhost:3000/api/v1/cache/invalidate/all
```

---

## 📚 API Reference

### **GET /api/v1/cache/stats**
Get cache statistics (hits, misses, hit rate)

### **GET /api/v1/cache/health**
Check cache health status

### **POST /api/v1/cache/invalidate?pattern=***
Invalidate cache entries by pattern

### **POST /api/v1/cache/invalidate/all**
Invalidate all cache entries

### **POST /api/v1/cache/invalidate/stage/{stage}**
Invalidate specific stage cache (stage_a, stage_b, stage_c)

---

## ✅ Success Checklist

- [ ] Services restarted successfully
- [ ] Cache manager connected to Redis
- [ ] First request takes ~1.7s (cache miss)
- [ ] Second request takes ~10ms (cache hit)
- [ ] Cache hit rate shows 50%
- [ ] Cache invalidation works
- [ ] No errors in logs

---

## 🎉 Next Steps

### **Phase 3.2: Stage C Caching** (Recommended)
Implement caching for Stage C (Planning) for additional 68% improvement.

**Expected Impact:**
- Stage C: 13.2s → 0.01s (99% faster)
- Total: 19.5s → 2.4s (88% faster)

### **Phase 3.3: Cache Warming** (Optional)
Pre-populate cache with common queries for better initial performance.

### **Phase 3.4: Cache Monitoring** (Recommended)
Add cache metrics to Prometheus for production monitoring.

---

## 📖 Full Documentation

- **Implementation Plan:** `PHASE_3_CACHING_IMPLEMENTATION_PLAN.md`
- **Implementation Complete:** `PHASE_3_IMPLEMENTATION_COMPLETE.md`
- **Testing Script:** `scripts/test_cache.sh`

---

**Ready to test?** Run the Quick Test above! 🚀