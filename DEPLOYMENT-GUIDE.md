# 🚀 OpsConductor NG - Complete Deployment Guide

## 📋 Overview

This comprehensive guide covers deploying OpsConductor NG, a production-ready AI-powered IT operations automation platform with microservices architecture.

## 🎯 What You're Deploying

### Core Platform
- **11 Microservices** - API Gateway, Identity, Asset, Automation, Communication, AI services
- **AI Capabilities** - Natural language processing, intent classification, workflow generation
- **Infrastructure** - PostgreSQL, Redis, ChromaDB, Ollama, Nginx
- **Frontend** - React TypeScript web interface
- **Workers** - Celery-based distributed task processing

### Key Features
- 🧠 **AI-Powered Interface** - Natural language commands
- 🏗️ **Microservices Architecture** - Scalable, maintainable design
- 🔧 **Multi-Protocol Automation** - SSH, RDP, SNMP, HTTP, PowerShell
- 📊 **Real-Time Monitoring** - Comprehensive infrastructure visibility
- 🛡️ **Enterprise Security** - RBAC, audit logging, encrypted credentials

## 🔧 Prerequisites

### System Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 20GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB storage
- **Production**: 16GB RAM, 8 CPU cores, 100GB storage

### Software Requirements
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for repository cloning
- **curl** for testing (optional)

### Optional Requirements
- **NVIDIA GPU** with Docker GPU support for enhanced AI performance
- **SSL Certificates** for production HTTPS deployment

## 🚀 Quick Start Deployment

### One-Command Deployment
```bash
# Clone repository
git clone <repository-url>
cd opsconductor-ng

# Automated deployment
./deploy.sh
```

**Access the platform:**
- **Web Interface**: http://localhost:3100
- **API Gateway**: http://localhost:3000
- **Default Login**: admin / admin123

### Manual Deployment Steps

#### Step 1: Clone and Prepare
```bash
git clone <repository-url>
cd opsconductor-ng

# Copy environment template
cp .env.example .env

# Review and customize environment variables
nano .env
```

#### Step 2: Build Services
```bash
# Build all services
./build.sh

# Or build manually
docker-compose build
```

#### Step 3: Deploy Infrastructure
```bash
# Start infrastructure services first
docker-compose up -d postgres redis chromadb

# Wait for services to be ready
docker-compose logs -f postgres
# Wait for "database system is ready to accept connections"
```

#### Step 4: Deploy Core Services
```bash
# Start core services
docker-compose up -d api-gateway identity-service asset-service automation-service communication-service

# Check service health
docker-compose ps
```

#### Step 5: Deploy AI Services
```bash
# Start AI infrastructure
docker-compose up -d ollama

# Pull AI models (this may take time)
docker-compose exec ollama ollama pull llama2:latest

# Start AI services
docker-compose up -d ai-brain

# Check AI service health
curl http://localhost:3005/health
```

#### Step 6: Deploy Frontend and Proxy
```bash
# Start frontend and nginx
docker-compose up -d frontend nginx

# Verify complete deployment
docker-compose ps
```

## 🔍 Verification and Testing

### Health Check Script
```bash
# Run automated verification
./verify-setup.sh
```

### Manual Health Checks
```bash
# Check all services
docker-compose ps

# Individual service health
curl http://localhost:3000/health  # API Gateway
curl http://localhost:3001/health  # Identity Service
curl http://localhost:3002/health  # Asset Service
curl http://localhost:3003/health  # Automation Service
curl http://localhost:3004/health  # Communication Service
curl http://localhost:3005/health  # AI Command Service
curl http://localhost:3007/health  # Vector Service
curl http://localhost:3008/health  # LLM Service
curl http://localhost:3010/health  # AI Orchestrator

# Infrastructure health
curl http://localhost:8000/api/v1/heartbeat  # ChromaDB
curl http://localhost:11434/api/tags         # Ollama
```

### Database Verification
```bash
# Check database schemas
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name IN ('identity', 'assets', 'automation', 'communication');"

# Check table counts
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT schemaname, COUNT(*) as table_count 
FROM pg_tables 
WHERE schemaname IN ('identity', 'assets', 'automation', 'communication') 
GROUP BY schemaname;"
```

### AI System Testing
```bash
# Test AI chat interface
curl -X POST http://localhost:3005/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me all servers", "user_id": 1}'

# Test vector search
curl -X POST http://localhost:3007/vector/search \
  -H "Content-Type: application/json" \
  -d '{"query": "server management", "limit": 3}'

# Test LLM generation
curl -X POST http://localhost:3008/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain Docker containers", "model": "llama2:latest"}'
```

## 🎮 First Steps After Deployment

### 1. Initial Login
- Navigate to http://localhost:3100
- Login with: **admin** / **admin123**
- **Change password immediately**

### 2. Create Your First Asset
```bash
curl -X POST http://localhost:3000/api/v1/assets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{
    "name": "web-server-01",
    "hostname": "web-server-01.local",
    "ip_address": "192.168.1.100",
    "description": "Production web server",
    "service_type": "ssh",
    "port": 22,
    "os_type": "linux",
    "credential_type": "username_password",
    "username": "admin",
    "password_encrypted": "encrypted-password"
  }'
```

