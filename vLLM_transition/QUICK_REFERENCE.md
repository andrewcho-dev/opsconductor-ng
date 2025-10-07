# Quick Reference Card

## 🎯 One-Page Summary

### The Transformation
```
90 seconds → 3-5 seconds (uncached) or 0.1 seconds (cached)
```

### Three Phases
1. **vLLM Migration** (1-2 days) → 43s to 10-15s
2. **Prompt Compression** (1-2 days) → 10-15s to 3-5s
3. **Caching Layer** (1-2 days) → 3-5s to 0.1s (cached)

---

## 📚 Document Quick Links

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **START_HERE.md** | Entry point | First time |
| **VISUAL_SUMMARY.md** | Visual overview | First time |
| **00_TRANSFORMATION_OVERVIEW.md** | Strategy | Before starting |
| **05_IMPLEMENTATION_CHECKLIST.md** | Step-by-step | During implementation |
| **01_VLLM_MIGRATION_GUIDE.md** | Phase 1 details | Day 1-2 |
| **02_PROMPT_OPTIMIZATION_GUIDE.md** | Phase 2 details | Day 2-3 |
| **03_CACHING_ARCHITECTURE.md** | Phase 3 details | Day 3-4 |
| **06_TROUBLESHOOTING_GUIDE.md** | Problem solving | When stuck |
| **04_PERFORMANCE_SUMMARY.md** | Results | After completion |

---

## 🚀 Phase 1: vLLM Migration

### Commands
```bash
# Install
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct-AWQ \
  --dtype auto \
  --port 8000 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.92 \
  --enforce-eager \
  --quantization awq

# Test
curl http://localhost:8000/health
```

### Config Changes
```yaml
# config/llm_config.yaml
llm:
  base_url: "http://localhost:8000/v1"  # Was: localhost:11434/v1
  model: "Qwen/Qwen2.5-7B-Instruct-AWQ"  # Was: qwen2.5:7b
```

### Expected Result
Stage A: 43s → 10-15s (65-77% faster)

---

## 📝 Phase 2: Prompt Optimization

### Changes
1. **Intent prompt:** 2,500 → 500 chars (80% reduction)
2. **Entity prompt:** 1,000 → 300 chars (70% reduction)
3. **Confidence + Risk:** 2 calls → 1 call (50% reduction)

### Files to Edit
- `llm/prompt_manager.py` (intent & entity prompts)
- `pipeline/stages/stage_a/classifier.py` (merge confidence+risk)

### Validation
```bash
python validate_prompt_optimization.py
# Expected: ≥93% accuracy (≤5% degradation)
```

### Expected Result
Stage A: 10-15s → 3-5s (67-80% faster)

---

## 💾 Phase 3: Caching Layer

### Setup Redis
```bash
# Install
sudo apt install redis-server

# Start
sudo systemctl start redis-server

# Test
redis-cli ping  # Expected: PONG
```

### Three Cache Layers
1. **Intent Cache** (Redis) - TTL: 1 hour
2. **Asset Context Cache** (Redis + Memory) - TTL: 5 minutes
3. **Tool Result Cache** (Redis) - TTL: 30s-5min

### Files to Create
- `pipeline/stages/stage_a/intent_cache.py`
- `pipeline/stages/stage_c/tool_result_cache.py`
- `pipeline/integration/cache_manager.py`

### Files to Edit
- `pipeline/stages/stage_a/classifier.py` (add intent cache)
- `pipeline/integration/asset_service_context.py` (enhance cache)
- `pipeline/stages/stage_c/executor.py` (add tool cache)

### Expected Result
Stage A: 3-5s → 0.1s (cached), 30-50% cache hit rate

---

## 🔍 Monitoring Commands

```bash
# Check services
systemctl status vllm redis-server

# Monitor GPU
watch -n 1 nvidia-smi

# Test LLM
curl http://localhost:8000/health

# Check cache stats
curl http://localhost:5001/cache/stats

# Run performance test
python test_pipeline_performance.py

# View logs
journalctl -u vllm -f
journalctl -u redis-server -f

# Redis stats
redis-cli INFO memory
redis-cli DBSIZE
```

---

## 🚨 Common Issues

### vLLM Won't Start
```bash
# Check GPU
nvidia-smi

# Check port
sudo lsof -i :8000

# Reduce memory
--gpu-memory-utilization 0.85  # Was 0.92
```

