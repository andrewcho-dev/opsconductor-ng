# OpsConductor NG - Deployment Checklist

Use this checklist to ensure your OpsConductor NG deployment is complete and reproducible on any machine.

## Pre-Deployment Checklist

### System Requirements
- [ ] Ubuntu 22.04 LTS or later installed
- [ ] Minimum 16GB RAM (32GB recommended)
- [ ] Minimum 100GB free disk space (200GB recommended)
- [ ] NVIDIA GPU with 8GB+ VRAM (24GB recommended)
- [ ] Internet connection for downloading images and models

### Software Installation
- [ ] Docker 24.0+ installed
- [ ] Docker Compose V2 installed
- [ ] NVIDIA Driver 535+ installed
- [ ] NVIDIA Container Toolkit installed
- [ ] Git installed
- [ ] curl installed

### Verification Commands
```bash
# Verify Docker
docker --version
docker compose version

# Verify NVIDIA Driver
nvidia-smi

# Verify GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Verify Git
git --version
```

---

## Repository Setup Checklist

### Clone and Configure
- [ ] Repository cloned: `git clone <repo-url>`
- [ ] Correct branch checked out: `git checkout performance-optimization`
- [ ] `.env` file created from `.env.example`
- [ ] `.env` file configured with correct values
- [ ] All scripts made executable: `chmod +x *.sh`

### Required Files Present
- [ ] `docker-compose.yml` - Main orchestration
- [ ] `Dockerfile.vllm.3090ti` - vLLM container (with kv-cache-dtype fix)
- [ ] `start_vllm_3090ti.sh` - vLLM helper script
- [ ] `.env` - Environment configuration
- [ ] `database/init-schema.sql` - Database schema
- [ ] `kong/kong.yml` - API Gateway config
- [ ] `requirements.txt` - Python dependencies

### Service Dockerfiles
- [ ] `frontend/Dockerfile` - React frontend
- [ ] `asset-service/Dockerfile` - Asset service
- [ ] `automation-service/Dockerfile.clean` - Automation service
- [ ] `network-analyzer-service/Dockerfile` - Network analyzer
- [ ] `communication-service/Dockerfile` - Communication service

---

## Configuration Checklist

### Environment Variables (.env)
- [ ] Database credentials configured
- [ ] Redis URL configured
- [ ] JWT secret key set (change from default!)
- [ ] Encryption keys generated and set
- [ ] Service URLs configured
- [ ] CORS origins set to your host IP
- [ ] SMTP settings configured (if using email)
- [ ] Cache settings configured

### GPU Configuration
- [ ] GPU model identified (RTX 3060, 3090 Ti, 4090, etc.)
- [ ] Correct Dockerfile selected for GPU
- [ ] vLLM parameters adjusted for GPU VRAM
- [ ] Model size appropriate for GPU (7B, 14B, 32B, 72B)
- [ ] `kv-cache-dtype` set to `auto` (not `fp16`)

### Docker Compose Configuration
- [ ] Ports not conflicting with existing services
- [ ] Volume mounts configured correctly
- [ ] Network configuration verified
- [ ] GPU resources allocated to vLLM service
- [ ] Health checks configured for all services

---

## Build and Deployment Checklist

### Initial Build
- [ ] All images built successfully: `docker compose build`
- [ ] No build errors in output
- [ ] vLLM image built with correct Dockerfile
- [ ] All service images built

### First Startup
- [ ] All services started: `docker compose up -d`
- [ ] PostgreSQL container healthy
- [ ] Redis container healthy
- [ ] Kong container healthy
- [ ] Keycloak container healthy
- [ ] vLLM container healthy (may take 2-3 minutes)
- [ ] All application services healthy
- [ ] AI Pipeline container healthy
- [ ] Frontend container healthy

### Service Verification
```bash
# Check all containers
docker compose ps

# Expected: All containers "Up" and "healthy"
```

---

## Testing Checklist

### Infrastructure Tests
- [ ] PostgreSQL accessible: `docker compose exec postgres pg_isready`
- [ ] Redis accessible: `docker compose exec redis redis-cli ping`
- [ ] Kong admin API accessible: `curl http://localhost:8888`

### vLLM Tests
- [ ] vLLM health check passes: `curl http://localhost:8000/health`
- [ ] vLLM model loaded (check logs): `docker compose logs vllm`
- [ ] vLLM completion test passes:
```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
    "prompt": "Hello, how are you?",
    "max_tokens": 50
  }'
```

### Application Tests
- [ ] AI Pipeline health check: `curl http://localhost:3005/health`
- [ ] AI Pipeline test request:
```bash
curl -X POST http://localhost:3005/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Check system status",
    "context": {}
  }'
```
- [ ] Frontend accessible: http://localhost:3100
- [ ] Frontend loads without errors
- [ ] Can submit requests through UI

### Service Integration Tests
- [ ] Asset service accessible through Kong
- [ ] Automation service accessible through Kong
- [ ] Network analyzer accessible through Kong
- [ ] Communication service accessible through Kong
- [ ] Authentication working (if configured)

---

## Performance Checklist

### GPU Utilization
- [ ] GPU memory usage reasonable (check with `nvidia-smi`)
- [ ] No CUDA out of memory errors
- [ ] vLLM using expected amount of VRAM
- [ ] GPU utilization during inference (should spike during requests)

### Response Times
- [ ] vLLM completion time < 5 seconds for short prompts
- [ ] AI Pipeline response time < 10 seconds for simple requests
- [ ] Frontend loads in < 3 seconds
- [ ] No timeout errors

### Resource Usage
- [ ] CPU usage reasonable (< 80% average)
- [ ] RAM usage within limits (< 80% of available)
- [ ] Disk I/O not saturated
- [ ] Network connectivity stable

