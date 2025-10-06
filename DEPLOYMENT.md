# OpsConductor NG - October 2025 Release
## Deployment Guide

This document provides complete deployment instructions for the **October 2025 Release** of OpsConductor NG.

## 🎯 Release Information

- **Release Date**: October 2025
- **Version**: October 2025 Release
- **Status**: Production Ready
- **Architecture**: 5-Stage AI Pipeline with Integrated Execution

## ✨ What's Included

### Core Features
- ✅ **5-Stage AI Pipeline**: Complete intent classification, tool selection, planning, response generation, and execution
- ✅ **Asset Management**: Full integration with asset service for infrastructure queries
- ✅ **Execution Engine**: Immediate and scheduled execution with approval workflows
- ✅ **Authentication**: Keycloak-based identity management
- ✅ **API Gateway**: Kong for centralized routing and security
- ✅ **Web Interface**: React TypeScript frontend with real-time updates

### Microservices
- **AI Pipeline Service**: 5-stage LLM-driven decision engine
- **Asset Service**: Infrastructure asset management and queries
- **Automation Service**: Command execution and workflow management
- **Network Analyzer Service**: Network monitoring and analysis
- **Communication Service**: Notifications and alerts

### Infrastructure
- **PostgreSQL 17**: Multi-schema database for all services
- **Redis 7**: Message queue and caching
- **Ollama 0.11**: Local LLM server with GPU acceleration
- **Kong 3.4**: API Gateway
- **Keycloak 22**: Identity provider

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **CPU**: 4+ cores recommended
- **RAM**: 16GB minimum, 32GB recommended
- **Disk**: 50GB free space minimum
- **GPU**: Optional but recommended for better LLM performance

### Software Requirements
- **Docker**: 24.0+ with Docker Compose V2
- **Git**: For cloning the repository
- **Network**: Internet access for initial setup

## 🚀 Fresh Deployment Instructions

### Step 1: Clone the Repository

```bash
git clone https://github.com/andrewcho-dev/opsconductor-ng.git
cd opsconductor-ng
```

### Step 2: Verify Repository State

```bash
# Check you're on the main branch
git branch

# Verify you have the October 2025 release
git log --oneline -1
```

### Step 3: Start the System

```bash
# Start all services
docker compose up -d

# This will:
# - Pull all required Docker images
# - Build custom service images
# - Initialize databases
# - Configure Keycloak
# - Start all microservices
```

### Step 4: Wait for Services to Initialize

```bash
# Monitor startup progress
docker compose logs -f

# Wait for these key messages:
# - "Keycloak started"
# - "AI Pipeline ready"
# - "Asset Service ready"
# - "Frontend ready"

# Check service health (wait until all are healthy)
docker compose ps
```

**Expected startup time**: 2-5 minutes depending on system resources

### Step 5: Verify Deployment

```bash
# Check all containers are running
docker compose ps

# Expected output: All services should show "Up" status
# - opsconductor-ai-pipeline (healthy)
# - opsconductor-assets (healthy)
# - opsconductor-automation (healthy)
# - opsconductor-network (healthy)
# - opsconductor-communication (healthy)
# - opsconductor-frontend (Up)
# - opsconductor-postgres (healthy)
# - opsconductor-redis (healthy)
# - opsconductor-ollama (healthy)
# - opsconductor-kong (healthy)
# - opsconductor-keycloak (healthy)
```

### Step 6: Access the System

#### Web Interface
- **URL**: http://localhost:3100
- **Username**: `admin`
- **Password**: `admin123`

#### API Endpoints
- **AI Pipeline**: http://localhost:3005
- **Kong Gateway**: http://localhost:3000
- **Keycloak Admin**: http://localhost:8090

### Step 7: Test the System

1. **Login to Web Interface**
   - Navigate to http://localhost:3100
   - Login with admin/admin123

2. **Test Asset Query**
   - Type: "Show me all assets"
   - Expected: List of 7 assets with details

3. **Test Execution**
   - The system will automatically execute the query
   - Results should appear within 30 seconds

## 🔧 Configuration

### Default Credentials

**Frontend/API Access**:
- Username: `admin`
- Password: `admin123`

**Keycloak Admin Console**:
- URL: http://localhost:8090
- Username: `admin`
- Password: `OpsConductor2024!`

**PostgreSQL Database**:
- Host: `localhost:5432`
- Username: `postgres`
- Password: `postgres`
- Databases: `ai_pipeline`, `asset_service`, `automation_service`, `network_analyzer`, `communication_service`

### Environment Variables

All services use environment variables defined in `docker-compose.yml`. Key variables:

- `OLLAMA_BASE_URL`: http://ollama:11434
- `DATABASE_URL`: PostgreSQL connection strings
- `REDIS_URL`: redis://redis:6379
- `KEYCLOAK_URL`: http://keycloak:8080