### 3. Test AI Functionality
- Use the chat interface: "show me all my servers"
- Try automation: "restart nginx on web servers"
- Test job creation: "check disk space on all Linux servers"

### 4. Create Additional Users
- Navigate to Identity Management
- Create users with appropriate roles
- Test RBAC functionality

## 🔧 Advanced Deployment Options

### GPU Acceleration
```bash
# Deploy with GPU support for enhanced AI performance
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# Verify GPU access
docker exec opsconductor-ai-brain nvidia-smi
```

### Production SSL Configuration
```bash
# Place SSL certificates
mkdir -p ssl/
cp your-cert.crt ssl/nginx.crt
cp your-key.key ssl/nginx.key

# Update nginx configuration for SSL
# Edit nginx/nginx.conf for your domain

# Deploy with SSL
docker-compose up -d nginx
```

### Scaling Workers
```bash
# Scale automation workers
docker-compose up -d --scale automation-worker-1=3 --scale automation-worker-2=2

# Scale AI services
docker-compose up -d --scale ai-brain=2
```

### Custom Environment Configuration
```bash
# Edit environment variables
nano .env

# Key variables to customize:
# - Database passwords
# - JWT secret keys
# - SMTP settings
# - Service URLs
# - AI model preferences

# Apply changes
docker-compose down
docker-compose up -d
```

## 📊 Monitoring and Maintenance

### Service Monitoring
```bash
# View service logs
docker-compose logs -f <service-name>

# Monitor resource usage
docker stats

# Check service dependencies
docker-compose config --services
```

### Database Maintenance
```bash
# Database backup
docker exec opsconductor-postgres pg_dump -U postgres opsconductor > backup-$(date +%Y%m%d).sql

# Database restore
docker exec -i opsconductor-postgres psql -U postgres opsconductor < backup.sql

# Check database size
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT pg_size_pretty(pg_database_size('opsconductor'));"
```

### AI Model Management
```bash
# List available models
curl http://localhost:11434/api/tags

# Pull new models
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "codellama:latest"}'

# Remove unused models
curl -X DELETE http://localhost:11434/api/delete \
  -H "Content-Type: application/json" \
  -d '{"name": "old-model:tag"}'
```

### Performance Monitoring
- **Celery Flower**: http://localhost:5555 (admin/admin123)
- **Service Health**: All services provide `/health` endpoints
- **Database Metrics**: Available through PostgreSQL queries
- **AI Performance**: Response times and accuracy metrics

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
docker-compose logs <service-name>

# Check dependencies
docker-compose ps

# Restart specific service
docker-compose restart <service-name>

# Rebuild and restart
docker-compose up -d --build <service-name>
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Test connection
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "SELECT 1;"

# Reset database (WARNING: Data loss)
docker-compose down -v
docker-compose up -d postgres
```

#### AI Services Not Responding
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check ChromaDB status
curl http://localhost:8000/api/v1/heartbeat

# Restart AI services
docker-compose restart ai-brain

# Check GPU access (if using GPU)
docker exec opsconductor-ai-brain nvidia-smi
```

#### Frontend Not Loading
```bash
# Check frontend logs
docker-compose logs frontend

# Check nginx logs
docker-compose logs nginx

# Verify API Gateway
curl http://localhost:3000/health

# Rebuild frontend
docker-compose up -d --build frontend
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Scale workers
docker-compose up -d --scale automation-worker-1=3

# Optimize database
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "VACUUM ANALYZE;"

# Clear Redis cache
docker exec opsconductor-redis redis-cli FLUSHALL
```

## 🔄 Updates and Upgrades

### Updating Services
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart specific service
docker-compose up -d --build <service-name>

# Full system update
docker-compose down
docker-compose build
docker-compose up -d
```

### Database Migrations
```bash
# Check for new migrations
ls database/migrations/

# Apply migrations manually if needed
docker exec -i opsconductor-postgres psql -U postgres opsconductor < database/migrations/new-migration.sql
```

## 📚 Additional Resources

### Documentation
- **[README.md](README.md)** - Main project overview
- **[REPO.md](REPO.md)** - Repository structure
- **[AI_DOCUMENTATION.md](AI_DOCUMENTATION.md)** - AI system details
- **[VOLUME_MOUNT_SYSTEM.md](VOLUME_MOUNT_SYSTEM.md)** - Volume configuration

### API Documentation
- **API Gateway**: http://localhost:3000/docs
- **AI Command Service**: http://localhost:3005/docs
- **All Services**: Available at `<service-url>/docs`

### Support and Community
- **Issues**: Report bugs and feature requests
- **Discussions**: Community support and questions
- **Documentation**: Comprehensive guides and tutorials

---

**🎉 Congratulations! You've successfully deployed OpsConductor NG. Start automating your IT operations with AI-powered natural language commands!**