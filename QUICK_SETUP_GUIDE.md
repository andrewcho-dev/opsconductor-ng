# OpsConductor NG - Quick Setup Guide

**Goal**: Get OpsConductor NG running on a new machine in under 30 minutes.

---

## Prerequisites (5 minutes)

### 1. System Requirements
- Ubuntu 22.04 LTS
- NVIDIA GPU with 8GB+ VRAM (24GB recommended)
- 16GB+ RAM
- 100GB+ free disk space

### 2. Install Required Software

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install NVIDIA Driver (if not installed)
sudo apt-get install -y nvidia-driver-535

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Log out and back in for Docker group to take effect
```

### 3. Verify Installation

```bash
# Check Docker
docker --version

# Check NVIDIA
nvidia-smi

# Check GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## Setup (10 minutes)

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/andrewcho-dev/opsconductor-ng.git
cd opsconductor-ng

# Checkout the correct branch
git checkout performance-optimization
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit if needed (optional for testing)
nano .env
```

**Note**: Default values work for testing. For production, change passwords and keys.

### 3. Make Scripts Executable

```bash
chmod +x verify-deployment.sh
chmod +x start_vllm_3090ti.sh
```

---

## Deploy (10 minutes)

### 1. Build Images

```bash
# Build all images (this will take a few minutes)
docker compose build
```

**Expected time**: 3-5 minutes depending on internet speed.

### 2. Start Services

```bash
# Start all services
docker compose up -d
```

**Expected time**: 3-5 minutes for all services to become healthy.

### 3. Monitor Startup

```bash
# Watch logs (Ctrl+C to exit)
docker compose logs -f

# Or check specific service
docker compose logs -f vllm
```

**What to expect**:
- Infrastructure services (postgres, redis, kong) start in 30-60 seconds
- vLLM takes 2-3 minutes to load the model
- Application services start in 30-60 seconds after vLLM is ready

---

## Verify (5 minutes)

### 1. Run Automated Verification

```bash
./verify-deployment.sh
```

**Expected output**: All checks should pass with green checkmarks.

### 2. Manual Verification

```bash
# Check all containers are running
docker compose ps

# Test vLLM
curl http://localhost:8000/health

# Test AI Pipeline
curl http://localhost:3005/health

# Test Frontend
curl http://localhost:3100
```

### 3. Access Web Interface

Open your browser and go to:
- **Frontend**: http://localhost:3100

---

## Test (5 minutes)

### 1. Test vLLM Inference

```bash
curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
    "prompt": "Hello, how are you?",
    "max_tokens": 50
  }'
```

**Expected**: JSON response with generated text.

### 2. Test AI Pipeline

```bash
curl -X POST http://localhost:3005/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Check system status",
    "context": {}
  }'
```

**Expected**: JSON response with pipeline processing results.

### 3. Test Frontend

1. Open http://localhost:3100 in your browser
2. You should see the OpsConductor interface
3. Try submitting a request through the UI

---

## Troubleshooting

### vLLM Won't Start

```bash
# Check logs
docker compose logs vllm

# Common issue: Out of memory
# Solution: Reduce GPU memory usage in Dockerfile.vllm.3090ti
# Change line 33: "--gpu-memory-utilization", "0.85"

# Rebuild
docker compose up -d --build vllm
```

### Services Can't Connect to Database

```bash
# Check database health
docker compose exec postgres pg_isready

# Restart services
docker compose restart automation asset network communication ai-pipeline
```

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

### GPU Not Detected

```bash
# Verify NVIDIA setup
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Restart Docker
sudo systemctl restart docker

# Rebuild vLLM
docker compose up -d --build vllm
```

---

## Common Commands

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# Restart a service
docker compose restart vllm

# View logs
docker compose logs -f

# Check status
docker compose ps

# Rebuild a service
docker compose up -d --build vllm

# Clean slate (removes volumes)
docker compose down -v
```

---

## GPU Configuration

### For Different GPUs

The default configuration is optimized for RTX 3090 Ti (24GB). If you have a different GPU:

#### RTX 3060 (12GB)
Edit `Dockerfile.vllm.3090ti`:
```dockerfile
"--max-model-len", "4096",           # Reduce from 8192
"--gpu-memory-utilization", "0.85",  # Reduce from 0.92
```

#### RTX 4090 (24GB)
Can use the same settings or increase context:
```dockerfile
"--max-model-len", "16384",          # Increase to 16K
"--kv-cache-dtype", "fp8",           # Use FP8 (Ada Lovelace supports it)
```

After editing, rebuild:
```bash
docker compose up -d --build vllm
```

---

## Performance Profiles

Use different vLLM profiles for different workloads:

```bash
# Stop current vLLM
docker compose stop vllm

# Start with different profile
./start_vllm_3090ti.sh balanced        # 16K context (recommended)
./start_vllm_3090ti.sh max-context     # 32K context (long documents)
./start_vllm_3090ti.sh high-throughput # 8K context (high concurrency)
```

---

## Next Steps

### For Development
- Read `CLEAN_ARCHITECTURE.md` for architecture overview
- Check service directories for code structure
- Run tests: `pytest tests/`

### For Production
- Read `DEPLOYMENT.md` for production deployment
- Change all default passwords in `.env`
- Configure SSL/TLS in Kong
- Set up monitoring and backups

### For Customization
- Read `RTX_3090Ti_SETUP.md` for GPU optimization
- Check `DEPLOYMENT_CHECKLIST.md` for comprehensive setup
- Review `INSTALLATION.md` for detailed instructions

---

## Success Checklist

- [ ] All prerequisites installed
- [ ] Repository cloned and configured
- [ ] All containers running and healthy
- [ ] `verify-deployment.sh` passes all checks
- [ ] vLLM responds to inference requests
- [ ] Frontend accessible at http://localhost:3100
- [ ] AI Pipeline processes requests
- [ ] GPU showing utilization in `nvidia-smi`

---

## Support

If you encounter issues:

1. **Check logs**: `docker compose logs -f`
2. **Run verification**: `./verify-deployment.sh`
3. **Review troubleshooting**: See INSTALLATION.md
4. **Check documentation**: See DEPLOYMENT_CHECKLIST.md

---

## Summary

You should now have:
- ✅ All services running and healthy
- ✅ vLLM serving AI models on GPU
- ✅ Frontend accessible in browser
- ✅ AI Pipeline processing requests
- ✅ Automated verification passing

**Total time**: ~30 minutes from fresh Ubuntu install to working system.

**Next**: Start using the platform or customize for your needs!

---

**Quick Reference**:
- Frontend: http://localhost:3100
- AI Pipeline: http://localhost:3005
- vLLM API: http://localhost:8000
- Verify: `./verify-deployment.sh`
- Logs: `docker compose logs -f`
- Status: `docker compose ps`