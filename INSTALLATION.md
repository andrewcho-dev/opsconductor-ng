# OpsConductor NG - Complete Installation Guide

This guide provides step-by-step instructions to recreate the OpsConductor NG environment on any machine with NVIDIA GPU support.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Hardware Requirements](#hardware-requirements)
3. [System Setup](#system-setup)
4. [Installation Steps](#installation-steps)
5. [Configuration](#configuration)
6. [Starting the Platform](#starting-the-platform)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Operating System**: Ubuntu 22.04 LTS or later (Linux)
- **Docker**: Version 24.0+ with Docker Compose V2
- **NVIDIA Driver**: Version 535+ (for CUDA 12.1 support)
- **NVIDIA Container Toolkit**: Latest version
- **Git**: For cloning the repository
- **curl**: For testing API endpoints

### Installation Commands

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install NVIDIA Driver (if not already installed)
sudo apt-get install -y nvidia-driver-535

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU access in Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## Hardware Requirements

### Minimum Requirements

- **CPU**: 4 cores
- **RAM**: 16 GB
- **Storage**: 100 GB free space
- **GPU**: NVIDIA GPU with 8GB+ VRAM (Compute Capability 7.0+)

### Recommended Configuration

- **CPU**: 8+ cores
- **RAM**: 32 GB
- **Storage**: 200 GB SSD
- **GPU**: NVIDIA RTX 3090 Ti (24GB) or RTX 4090 (24GB)

### Tested Configurations

| GPU Model | VRAM | Architecture | Status | Notes |
|-----------|------|--------------|--------|-------|
| RTX 3060 | 12 GB | Ampere | ✅ Works | Limited context (8K tokens) |
| RTX 3090 Ti | 24 GB | Ampere | ✅ Recommended | 32K context, no FP8 |
| RTX 4090 | 24 GB | Ada Lovelace | ✅ Best | 64K context with FP8 |

---

## System Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/opsconductor-ng.git
cd opsconductor-ng

# Checkout the performance-optimization branch (contains vLLM fixes)
git checkout performance-optimization
```

### 2. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your settings
nano .env
```

**Key Environment Variables:**

```bash
# Database Configuration
POSTGRES_DB=opsconductor
POSTGRES_USER=opsconductor
POSTGRES_PASSWORD=opsconductor_secure_2024

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# vLLM Configuration
VLLM_HOST=vllm
VLLM_PORT=8000
CUDA_VISIBLE_DEVICES=0

# API Configuration
AI_PIPELINE_PORT=3005
FRONTEND_PORT=3100
KONG_PORT=3000
```

---

## Installation Steps

### Step 1: Verify GPU Configuration

```bash
# Check NVIDIA driver
nvidia-smi

# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Step 2: Choose GPU Configuration

The repository includes optimized configurations for different GPUs:

#### For RTX 3090 Ti (24GB) - **RECOMMENDED**

```bash
# The docker-compose.yml is already configured for RTX 3090 Ti
# It uses Dockerfile.vllm.3090ti with optimized settings
```

**Configuration Details:**
- Model: Qwen/Qwen2.5-14B-Instruct-AWQ
- KV Cache: auto (uses FP16 on Ampere)
- Max Context: 8192 tokens
- Max Sequences: 2
- GPU Memory: 92%

#### For Other GPUs

If you have a different GPU, you may need to adjust the configuration:

1. **RTX 3060 (12GB)**: Reduce `max-model-len` to 4096 and `gpu-memory-utilization` to 0.85
2. **RTX 4090 (24GB)**: Can use FP8 KV cache for better performance
3. **Data Center GPUs (A100, H100)**: Can run larger models (32B, 72B)

Edit `Dockerfile.vllm.3090ti` to adjust parameters:

```dockerfile
CMD ["python3", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", "Qwen/Qwen2.5-14B-Instruct-AWQ", \
     "--quantization", "awq", \
     "--kv-cache-dtype", "auto", \
     "--max-model-len", "8192", \
     "--max-num-seqs", "2", \
     "--gpu-memory-utilization", "0.92", \
     "--enforce-eager", \
     "--port", "8000", \
     "--host", "0.0.0.0"]
```

### Step 3: Build and Start Services

```bash
# Pull base images and build custom images
docker compose build

# Start all services
docker compose up -d

# Monitor startup progress
docker compose logs -f
```

**Expected Startup Time:**
- Infrastructure services (postgres, redis, kong): 30-60 seconds
- vLLM model loading: 2-3 minutes (first time may take longer to download model)
- Application services: 30-60 seconds
- Total: 3-5 minutes

---

## Configuration

### vLLM Configuration Profiles

The repository includes a helper script for different performance profiles:

```bash
# Make the script executable
chmod +x start_vllm_3090ti.sh

# Start with different profiles
./start_vllm_3090ti.sh balanced        # 16K context (recommended)
./start_vllm_3090ti.sh max-context     # 32K context (long documents)
./start_vllm_3090ti.sh high-throughput # 8K context (high concurrency)
```

**Profile Comparison:**

| Profile | Context | Sequences | Memory | Use Case |
|---------|---------|-----------|--------|----------|
| balanced | 16K | 4 | 90% | General use (recommended) |
| max-context | 32K | 2 | 95% | Long documents, large codebases |
| high-throughput | 8K | 8 | 85% | API serving, many users |

### Database Schema

The database schema is automatically initialized on first startup from:
```
database/init-schema.sql
```

This creates all necessary tables, indexes, and initial data.

---

## Starting the Platform

### Full Stack Startup

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Check specific service
docker compose logs -f vllm
```

### Service-by-Service Startup

For debugging or development:

```bash
# Start infrastructure first
docker compose up -d postgres redis kong keycloak

# Wait for health checks
sleep 30

# Start vLLM
docker compose up -d vllm

# Wait for model loading
sleep 120

# Start application services
docker compose up -d automation asset network communication

# Start AI pipeline
docker compose up -d ai-pipeline

# Start frontend
docker compose up -d frontend
```

### Stopping the Platform

```bash
# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Stop and rebuild
docker compose down && docker compose up -d --build
```

---

## Verification

### 1. Check Container Status

```bash
# All containers should be running and healthy
docker compose ps

# Expected output:
# NAME                        STATUS
# opsconductor-postgres       Up (healthy)
# opsconductor-redis          Up (healthy)
# opsconductor-vllm           Up (healthy)
# opsconductor-kong           Up (healthy)
# opsconductor-keycloak       Up (healthy)
# opsconductor-automation     Up (healthy)
# opsconductor-asset          Up (healthy)
# opsconductor-network        Up (healthy)
# opsconductor-communication  Up (healthy)
# opsconductor-ai-pipeline    Up (healthy)
# opsconductor-frontend       Up (healthy)
```

### 2. Test vLLM API

```bash
# Health check
curl http://localhost:8000/health

# Test completion
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
    "prompt": "Hello, how are you?",
    "max_tokens": 50
  }'
```

### 3. Test AI Pipeline

```bash
# Submit a request
curl -X POST http://localhost:3005/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Check system status",
    "context": {}
  }'
```

### 4. Access Web Interface

Open your browser and navigate to:
- **Frontend**: http://localhost:3100
- **Kong Admin**: http://localhost:8888
- **Keycloak**: http://localhost:8090

---

## Troubleshooting

### vLLM Container Fails to Start

**Symptom**: vLLM container exits with error code 2

**Solution**: Check the logs for parameter errors:

```bash
docker compose logs vllm

# Common issues:
# 1. Invalid kv-cache-dtype parameter
# 2. Out of memory
# 3. CUDA version mismatch
```

**Fix for kv-cache-dtype error:**

The `fp16` parameter was removed in vLLM 0.11.0. Use `auto` instead:

```dockerfile
# In Dockerfile.vllm.3090ti, line 30:
"--kv-cache-dtype", "auto",  # Changed from "fp16"
```

### Out of Memory Errors

**Symptom**: CUDA out of memory errors in vLLM logs

**Solution**: Reduce memory usage:

```bash
# Edit Dockerfile.vllm.3090ti
# Reduce max-model-len
"--max-model-len", "4096",  # Down from 8192

# Reduce GPU memory utilization
"--gpu-memory-utilization", "0.85",  # Down from 0.92

# Rebuild
docker compose up -d --build vllm
```

### Database Connection Errors

**Symptom**: Services can't connect to PostgreSQL

**Solution**: Check database health:

```bash
# Check postgres logs
docker compose logs postgres

# Verify database is ready
docker compose exec postgres pg_isready -U opsconductor

# Restart services
docker compose restart automation asset network communication ai-pipeline
```

### Model Download Issues

**Symptom**: vLLM takes very long to start or fails to download model

**Solution**: Pre-download the model:

```bash
# Download model manually
docker run --rm -v vllm_cache:/root/.cache/huggingface \
  nvidia/cuda:12.1.0-runtime-ubuntu22.04 \
  bash -c "apt-get update && apt-get install -y python3-pip && \
           pip3 install huggingface-hub && \
           python3 -c 'from huggingface_hub import snapshot_download; \
           snapshot_download(\"Qwen/Qwen2.5-14B-Instruct-AWQ\")'"

# Then start vLLM
docker compose up -d vllm
```

### Port Conflicts

**Symptom**: Services fail to start due to port already in use

**Solution**: Check and modify ports in docker-compose.yml:

```bash
# Check what's using the port
sudo lsof -i :8000  # vLLM
sudo lsof -i :3005  # AI Pipeline
sudo lsof -i :3100  # Frontend

# Edit docker-compose.yml to use different ports
# Example: Change vLLM from 8000 to 8001
ports:
  - "8001:8000"
```

### GPU Not Detected

**Symptom**: vLLM can't find GPU

**Solution**: Verify NVIDIA setup:

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Restart Docker daemon
sudo systemctl restart docker

# Rebuild vLLM container
docker compose up -d --build vllm
```

---

## Advanced Configuration

### Using Different Models

To use a different model, edit `Dockerfile.vllm.3090ti`:

```dockerfile
# Change model in line 15 (pre-download)
RUN pip3 install --no-cache-dir huggingface-hub && \
    python3 -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Qwen/Qwen2.5-32B-Instruct-AWQ')"

# Change model in line 28 (runtime)
"--model", "Qwen/Qwen2.5-32B-Instruct-AWQ",
```

**Recommended Models:**

| Model | Size | VRAM | Context | Use Case |
|-------|------|------|---------|----------|
| Qwen2.5-7B-Instruct-AWQ | 7B | 6GB | 32K | Small GPUs |
| Qwen2.5-14B-Instruct-AWQ | 14B | 10GB | 32K | Balanced (default) |
| Qwen2.5-32B-Instruct-AWQ | 32B | 20GB | 32K | Best quality |
| Qwen2.5-72B-Instruct-AWQ | 72B | 45GB | 32K | Multi-GPU only |

### Multi-GPU Setup

For systems with multiple GPUs:

```dockerfile
# In Dockerfile.vllm.3090ti, add tensor parallelism
CMD ["python3", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", "Qwen/Qwen2.5-32B-Instruct-AWQ", \
     "--tensor-parallel-size", "2", \
     # ... other parameters
```

### Production Deployment

For production environments:

1. **Use external database**: Replace PostgreSQL container with managed database
2. **Use external Redis**: Replace Redis container with managed Redis
3. **Add monitoring**: Integrate Prometheus and Grafana
4. **Add load balancer**: Use NGINX or HAProxy in front of Kong
5. **Enable HTTPS**: Configure SSL certificates in Kong
6. **Backup strategy**: Implement automated backups for database and volumes

---

## File Checklist

Ensure these files are present and properly configured:

- ✅ `docker-compose.yml` - Main orchestration file
- ✅ `Dockerfile.vllm.3090ti` - vLLM container with fixed kv-cache-dtype
- ✅ `start_vllm_3090ti.sh` - Helper script for different profiles
- ✅ `RTX_3090Ti_SETUP.md` - GPU-specific documentation
- ✅ `.env` - Environment variables (copy from .env.example)
- ✅ `database/init-schema.sql` - Database initialization
- ✅ `kong/kong.yml` - API Gateway configuration
- ✅ All service directories with Dockerfiles

---

## Quick Reference

### Essential Commands

```bash
# Start everything
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Restart a service
docker compose restart vllm

# Rebuild a service
docker compose up -d --build vllm

# Stop everything
docker compose down

# Clean slate (removes volumes)
docker compose down -v
```

### Service URLs

- Frontend: http://localhost:3100
- AI Pipeline: http://localhost:3005
- vLLM API: http://localhost:8000
- Kong Gateway: http://localhost:3000
- Kong Admin: http://localhost:8888
- Keycloak: http://localhost:8090
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## Support and Documentation

For more information, see:

- `README.md` - Project overview
- `RTX_3090Ti_SETUP.md` - GPU-specific setup guide
- `DEPLOYMENT.md` - Production deployment guide
- `CLEAN_ARCHITECTURE.md` - Architecture documentation

---

## Version Information

- **OpsConductor NG**: Latest (performance-optimization branch)
- **vLLM**: 0.11.0
- **Docker Compose**: V2
- **CUDA**: 12.1
- **Python**: 3.10+
- **PostgreSQL**: 17
- **Redis**: 7
- **Kong**: 3.4
- **Keycloak**: 22

---

**Last Updated**: 2025-01-XX  
**Tested On**: Ubuntu 22.04 LTS with RTX 3090 Ti (24GB)