## 📊 Service Ports

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Frontend | 3000 | 3100 | Web UI |
| AI Pipeline | 3005 | 3005 | Pipeline API |
| Asset Service | 3002 | - | Internal only |
| Automation Service | 3003 | - | Internal only |
| Network Analyzer | 3004 | - | Internal only |
| Communication Service | 3006 | - | Internal only |
| Kong Gateway | 8000 | 3000 | API Gateway |
| Keycloak | 8080 | 8090 | Identity Provider |
| PostgreSQL | 5432 | 5432 | Database |
| Redis | 6379 | 6379 | Cache/Queue |
| Ollama | 11434 | 11434 | LLM Server |

## 🛠️ Maintenance

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ai-pipeline

# Last 100 lines
docker compose logs --tail=100 ai-pipeline
```

### Restarting Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart ai-pipeline

# Rebuild and restart after code changes
docker compose up -d --build ai-pipeline
```

### Stopping the System

```bash
# Stop all services (preserves data)
docker compose stop

# Stop and remove containers (preserves volumes)
docker compose down

# Complete cleanup (removes volumes - DATA LOSS!)
docker compose down -v
```

### Database Backup

```bash
# Backup all databases
docker exec opsconductor-postgres pg_dumpall -U postgres > backup.sql

# Restore from backup
docker exec -i opsconductor-postgres psql -U postgres < backup.sql
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check Docker daemon
docker info

# Check disk space
df -h

# Check logs for errors
docker compose logs
```

### Frontend Not Loading

```bash
# Check frontend logs
docker compose logs frontend

# Verify frontend is running
curl http://localhost:3100

# Rebuild frontend
docker compose up -d --build frontend
```

### AI Pipeline Errors

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check AI Pipeline logs
docker compose logs ai-pipeline

# Restart AI Pipeline
docker compose restart ai-pipeline
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test database connection
docker exec opsconductor-postgres psql -U postgres -c "SELECT version();"

# Check database logs
docker compose logs postgres
```

### Authentication Issues

```bash
# Check Keycloak is running
docker compose ps keycloak

# Access Keycloak admin console
# http://localhost:8090 (admin/OpsConductor2024!)

# Restart Keycloak
docker compose restart keycloak
```

## 🔄 Updating the System

### Pulling Latest Changes

```bash
# Pull latest code
git pull origin main

# Rebuild and restart services
docker compose up -d --build

# Check for any migration scripts
ls -la migrations/
```

### Rolling Back

```bash
# Stop current version
docker compose down

# Checkout previous version
git checkout <previous-commit-hash>

# Rebuild and start
docker compose up -d --build
```

## 📈 Performance Tuning

### Ollama GPU Acceleration

If you have an NVIDIA GPU:

```bash
# Verify GPU is available
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Ollama will automatically use GPU if available
```

### Database Optimization

```bash
# Connect to PostgreSQL
docker exec -it opsconductor-postgres psql -U postgres

# Run VACUUM ANALYZE on all databases
VACUUM ANALYZE;
```

### Redis Memory Management

```bash
# Check Redis memory usage
docker exec opsconductor-redis redis-cli INFO memory

# Clear cache if needed
docker exec opsconductor-redis redis-cli FLUSHDB
```

## 🔐 Security Considerations

### Production Deployment

For production deployments, you should:

1. **Change Default Passwords**
   - Update Keycloak admin password
   - Update PostgreSQL password
   - Update frontend admin password

2. **Enable HTTPS**
   - Configure SSL certificates in Kong
   - Update frontend to use HTTPS

3. **Network Security**
   - Use Docker networks to isolate services
   - Configure firewall rules
   - Limit external port exposure

4. **Secrets Management**
   - Use Docker secrets or external secret managers
   - Never commit secrets to git

## 📞 Support

For issues or questions:
- Check logs: `docker compose logs`
- Review documentation in the repository
- Check GitHub issues

## 📝 Release Notes

### October 2025 Release

**New Features**:
- ✅ Complete 5-stage AI pipeline with integrated execution
- ✅ Asset service integration with real-time queries
- ✅ Execution engine with immediate and scheduled modes
- ✅ Approval workflow system
- ✅ UUID-based request tracing
- ✅ Step type recognition for multiple tool variants

**Bug Fixes**:
- Fixed UUID validation in execution requests
- Fixed step type recognition for asset-list queries
- Fixed result retrieval for immediate executions
- Fixed step_results storage in execution responses

**Improvements**:
- Enhanced error handling in execution engine
- Improved logging throughout the pipeline
- Better frontend error messages
- Optimized database queries

**Known Issues**:
- None at release time

---

**OpsConductor NG October 2025 Release - Production Ready**