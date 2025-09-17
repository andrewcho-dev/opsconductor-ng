# Fix PyTorch GPU Detection in AI Services

## Summary of Changes Made

1. **Renamed folders for consistency:**
   - `ai-service` → `ai-command` (matches service name and container name)
   - Service names now match folder names throughout

2. **Updated Dockerfiles for GPU support:**
   - `ai-command/Dockerfile` - Now uses CUDA base image and installs PyTorch with CUDA
   - `ai-orchestrator/Dockerfile` - Now uses CUDA base image  
   - Other AI services already had CUDA support

3. **Updated docker-compose.gpu.yml:**
   - Added `ai-command` service with GPU runtime
   - Added `ai-orchestrator` service with GPU runtime
   - All AI services now have GPU configuration

## Steps to Apply Fixes

### 1. Stop all services
```bash
docker-compose down
```

### 2. Clean old images (optional but recommended)
```bash
docker system prune -a --volumes
```

### 3. Rebuild all AI services with GPU support
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build --no-cache ai-command ai-orchestrator nlp-service vector-service llm-service
```

### 4. Start services with GPU support
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

### 5. Verify GPU detection
```bash
# Test GPU is visible to containers
docker exec opsconductor-ai-command nvidia-smi
docker exec opsconductor-nlp nvidia-smi
docker exec opsconductor-vector nvidia-smi
docker exec opsconductor-llm nvidia-smi

# Test PyTorch GPU detection
docker exec opsconductor-ai-command python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
docker exec opsconductor-nlp python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
docker exec opsconductor-vector python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
docker exec opsconductor-llm python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
```

### 6. Run comprehensive test
```bash
# Copy test script to container and run
docker cp check_pytorch_gpu.py opsconductor-ai-command:/tmp/
docker exec opsconductor-ai-command python /tmp/check_pytorch_gpu.py
```

## Troubleshooting

### If GPU still not detected:

1. **Check NVIDIA Docker runtime is installed:**
```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

2. **Verify docker-compose is using GPU runtime:**
```bash
# Should show GPU configuration
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml config | grep -A3 "runtime:"
```

3. **Check container has GPU access:**
```bash
docker inspect opsconductor-ai-command | grep -i gpu
```

4. **Verify PyTorch installation:**
```bash
docker exec opsconductor-ai-command pip show torch | grep Version
```

## Expected Output

When working correctly, you should see:
```
✓ PyTorch version: 2.x.x+cu121
✓ CUDA available: True
✓ CUDA version: 12.1
✓ GPU count: 1
✓ GPU name: NVIDIA GeForce RTX 3060
✓ GPU tensor math test successful: cuda:0

🎉 SUCCESS: PyTorch can use GPU!
```