### Out of Memory
```bash
# Reduce max length
--max-model-len 3072  # Was 4096

# Add enforce-eager
--enforce-eager
```

### Redis Connection Failed
```bash
# Start Redis
sudo systemctl start redis-server

# Test connection
redis-cli ping
```

### Low Cache Hit Rate
```python
# Improve query normalization
def normalize_query(query: str) -> str:
    query = query.lower().strip()
    query = ' '.join(query.split())
    query = query.replace("please ", "")
    query = query.replace("show me ", "show ")
    return query
```

---

## ✅ Success Criteria

### Performance
- [ ] Stage A < 5s (uncached)
- [ ] Stage A < 0.5s (cached)
- [ ] Full pipeline < 30s (uncached)
- [ ] Full pipeline < 10s (cached)
- [ ] 70%+ token reduction
- [ ] 30%+ cache hit rate

### Quality
- [ ] ≥93% accuracy (≤5% degradation)
- [ ] All features work
- [ ] Asset database preserved
- [ ] Approval gates unchanged
- [ ] Audit trails maintained

---

## 📊 Performance Targets

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Stage A (uncached) | 43.98s | 3-5s | 88-93% faster |
| Stage A (cached) | 43.98s | 0.1s | 99.8% faster |
| Full pipeline (uncached) | ~90s | ~25s | 72% faster |
| Full pipeline (cached) | ~90s | ~5s | 94% faster |
| Token usage | 1,275 | 300 | 76% reduction |
| LLM calls | 4 | 3 | 25% reduction |

---

## 🔄 Rollback Plan

If something goes wrong:

```bash
# Stop vLLM
sudo systemctl stop vllm

# Restore Ollama
sudo systemctl start ollama

# Restore config
cp config/llm_config.yaml.backup config/llm_config.yaml

# Restore code
git checkout main

# Restart OpsConductor
sudo systemctl restart opsconductor
```

---

## 📞 Quick Help

### Diagnostic Info to Collect
```bash
# System info
uname -a
nvidia-smi
python --version

# Service status
systemctl status vllm redis-server

# Logs
journalctl -u vllm -n 100
journalctl -u redis-server -n 100

# Performance
curl http://localhost:5001/cache/stats
python test_pipeline_performance.py

# Config
cat config/llm_config.yaml
redis-cli CONFIG GET maxmemory
```

---

## 🎯 Implementation Order

```
Day 1: vLLM Setup
├─ Install vLLM
├─ Start server
├─ Update config
└─ Validate (43s → 10-15s)

Day 2: Prompt Compression
├─ Compress intent prompt
├─ Compress entity prompt
├─ Merge confidence+risk
└─ Validate (10-15s → 3-5s)

Day 3: Caching Layer
├─ Install Redis
├─ Implement intent cache
├─ Enhance asset cache
└─ Add tool cache (3-5s → 0.1s cached)

Day 4: Testing
├─ Run comprehensive tests
├─ Validate accuracy
└─ Document results
```

---

## 💡 Key Insights

### Why This Works
1. vLLM is production-grade (used by Anthropic, Cohere)
2. Prompt compression is free (no hardware changes)
3. Caching is low-hanging fruit (30-50% queries repetitive)
4. Architecture is sound (no need to rebuild)
5. Asset database is strategic advantage

### Why NOT ReAct
- Would require rebuilding approval gates, audit trails
- Wouldn't solve LLM speed problem
- Would lose asset database integration
- Takes weeks vs. days

**Problem is prompt bloat and LLM speed, not architecture.**

---

## 🎉 Expected Outcome

```
OpsConductor will be FASTER than ChatGPT for infrastructure queries

Why?
✅ Asset database provides instant context
✅ No discovery or clarification needed
✅ Optimized prompts (76% fewer tokens)
✅ Intelligent caching (99% improvement)
✅ Local inference (no network latency)

Result:
🚀 0.3s for "list servers" (vs ChatGPT: 2-3s)
🚀 3s for complex queries (vs ChatGPT: 5-10s)
🚀 Institutional knowledge (vs ChatGPT: generic)
```

---

**Print this page for quick reference during implementation!**

**Next:** [START_HERE.md](./START_HERE.md) → [VISUAL_SUMMARY.md](./VISUAL_SUMMARY.md)