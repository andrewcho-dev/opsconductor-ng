# Implementation Checklist

## 🎯 Purpose
Step-by-step checklist for implementing the complete performance transformation.

**Estimated Total Time:** 3-5 days  
**Recommended Approach:** Sequential (Phase 1 → Phase 2 → Phase 3)

---

## 📋 Pre-Implementation

### Environment Preparation
- [ ] Backup current OpsConductor codebase
  ```bash
  cd /home/opsconductor
  tar -czf opsconductor-backup-$(date +%Y%m%d).tar.gz opsconductor-ng/
  ```
- [ ] Create git branch for transformation
  ```bash
  cd /home/opsconductor/opsconductor-ng
  git checkout -b performance-optimization
  ```
- [ ] Document current performance baseline
  ```bash
  python test_pipeline_performance.py > baseline_performance.txt
  ```
- [ ] Verify GPU is available
  ```bash
  nvidia-smi
  ```
- [ ] Check available disk space (need ~10GB for vLLM model)
  ```bash
  df -h
  ```

---

## 🚀 Phase 1: vLLM Migration (Day 1-2)

### 1.1: Install vLLM
- [ ] Install vLLM with CUDA support
  ```bash
  pip install vllm
  ```
- [ ] Verify installation
  ```bash
  python -c "import vllm; print(f'vLLM version: {vllm.__version__}')"
  ```
- [ ] Check CUDA availability
  ```bash
  python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
  ```

**Expected output:**
```
vLLM version: 0.6.x
CUDA available: True
```

### 1.2: Download Model
- [ ] Pre-download Qwen2.5-7B-Instruct-AWQ (optional but recommended)
  ```bash
  huggingface-cli download Qwen/Qwen2.5-7B-Instruct-AWQ
  ```
- [ ] Verify model size (~4-5 GB)
  ```bash
  du -sh ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct-AWQ
  ```

### 1.3: Start vLLM Server
- [ ] Start vLLM in terminal (for testing)
  ```bash
  python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct-AWQ \
    --dtype auto \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.92 \
    --enforce-eager \
    --quantization awq
  ```
- [ ] Wait for server to start (watch for "Application startup complete")
- [ ] Test server health
  ```bash
  curl http://localhost:8000/health
  ```
  **Expected:** `{"status": "ok"}`

### 1.4: Test vLLM Connection
- [ ] Create test script `test_vllm_connection.py`
  ```python
  from openai import OpenAI
  
  client = OpenAI(
      base_url="http://localhost:8000/v1",
      api_key="EMPTY"
  )
  
  response = client.chat.completions.create(
      model="Qwen/Qwen2.5-7B-Instruct-AWQ",
      messages=[{"role": "user", "content": "Say 'vLLM is working!'"}],
      max_tokens=50
  )
  
  print(response.choices[0].message.content)
  ```
- [ ] Run test
  ```bash
  python test_vllm_connection.py
  ```
  **Expected:** `vLLM is working!`

### 1.5: Update OpsConductor Configuration
- [ ] Backup current config
  ```bash
  cp config/llm_config.yaml config/llm_config.yaml.backup
  ```
- [ ] Update `config/llm_config.yaml`
  ```yaml
  llm:
    provider: "vllm"
    base_url: "http://localhost:8000/v1"
    model: "Qwen/Qwen2.5-7B-Instruct-AWQ"
    temperature: 0.7
    max_tokens: 2000
  ```
- [ ] Update `.env` (if used)
  ```bash
  LLM_BASE_URL=http://localhost:8000/v1
  LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ
  ```

### 1.6: Validate Integration
- [ ] Run pipeline performance test
  ```bash
  python test_pipeline_performance.py
  ```
- [ ] Record Stage A timing (should be 10-15s vs 43s baseline)
- [ ] Verify all 4 LLM calls work correctly
- [ ] Check GPU utilization during test
  ```bash
  watch -n 1 nvidia-smi
  ```
  **Expected:** 85-95% GPU utilization

### 1.7: Set Up as Service (Optional)
- [ ] Create systemd service file `/etc/systemd/system/vllm.service`
  ```ini
  [Unit]
  Description=vLLM OpenAI API Server
  After=network.target
  
  [Service]
  Type=simple
  User=opsconductor
  WorkingDirectory=/home/opsconductor
  Environment="CUDA_VISIBLE_DEVICES=0"
  ExecStart=/usr/bin/python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct-AWQ \
    --dtype auto \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.92 \
    --enforce-eager \
    --quantization awq
  Restart=always
  RestartSec=10
  
  [Install]
  WantedBy=multi-user.target
  ```