---

## Documentation Checklist

### Required Documentation Present
- [ ] `README.md` - Project overview
- [ ] `INSTALLATION.md` - Complete installation guide
- [ ] `DEPLOYMENT_CHECKLIST.md` - This file
- [ ] `RTX_3090Ti_SETUP.md` - GPU-specific guide
- [ ] `CLEAN_ARCHITECTURE.md` - Architecture documentation
- [ ] `.env.example` - Environment template

### Documentation Accuracy
- [ ] All URLs in docs match actual configuration
- [ ] All commands tested and working
- [ ] Version numbers up to date
- [ ] Troubleshooting section covers common issues

---

## Backup and Recovery Checklist

### Backup Strategy
- [ ] Database backup strategy defined
- [ ] Volume backup strategy defined
- [ ] Configuration files backed up
- [ ] Backup schedule configured (if automated)
- [ ] Backup restoration tested

### Recovery Procedures
- [ ] Database restore procedure documented
- [ ] Volume restore procedure documented
- [ ] Service restart procedure documented
- [ ] Rollback procedure documented

---

## Security Checklist

### Credentials
- [ ] All default passwords changed
- [ ] JWT secret key changed from default
- [ ] Encryption keys generated (not using defaults)
- [ ] Database password strong and unique
- [ ] Redis password set (if exposed)
- [ ] Keycloak admin password changed

### Network Security
- [ ] Firewall configured (if production)
- [ ] Only necessary ports exposed
- [ ] CORS configured correctly
- [ ] SSL/TLS configured (if production)
- [ ] Kong security plugins configured

### Access Control
- [ ] User authentication working
- [ ] Role-based access control configured
- [ ] API rate limiting configured
- [ ] Audit logging enabled

---

## Production Readiness Checklist

### Monitoring
- [ ] Health checks configured for all services
- [ ] Logging configured and centralized
- [ ] Metrics collection enabled
- [ ] Alerting configured (if production)
- [ ] Dashboard created (if using monitoring stack)

### High Availability
- [ ] Database replication configured (if production)
- [ ] Redis persistence configured
- [ ] Load balancer configured (if production)
- [ ] Backup services configured
- [ ] Disaster recovery plan documented

### Performance Optimization
- [ ] Database indexes optimized
- [ ] Redis cache configured
- [ ] vLLM parameters tuned for workload
- [ ] Connection pooling configured
- [ ] Resource limits set appropriately

---

## Maintenance Checklist

### Regular Maintenance
- [ ] Update schedule defined
- [ ] Backup verification schedule defined
- [ ] Log rotation configured
- [ ] Disk space monitoring configured
- [ ] Security update process defined

### Upgrade Procedures
- [ ] Docker image update procedure documented
- [ ] Database migration procedure documented
- [ ] Service upgrade procedure documented
- [ ] Rollback procedure documented
- [ ] Testing procedure for upgrades defined

---

## Troubleshooting Reference

### Common Issues and Solutions

#### vLLM Won't Start
```bash
# Check logs
docker compose logs vllm

# Common fixes:
# 1. kv-cache-dtype parameter error -> Use "auto" instead of "fp16"
# 2. Out of memory -> Reduce max-model-len or gpu-memory-utilization
# 3. Model download failed -> Pre-download model manually
# 4. GPU not detected -> Verify nvidia-container-toolkit
```

#### Database Connection Errors
```bash
# Check database health
docker compose exec postgres pg_isready

# Restart services
docker compose restart automation asset network communication ai-pipeline
```

#### Port Conflicts
```bash
# Find what's using the port
sudo lsof -i :8000

# Change port in docker-compose.yml
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check GPU usage
nvidia-smi

# Check logs for errors
docker compose logs --tail=100
```

---

## Sign-Off Checklist

### Deployment Complete
- [ ] All services running and healthy
- [ ] All tests passing
- [ ] Documentation complete and accurate
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Security hardened
- [ ] Performance acceptable
- [ ] Team trained on operations

### Handover Complete
- [ ] Operations team trained
- [ ] Documentation reviewed
- [ ] Access credentials shared securely
- [ ] Support contacts documented
- [ ] Escalation procedures defined

---

## Version Control

### Git Repository Status
- [ ] All changes committed
- [ ] Commit messages descriptive
- [ ] Branch pushed to remote
- [ ] Tags created for releases
- [ ] README updated

### Verification Commands
```bash
# Check git status
git status

# Should show: "nothing to commit, working tree clean"

# Check current branch
git branch

# Check remote status
git remote -v

# Check last commit
git log -1
```

---

## Final Verification

Run this comprehensive test to verify everything:

```bash
#!/bin/bash
echo "=== OpsConductor NG Deployment Verification ==="

echo "1. Checking Docker..."
docker --version || exit 1

echo "2. Checking NVIDIA..."
nvidia-smi || exit 1

echo "3. Checking containers..."
docker compose ps

echo "4. Testing vLLM..."
curl -f http://localhost:8000/health || exit 1

echo "5. Testing AI Pipeline..."
curl -f http://localhost:3005/health || exit 1

echo "6. Testing Frontend..."
curl -f http://localhost:3100 || exit 1

echo "7. Testing vLLM completion..."
curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-14B-Instruct-AWQ", "prompt": "Test", "max_tokens": 10}' \
  || exit 1

echo ""
echo "✅ All checks passed! Deployment verified."
```

Save this as `verify-deployment.sh` and run it:
```bash
chmod +x verify-deployment.sh
./verify-deployment.sh
```

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Environment**: _____________  
**Git Commit**: _____________  
**Notes**: _____________
