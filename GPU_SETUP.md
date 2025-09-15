# OpsConductor GPU Setup Guide

This guide explains how to set up and verify GPU acceleration for OpsConductor's AI services.

## 🚀 Overview

OpsConductor's AI services (NLP, Vector, and LLM services) are designed to leverage GPU acceleration for improved performance:

- **NLP Service**: GPU-accelerated spaCy models and transformers
- **Vector Service**: GPU-accelerated sentence transformers and FAISS
- **LLM Service**: GPU monitoring and acceleration support for Ollama

## 📋 Prerequisites

### 1. NVIDIA GPU and Drivers
- NVIDIA GPU with CUDA Compute Capability 3.5+
- NVIDIA drivers (version 450.80.02+)
- Verify with: `nvidia-smi`

### 2. NVIDIA Container Toolkit
Install NVIDIA Container Toolkit for Docker GPU support:

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker daemon
sudo systemctl restart docker
```

### 3. Docker Compose
- Docker Compose 1.28+ or Docker Compose V2
- Supports GPU resource allocation syntax

## 🔧 Setup Instructions

### 1. Validate GPU Setup
Run the validation script to ensure everything is configured correctly:

```bash
./scripts/validate_gpu_setup.sh
```

This script checks:
- Docker permissions
- NVIDIA drivers and GPU availability
- NVIDIA Container Toolkit installation
- Docker Compose GPU support
- AI service requirements

### 2. Start Services with GPU Support

#### Option A: Using GPU Override File (Recommended)
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

#### Option B: Standard Startup (GPU support included in main compose file)
```bash
docker-compose up -d
```

### 3. Verify GPU Access
After services are running, check GPU status:

```bash
python3 scripts/check_gpu_status.py
```

This will:
- Check health of all AI services
- Verify GPU availability and utilization
- Display memory usage and device information
- Generate a detailed report

## 📊 Monitoring GPU Usage

### Service-Specific GPU Status
Each AI service provides a GPU status endpoint:

```bash
# NLP Service
curl http://localhost:3006/gpu-status

# Vector Service  
curl http://localhost:3007/gpu-status

# LLM Service
curl http://localhost:3008/gpu-status
```

### Service Information with GPU Details
```bash
# Get comprehensive service info including GPU status
curl http://localhost:3006/info  # NLP Service
curl http://localhost:3007/info  # Vector Service
curl http://localhost:3008/info  # LLM Service
```

### Host GPU Monitoring
Monitor GPU usage on the host system:

```bash
# Real-time GPU monitoring
nvidia-smi -l 1

# GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Running processes on GPU
nvidia-smi pmon
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "NVIDIA-SMI has failed"
- **Cause**: NVIDIA drivers not installed or GPU not detected
- **Solution**: Install/update NVIDIA drivers, reboot system

#### 2. "docker: Error response from daemon: could not select device driver"
- **Cause**: NVIDIA Container Toolkit not installed
- **Solution**: Install nvidia-docker2, restart Docker daemon

#### 3. "RuntimeError: No CUDA GPUs are available"
- **Cause**: GPU not accessible in container
- **Solution**: Check Docker GPU access with test container:
  ```bash
  docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
  ```

#### 4. Services start but GPU shows as unavailable
- **Cause**: Container doesn't have GPU access
- **Solution**: 
  - Use GPU override file: `docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d`
  - Check container logs for CUDA errors
  - Verify GPU isn't being used by other processes

#### 5. "ImportError: No module named 'torch'"
- **Cause**: GPU packages not installed in container
- **Solution**: Rebuild containers to install GPU dependencies:
  ```bash
  docker-compose build --no-cache nlp-service vector-service llm-service
  ```

### Debug Commands

```bash
# Check Docker GPU support
docker info | grep -i nvidia

# Test GPU in container
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi

# Check service logs for GPU initialization
docker-compose logs nlp-service | grep -i gpu
docker-compose logs vector-service | grep -i gpu
docker-compose logs llm-service | grep -i gpu

# Check container GPU access
docker exec opsconductor-nlp nvidia-smi
docker exec opsconductor-vector nvidia-smi
docker exec opsconductor-llm nvidia-smi
```

## 🔧 Configuration

### GPU Memory Management
Services automatically detect and use available GPU memory. For fine-tuning:

#### Environment Variables
```yaml
# In docker-compose.yml or docker-compose.gpu.yml
environment:
  - CUDA_VISIBLE_DEVICES=0  # Use specific GPU
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Limit memory fragmentation
```

#### Resource Limits
```yaml
# Limit GPU memory usage
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
    limits:
      memory: 4G  # Limit container memory
```

### Model Configuration
Services use GPU-optimized models by default:

- **NLP Service**: spaCy with GPU support, transformers on CUDA
- **Vector Service**: sentence-transformers on CUDA, FAISS-GPU
- **LLM Service**: Ollama with GPU acceleration

## 📈 Performance Optimization

### Best Practices
1. **Warm-up**: Services may be slower on first GPU operation
2. **Batch Processing**: Process multiple requests together when possible
3. **Memory Management**: Monitor GPU memory to avoid OOM errors
4. **Model Caching**: Models are cached after first load

### Expected Performance Improvements
- **Text Processing**: 3-10x faster with GPU acceleration
- **Embeddings**: 5-15x faster for large batches
- **Model Inference**: 2-8x faster depending on model size

## 🔍 Verification Checklist

After setup, verify:

- [ ] `nvidia-smi` shows GPU(s) available
- [ ] `./scripts/validate_gpu_setup.sh` passes all checks
- [ ] Services start without errors: `docker-compose ps`
- [ ] GPU status endpoints return `"gpu_available": true`
- [ ] `python3 scripts/check_gpu_status.py` shows all services GPU-enabled
- [ ] GPU memory usage visible in `nvidia-smi` during AI operations

## 📚 Additional Resources

- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker Compose GPU Support](https://docs.docker.com/compose/gpu-support/)
- [PyTorch CUDA Documentation](https://pytorch.org/get-started/locally/)
- [spaCy GPU Installation](https://spacy.io/usage/v3#gpu)

## 🆘 Support

If you encounter issues:

1. Run the validation script: `./scripts/validate_gpu_setup.sh`
2. Check the GPU status: `python3 scripts/check_gpu_status.py`
3. Review service logs: `docker-compose logs [service-name]`
4. Test basic GPU access: `docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi`

For persistent issues, include the output of these commands when seeking support.