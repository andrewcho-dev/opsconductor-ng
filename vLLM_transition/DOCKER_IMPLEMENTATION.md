# vLLM Docker Implementation

## ✅ What Was Fixed

### The Problem
- vLLM was incorrectly installed on the **host system** instead of in a Docker container
- This violated the established architecture where all OpsConductor services run in containers
- Created inconsistency with the existing docker-compose.yml setup

### The Solution
- **Removed** vLLM from host system (`pip uninstall vllm`)
- **Created** `Dockerfile.vllm` with proper NVIDIA CUDA base image
- **Replaced** Ollama service with vLLM service in `docker-compose.yml`
- **Updated** ai-pipeline service to use vLLM container

---

## 📁 Files Created/Modified

### New Files
1. **`Dockerfile.vllm`** - vLLM container definition
   - Base: `nvidia/cuda:12.1.0-runtime-ubuntu22.04`
   - Installs: vLLM 0.11.0, Python 3.10, curl
   - Pre-downloads: Qwen/Qwen2.5-7B-Instruct-AWQ model
   - Exposes: Port 8000

### Modified Files
1. **`docker-compose.yml`**
   - Replaced `ollama` service with `vllm` service
   - Updated `ai-pipeline` environment variables:
     - `LLM_PROVIDER=vllm`
     - `LLM_BASE_URL=http://vllm:8000/v1`
     - `LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ`
   - Changed dependency from `ollama` to `vllm`
   - Updated volume from `ollama_models` to `vllm_cache`

### Deleted Files
- `vllm.service` (systemd service - no longer needed)
- `start_vllm.sh` (startup script - no longer needed)
- `vllm_startup_test.log` (test log - no longer needed)

---

## 🐳 Docker Configuration

### vLLM Service
```yaml
vllm:
  build:
    context: .
    dockerfile: Dockerfile.vllm
  container_name: opsconductor-vllm
  ports:
    - "8000:8000"
  volumes:
    - vllm_cache:/root/.cache/huggingface
  networks:
    - opsconductor
  environment:
    - CUDA_VISIBLE_DEVICES=0
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 90s
```

### Key Features
- **GPU Access**: Uses NVIDIA Docker runtime for GPU acceleration
- **Persistent Cache**: Model cached in Docker volume `vllm_cache`
- **Health Checks**: Monitors `/health` endpoint
- **Network**: Connected to `opsconductor` bridge network
- **Port**: Exposed on host port 8000

---

## 🚀 Usage

### Build vLLM Container
```bash
cd /home/opsconductor/opsconductor-ng
docker compose build vllm
```

### Start vLLM Service
```bash
docker compose up -d vllm
```

### Check vLLM Logs
```bash
docker compose logs -f vllm
```

### Test vLLM Health
```bash
curl http://localhost:8000/health
```

### Start Full Stack (with vLLM)
```bash
docker compose up -d
```

### Stop vLLM Service
```bash
docker compose stop vllm
```

---

## 🔄 Rollback to Ollama (If Needed)

If you need to rollback to Ollama:

1. **Stop vLLM**:
   ```bash
   docker compose stop vllm
   ```

2. **Edit `docker-compose.yml`**:
   - Uncomment the `ollama` service section
   - Comment out the `vllm` service section
   - Update `ai-pipeline` environment:
     ```yaml
     LLM_PROVIDER: ollama
     LLM_BASE_URL: http://ollama:11434
     LLM_MODEL: qwen2.5:7b-instruct-q4_k_m
     ```
   - Change dependency from `vllm` to `ollama`

3. **Restart services**:
   ```bash
   docker compose up -d ollama ai-pipeline
   ```

---

## 📊 Expected Performance

### vLLM Container Startup
- **First build**: 5-10 minutes (downloads base image + model)
- **Subsequent builds**: 1-2 minutes (uses cache)
- **Container startup**: 30-45 seconds (loads model into GPU)

### Runtime Performance
- **Stage A (4 LLM calls)**: 10-15 seconds (vs 43s with Ollama)
- **Single inference**: 2-4 seconds (vs 10-12s with Ollama)
- **GPU utilization**: 85-95% during inference
- **VRAM usage**: ~9-10GB (out of 12GB available)

---

## 🔍 Monitoring

### Check Container Status
```bash
docker compose ps vllm
```

### View GPU Usage
```bash
nvidia-smi
```

### Check vLLM Metrics
```bash
curl http://localhost:8000/metrics
```

### View Available Models
```bash
curl http://localhost:8000/v1/models
```

---

## 🎯 Next Steps

1. **Wait for build to complete** (~5-10 minutes)
2. **Start vLLM container**: `docker compose up -d vllm`
3. **Verify health**: `curl http://localhost:8000/health`
4. **Test inference**: Run `test_pipeline_performance.py`
5. **Validate performance**: Compare Stage A timing (should be 10-15s)
6. **Start full stack**: `docker compose up -d`

---

## ✅ Architecture Compliance

This implementation now properly follows the OpsConductor architecture:
- ✅ All services containerized
- ✅ GPU access via Docker runtime
- ✅ Persistent storage via Docker volumes
- ✅ Service discovery via Docker networks
- ✅ Health checks and monitoring
- ✅ Easy rollback capability
- ✅ Consistent with existing services

---

## 📝 Notes

- The model is downloaded during Docker build and cached in the `vllm_cache` volume
- Subsequent container restarts will reuse the cached model (fast startup)
- The container uses the same GPU as Ollama did (RTX 3060 12GB)
- vLLM and Ollama cannot run simultaneously (both need GPU)
- The `.env` file is already configured for vLLM (no changes needed)