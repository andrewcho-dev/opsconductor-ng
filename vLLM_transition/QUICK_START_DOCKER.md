# vLLM Docker Quick Start

## 🚀 One-Command Startup

```bash
cd /home/opsconductor/opsconductor-ng
docker compose up -d vllm
```

Wait 30-45 seconds for model to load, then verify:

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

---

## 📋 Common Commands

### Build vLLM Image
```bash
docker compose build vllm
```

### Start vLLM
```bash
docker compose up -d vllm
```

### View Logs
```bash
docker compose logs -f vllm
```

### Stop vLLM
```bash
docker compose stop vllm
```

### Restart vLLM
```bash
docker compose restart vllm
```

### Remove vLLM Container
```bash
docker compose down vllm
```

### Rebuild from Scratch
```bash
docker compose build --no-cache vllm
```

---

## 🔍 Troubleshooting

### Check if vLLM is Running
```bash
docker compose ps vllm
```

### Check GPU Access
```bash
docker exec opsconductor-vllm nvidia-smi
```

### Test Inference
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 50
  }'
```

### View Container Stats
```bash
docker stats opsconductor-vllm
```

---

## 🎯 Integration with OpsConductor

### Start Full Stack
```bash
docker compose up -d
```

This will start:
- vLLM (GPU-accelerated LLM)
- ai-pipeline (uses vLLM)
- All other services (asset, automation, network, communication)
- Frontend
- Infrastructure (postgres, redis, kong, keycloak)

### Test Pipeline Performance
```bash
docker compose exec ai-pipeline python test_pipeline_performance.py
```

Expected Stage A timing: **10-15 seconds** (vs 43s with Ollama)

---

## 📊 Monitoring

### Real-time GPU Usage
```bash
watch -n 1 nvidia-smi
```

### vLLM Metrics
```bash
curl http://localhost:8000/metrics
```

### Available Models
```bash
curl http://localhost:8000/v1/models | jq
```

---

## 🔄 Switching Between vLLM and Ollama

### Currently Using: vLLM
To switch back to Ollama, edit `docker-compose.yml` and change the ai-pipeline environment:

```yaml
# Change from:
LLM_PROVIDER: vllm
LLM_BASE_URL: http://vllm:8000/v1
LLM_MODEL: Qwen/Qwen2.5-7B-Instruct-AWQ

# To:
LLM_PROVIDER: ollama
LLM_BASE_URL: http://ollama:11434
LLM_MODEL: qwen2.5:7b-instruct-q4_k_m
```

Then restart:
```bash
docker compose stop vllm
docker compose up -d ollama ai-pipeline
```

---

## ⚡ Performance Expectations

| Metric | Ollama | vLLM | Improvement |
|--------|--------|------|-------------|
| Stage A (4 calls) | 43s | 10-15s | **65-77% faster** |
| Single inference | 10-12s | 2-4s | **67-80% faster** |
| GPU utilization | 60-70% | 85-95% | Better efficiency |
| Startup time | 10-15s | 30-45s | Slower (acceptable) |

---

## 💾 Storage

### Model Cache Location
- **Volume**: `vllm_cache`
- **Size**: ~5.2GB (Qwen2.5-7B-AWQ model)
- **Persistence**: Survives container restarts

### Clear Cache (if needed)
```bash
docker volume rm opsconductor-ng_vllm_cache
docker compose build --no-cache vllm
```

---

## 🎓 Understanding the Setup

### Why Docker?
- ✅ Consistent with OpsConductor architecture
- ✅ Easy deployment and rollback
- ✅ Isolated dependencies
- ✅ GPU access via NVIDIA runtime
- ✅ Automatic restarts and health checks

### Why vLLM?
- ✅ 3-5x faster than Ollama
- ✅ Better GPU utilization
- ✅ OpenAI-compatible API
- ✅ Production-grade performance
- ✅ Supports quantized models (AWQ)

### Why Qwen2.5-7B-AWQ?
- ✅ Fits in 12GB VRAM (RTX 3060)
- ✅ 4-bit quantization (fast + accurate)
- ✅ Excellent instruction following
- ✅ Good balance of speed and quality