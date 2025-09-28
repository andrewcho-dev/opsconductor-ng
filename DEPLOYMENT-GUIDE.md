# 🚀 OpsConductor NG - Deployment Guide

## 📋 Overview

Complete deployment guide for OpsConductor NG, a production-ready AI-powered IT operations automation platform with microservices architecture.

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
- **Web Interface**: http://YOUR_HOST_IP:3100 (deployment script will show correct IP)
- **API Gateway**: http://YOUR_HOST_IP:3000 (deployment script will show correct IP)
- **Default Login**: admin / admin123

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

# Individual service health (replace YOUR_HOST_IP with actual host IP)
curl http://YOUR_HOST_IP:3000/health  # Kong Gateway
curl http://YOUR_HOST_IP:3005/health  # AI Brain
curl http://YOUR_HOST_IP:8090/health  # Keycloak
curl http://YOUR_HOST_IP:3001/health  # Identity Service
curl http://YOUR_HOST_IP:3002/health  # Asset Service
curl http://YOUR_HOST_IP:3003/health  # Automation Service
curl http://YOUR_HOST_IP:3004/health  # Communication Service
curl http://YOUR_HOST_IP:3006/health  # Network Analyzer

# Infrastructure health (replace YOUR_HOST_IP with actual host IP)
curl http://YOUR_HOST_IP:8000/api/v1/heartbeat  # ChromaDB
curl http://YOUR_HOST_IP:11434/api/tags         # Ollama
```

### Database Verification
```bash
# Check database schemas
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name IN ('identity', 'assets', 'automation', 'communication', 'network_analysis');"

# Check table counts
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "
SELECT schemaname, COUNT(*) as table_count 
FROM pg_tables 
WHERE schemaname IN ('identity', 'assets', 'automation', 'communication', 'network_analysis') 
GROUP BY schemaname;"
```

### AI System Testing
```bash
# Test AI chat interface (replace YOUR_HOST_IP with actual host IP)
curl -X POST http://YOUR_HOST_IP:3005/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me all servers", "user_id": 1}'

# Test Ollama LLM (replace YOUR_HOST_IP with actual host IP)
curl -X POST http://YOUR_HOST_IP:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama:7b", "prompt": "Explain Docker containers", "stream": false}'
```

## 🎮 First Steps After Deployment

### 1. Initial Login
- Navigate to http://YOUR_HOST_IP:3100 (deployment script will show correct IP)
- Login with: **admin** / **admin123**
- **Change password immediately**

### 2. Create Your First Asset
```bash
curl -X POST http://YOUR_HOST_IP:3000/api/v1/assets \
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
- Try automation: "restart apache on web servers"
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

### Alternative Deployment Methods
```bash
# With Traefik reverse proxy
./deploy-traefik.sh

# With ELK logging stack
./deploy-elk.sh

# With Redis Streams messaging
./deploy-redis-streams.sh

# With monitoring stack (Prometheus/Grafana)
./start-monitoring.sh
```

### Production SSL Configuration
```bash
# SSL is handled by Kong Gateway
# Configure SSL certificates in Kong:
# 1. Upload certificates via Kong Admin API
# 2. Configure SSL termination in Kong
# 3. Update Kong routes for HTTPS

# Example Kong SSL configuration:
curl -X POST http://kong:8001/certificates \
  -F "cert=@your-cert.crt" \
  -F "key=@your-key.key"
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
# List available models (replace YOUR_HOST_IP with actual host IP)
curl http://YOUR_HOST_IP:11434/api/tags

# Pull new models (replace YOUR_HOST_IP with actual host IP)
curl -X POST http://YOUR_HOST_IP:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "codellama:latest"}'

# Remove unused models (replace YOUR_HOST_IP with actual host IP)
curl -X DELETE http://YOUR_HOST_IP:11434/api/delete \
  -H "Content-Type: application/json" \
  -d '{"name": "old-model:tag"}'
```

### Performance Monitoring
- **Celery Flower**: http://YOUR_HOST_IP:5555 (admin/admin123) - deployment script will show correct IP
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
# Check Ollama status (replace YOUR_HOST_IP with actual host IP)
curl http://YOUR_HOST_IP:11434/api/tags

# Check ChromaDB status (replace YOUR_HOST_IP with actual host IP)
curl http://YOUR_HOST_IP:8000/api/v1/heartbeat

# Restart AI services
docker-compose restart ai-brain

# Check GPU access (if using GPU)
docker exec opsconductor-ai-brain nvidia-smi
```

#### Frontend Not Loading
```bash
# Check frontend logs
docker-compose logs frontend

# Verify Kong Gateway (replace YOUR_HOST_IP with actual host IP)
curl http://YOUR_HOST_IP:3000/health

# Rebuild frontend
docker-compose up -d --build frontend
```

#### Keycloak Authentication Issues
```bash
# Check Keycloak status (replace YOUR_HOST_IP with actual host IP)
curl http://YOUR_HOST_IP:8090/health

# Check Keycloak logs
docker-compose logs keycloak

# Verify realm configuration (replace YOUR_HOST_IP with actual host IP)
curl http://YOUR_HOST_IP:8090/realms/opsconductor/.well-known/openid_configuration
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
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d

# Update specific service
docker-compose up -d --no-deps <service-name>
```

### Backup Before Updates
```bash
# Backup database
docker exec opsconductor-postgres pg_dump -U postgres opsconductor > backup-pre-update.sql

# Backup volumes
docker run --rm -v opsconductor-postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-data-backup.tar.gz /data
```

## 📋 Production Checklist

### Security
- [ ] Change default admin password
- [ ] Configure SSL certificates
- [ ] Set up proper firewall rules
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerting

### Performance
- [ ] Configure resource limits
- [ ] Set up log rotation
- [ ] Configure database optimization
- [ ] Set up caching strategy
- [ ] Configure load balancing

### Monitoring
- [ ] Set up health checks
- [ ] Configure log aggregation
- [ ] Set up performance monitoring
- [ ] Configure alerting rules
- [ ] Set up backup verification

---

**For additional help, see [README.md](README.md) for overview and [REPO.md](REPO.md) for architecture details.**