- [ ] Enable and start service
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable vllm
  sudo systemctl start vllm
  sudo systemctl status vllm
  ```

### 1.8: Document Phase 1 Results
- [ ] Record actual Stage A timing
- [ ] Record GPU utilization
- [ ] Record any issues encountered
- [ ] Update `04_PERFORMANCE_TRANSFORMATION_SUMMARY.md` with Phase 1 results

**Phase 1 Complete! Expected improvement: 43s → 10-15s (65-77% faster)**

---

## 📝 Phase 2: Prompt Optimization (Day 2-3)

### 2.1: Prepare Test Dataset
- [ ] Create `test_queries.json` with 50 diverse queries
  ```json
  [
    {
      "query": "List all servers in production",
      "expected_intent": "ASSET_DISCOVERY",
      "expected_entities": {"asset_types": ["server"], "environments": ["production"]},
      "expected_risk": "LOW"
    }
    // ... 49 more queries
  ]
  ```
- [ ] Validate current accuracy on test dataset
  ```bash
  python validate_prompt_optimization.py --mode baseline
  ```

### 2.2: Compress Intent Classification Prompt
- [ ] Backup current prompt manager
  ```bash
  cp llm/prompt_manager.py llm/prompt_manager.py.backup
  ```
- [ ] Edit `llm/prompt_manager.py` → `_build_intent_classification_prompt()`
- [ ] Reduce prompt from 2,500 → 500 characters
  - Remove verbose descriptions
  - Use pipe-separated category list
  - Simplify output format
- [ ] Test new prompt
  ```bash
  python test_intent_classification.py
  ```
- [ ] Validate accuracy (should be ≥93%)
  ```bash
  python validate_prompt_optimization.py --mode intent
  ```
- [ ] Measure token reduction
  ```bash
  python measure_token_usage.py --component intent
  ```
  **Expected:** 625 → 125 tokens (80% reduction)

### 2.3: Compress Entity Extraction Prompt
- [ ] Edit `llm/prompt_manager.py` → `_build_entity_extraction_prompt()`
- [ ] Reduce prompt from 1,000 → 300 characters
  - Remove examples
  - Use compact entity list
  - Simplify instructions
- [ ] Test new prompt
  ```bash
  python test_entity_extraction.py
  ```
- [ ] Validate accuracy (should be ≥93%)
  ```bash
  python validate_prompt_optimization.py --mode entity
  ```
- [ ] Measure token reduction
  ```bash
  python measure_token_usage.py --component entity
  ```
  **Expected:** 250 → 75 tokens (70% reduction)

### 2.4: Merge Confidence + Risk Assessment
- [ ] Backup current classifier
  ```bash
  cp pipeline/stages/stage_a/classifier.py pipeline/stages/stage_a/classifier.py.backup
  ```
- [ ] Edit `pipeline/stages/stage_a/classifier.py`
- [ ] Create new method `_assess_confidence_and_risk()`
  ```python
  async def _assess_confidence_and_risk(
      self,
      query: str,
      intent: str,
      entities: Dict[str, Any]
  ) -> Dict[str, Any]:
      """Merged confidence and risk assessment"""
      prompt = f"""Assess confidence (0.0-1.0) and risk (LOW|MEDIUM|HIGH|CRITICAL).
  
  Query: {query}
  Intent: {intent}
  Entities: {json.dumps(entities)}
  
  Return JSON: {{"confidence": 0.0-1.0, "risk": "LEVEL", "reasoning": "brief"}}"""
      
      response = await self.llm_client.generate(prompt)
      return json.loads(response)
  ```
- [ ] Update `classify()` method to use merged assessment
- [ ] Remove old `_assess_confidence()` and `_assess_risk()` methods
- [ ] Test merged assessment
  ```bash
  python test_confidence_risk.py
  ```
- [ ] Validate accuracy (should be ≥93%)
  ```bash
  python validate_prompt_optimization.py --mode confidence_risk
  ```
- [ ] Measure token reduction
  ```bash
  python measure_token_usage.py --component confidence_risk
  ```
  **Expected:** 400 → 100 tokens (75% reduction), 2 calls → 1 call

### 2.5: Integration Testing
- [ ] Run full pipeline performance test
  ```bash
  python test_pipeline_performance.py
  ```
- [ ] Record Stage A timing (should be 3-5s)
- [ ] Validate accuracy on all 50 test queries
  ```bash
  python validate_prompt_optimization.py --mode full
  ```
- [ ] Compare before/after accuracy (should be ≤5% degradation)

### 2.6: Document Phase 2 Results
- [ ] Record actual Stage A timing
- [ ] Record token reduction percentages
- [ ] Record accuracy metrics
- [ ] Update `04_PERFORMANCE_TRANSFORMATION_SUMMARY.md` with Phase 2 results

**Phase 2 Complete! Expected improvement: 10-15s → 3-5s (67-80% faster from Phase 1)**

---

## 💾 Phase 3: Caching Layer (Day 3-4)

### 3.1: Install and Configure Redis
- [ ] Install Redis
  ```bash
  sudo apt update
  sudo apt install redis-server
  ```
- [ ] Start Redis
  ```bash
  sudo systemctl start redis-server
  sudo systemctl enable redis-server
  ```
- [ ] Test Redis
  ```bash
  redis-cli ping
  ```
  **Expected:** `PONG`
- [ ] Configure Redis (`/etc/redis/redis.conf`)
  ```conf
  maxmemory 2gb
  maxmemory-policy allkeys-lru
  save ""
  appendonly no
  ```
- [ ] Restart Redis
  ```bash
  sudo systemctl restart redis-server
  ```
- [ ] Install Python Redis client
  ```bash
  pip install redis
  ```

### 3.2: Implement Intent Cache
- [ ] Create `pipeline/stages/stage_a/intent_cache.py`
  - Implement `IntentCache` class
  - Add query normalization
  - Add cache statistics
- [ ] Edit `pipeline/stages/stage_a/classifier.py`
  - Add `self.cache = IntentCache()`
  - Wrap `classify()` with cache check
- [ ] Test intent cache
  ```bash
  python test_intent_cache.py
  ```
- [ ] Verify cache hit/miss behavior
  ```bash
  # First call (miss)
  python -c "from pipeline.stages.stage_a.classifier import IntentClassifier; c = IntentClassifier({}); print(c.classify('list servers'))"
  # Second call (hit)
  python -c "from pipeline.stages.stage_a.classifier import IntentClassifier; c = IntentClassifier({}); print(c.classify('list servers'))"
  ```

### 3.3: Implement Cache Warmer
- [ ] Create `pipeline/stages/stage_a/cache_warmer.py`
  - Define common queries list
  - Implement `warm_cache()` method
- [ ] Run cache warmer
  ```bash
  python -m pipeline.stages.stage_a.cache_warmer
  ```
- [ ] Verify cache is populated
  ```bash
  redis-cli KEYS "intent:*"
  ```

### 3.4: Enhance Asset Context Cache
- [ ] Backup current asset context
  ```bash
  cp pipeline/integration/asset_service_context.py pipeline/integration/asset_service_context.py.backup
  ```
- [ ] Edit `pipeline/integration/asset_service_context.py`
  - Add Redis backing
  - Implement two-level caching (memory + Redis)
  - Increase TTL from 60s → 300s
- [ ] Test asset context cache
  ```bash
  python test_asset_context_cache.py
  ```
- [ ] Verify cache hit rates
  ```bash
  python -c "from pipeline.integration.asset_service_context import AssetServiceContext; c = AssetServiceContext(); print(c.get_stats())"
  ```

### 3.5: Implement Tool Result Cache
- [ ] Create `pipeline/stages/stage_c/tool_result_cache.py`
  - Implement `ToolResultCache` class
  - Define cacheable vs uncacheable tools
  - Configure tool-specific TTLs
- [ ] Edit `pipeline/stages/stage_c/executor.py`
  - Add `self.cache = ToolResultCache()`
  - Wrap `execute_tool()` with cache check
- [ ] Test tool result cache
  ```bash
  python test_tool_result_cache.py
  ```

### 3.6: Implement Cache Manager
- [ ] Create `pipeline/integration/cache_manager.py`
  - Implement `CacheManager` class
  - Add `invalidate_asset()` method
  - Add `invalidate_all()` method
  - Add `get_global_stats()` method
- [ ] Test cache manager
  ```bash
  python test_cache_manager.py
  ```

### 3.7: Create Cache Dashboard
- [ ] Create `pipeline/monitoring/cache_dashboard.py`
  - Implement Flask endpoints for stats, invalidation
- [ ] Start dashboard
  ```bash
  python pipeline/monitoring/cache_dashboard.py
  ```
- [ ] Test dashboard endpoints
  ```bash
  curl http://localhost:5001/cache/stats
  curl -X POST http://localhost:5001/cache/invalidate/web-server-01
  ```

### 3.8: Integration Testing
- [ ] Run full pipeline performance test (uncached)
  ```bash
  python test_pipeline_performance.py
  ```
- [ ] Run full pipeline performance test (cached)
  ```bash
  python test_pipeline_performance.py --cached
  ```
- [ ] Record latency for both scenarios
- [ ] Monitor cache hit rates over 24 hours
  ```bash
  watch -n 60 "curl -s http://localhost:5001/cache/stats | jq"
  ```

### 3.9: Document Phase 3 Results
- [ ] Record cache hit rates (intent, asset, tool)
- [ ] Record latency improvements (cached vs uncached)
- [ ] Record cache memory usage
- [ ] Update `04_PERFORMANCE_TRANSFORMATION_SUMMARY.md` with Phase 3 results

**Phase 3 Complete! Expected improvement: 3-5s → 0.1s for cached queries (97-98% faster)**

---

## 📊 Phase 4: Validation & Documentation (Day 5)

### 4.1: Comprehensive Performance Testing
- [ ] Run performance tests on 100+ diverse queries
  ```bash
  python test_comprehensive_performance.py
  ```
- [ ] Measure P50, P95, P99 latencies
- [ ] Compare against baseline
- [ ] Generate performance graphs

### 4.2: Accuracy Validation
- [ ] Run accuracy tests on 50+ test queries
  ```bash
  python validate_accuracy.py
  ```
- [ ] Compare against baseline accuracy
- [ ] Identify any misclassifications
- [ ] Document accuracy metrics

### 4.3: Production Monitoring (1 Week)
- [ ] Deploy to production
- [ ] Monitor cache hit rates daily
  ```bash
  curl http://localhost:5001/cache/stats
  ```
- [ ] Monitor latency metrics
- [ ] Monitor error rates
- [ ] Monitor resource utilization (GPU, CPU, RAM, Redis)

### 4.4: Complete Documentation
- [ ] Fill in all `[MEASURED]` placeholders in `04_PERFORMANCE_TRANSFORMATION_SUMMARY.md`
- [ ] Add performance graphs
- [ ] Document lessons learned
- [ ] Document challenges encountered
- [ ] Add recommendations for future optimizations

### 4.5: Update Main Documentation
- [ ] Update main `README.md` with new performance metrics
- [ ] Update architecture diagrams (if needed)
- [ ] Add link to transformation documentation
- [ ] Update troubleshooting guide

### 4.6: Code Cleanup
- [ ] Remove backup files (`.backup`)
- [ ] Remove debug logging
- [ ] Add comments to optimized code
- [ ] Run linter/formatter
  ```bash
  black .
  flake8 .
  ```

### 4.7: Git Commit
- [ ] Review all changes
  ```bash
  git diff
  ```
- [ ] Commit changes
  ```bash
  git add .
  git commit -m "Performance optimization: vLLM + prompt compression + caching"
  ```
- [ ] Merge to main branch
  ```bash
  git checkout main
  git merge performance-optimization
  ```
- [ ] Tag release
  ```bash
  git tag -a v2.0.0 -m "Performance optimization release"
  git push origin v2.0.0
  ```

**Phase 4 Complete! Transformation fully documented and deployed.**

---

## ✅ Final Checklist

### Performance Validation
- [ ] Stage A < 5s (uncached) ✅
- [ ] Stage A < 0.5s (cached) ✅
- [ ] Full pipeline < 30s (uncached) ✅
- [ ] Full pipeline < 10s (cached) ✅
- [ ] 70%+ token reduction ✅
- [ ] 30%+ cache hit rate ✅

### Quality Validation
- [ ] No accuracy degradation (≤5%) ✅
- [ ] All existing features work ✅
- [ ] Asset database preserved ✅
- [ ] Approval gates unchanged ✅
- [ ] Audit trails maintained ✅

### Documentation
- [ ] All transformation documents complete ✅
- [ ] Performance metrics documented ✅
- [ ] Lessons learned documented ✅
- [ ] Main README updated ✅

### Deployment
- [ ] vLLM running as service ✅
- [ ] Redis running as service ✅
- [ ] Cache dashboard accessible ✅
- [ ] Monitoring in place ✅

---

## 🎯 Success Criteria

**Transformation is successful if:**
1. ✅ Stage A latency reduced by 70%+ (43s → <13s)
2. ✅ Cached queries respond in <1s
3. ✅ Token usage reduced by 70%+
4. ✅ Cache hit rate >30%
5. ✅ Accuracy maintained (≤5% degradation)
6. ✅ All features work unchanged

---

## 🚨 Rollback Plan

If transformation fails:

1. **Stop vLLM service**
   ```bash
   sudo systemctl stop vllm
   ```

2. **Restore Ollama**
   ```bash
   sudo systemctl start ollama
   ```

3. **Restore configuration**
   ```bash
   cp config/llm_config.yaml.backup config/llm_config.yaml
   ```

4. **Restore code**
   ```bash
   git checkout main
   ```

5. **Restart OpsConductor**
   ```bash
   sudo systemctl restart opsconductor
   ```

---

**Document Status:** Ready for Use  
**Last Updated:** 2025-01-XX  
**Estimated Completion Time:** 3-5 days  
**Risk Level:** Low-Medium (incremental changes, easy rollback)