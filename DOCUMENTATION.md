# OpsConductor NG - Documentation Index

## 📚 Core Documentation

### Getting Started
1. **[README.md](README.md)** - Project overview, features, and quick start
2. **[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)** - Complete deployment instructions
3. **[REPO.md](REPO.md)** - Repository structure and architecture

### Specialized Documentation
- **[docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md](docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md)** - AI scripting standards and best practices
- **[docs/GPU_VFIO_PCI_VM_FIX.md](docs/GPU_VFIO_PCI_VM_FIX.md)** - GPU support in virtualized environments

## 🎯 Quick Navigation

### For New Users
1. Start with [README.md](README.md) for overview
2. Follow [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md) for setup
3. Access web interface at http://localhost:3100

### For Developers
1. Review [REPO.md](REPO.md) for architecture
2. Check [docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md](docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md) for coding standards
3. Use development environment: `docker-compose -f docker-compose.dev.yml up`

### For System Administrators
1. Follow [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md) for production deployment
2. Use monitoring tools: http://localhost:5555 (Celery Flower)
3. Check service health: `./verify-setup.sh`

## 🔧 API Documentation

### Interactive Documentation
- **Kong Gateway**: http://localhost:3000/docs
- **AI Brain**: http://localhost:3005/docs
- **All Services**: Available at `<service-url>/docs`

### Key Endpoints
```
POST /api/v1/ai/chat              - Natural language chat interface
GET  /api/v1/assets               - List infrastructure targets
POST /api/v1/jobs                 - Create automation job
GET  /api/v1/executions           - List job executions
```

## 🚀 Deployment Options

### Standard Deployment
```bash
./deploy.sh
```

### Alternative Deployments
```bash
./deploy-traefik.sh        # With Traefik reverse proxy
./deploy-elk.sh            # With ELK logging stack
./deploy-redis-streams.sh  # With Redis Streams messaging
./start-monitoring.sh      # With Prometheus/Grafana monitoring
```

### GPU Acceleration
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## 🔍 Troubleshooting

### Health Checks
```bash
./verify-setup.sh                    # Complete system verification
docker-compose ps                    # Service status
curl http://localhost:3000/health    # Kong Gateway health
curl http://localhost:3005/health    # AI Brain health
```

### Common Issues
- **Services won't start**: Check `docker-compose logs <service-name>`
- **Database issues**: Verify with `docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "SELECT 1;"`
- **AI not responding**: Check Ollama with `curl http://localhost:11434/api/tags`
- **GPU issues**: See [docs/GPU_VFIO_PCI_VM_FIX.md](docs/GPU_VFIO_PCI_VM_FIX.md)

## 📊 System Information

### Default Access
- **Web Interface**: http://localhost:3100
- **Default Login**: admin / admin123
- **Change password immediately** after first login

### Service Ports
- Kong Gateway: 3000
- Identity Service: 3001
- Asset Service: 3002
- Automation Service: 3003
- Communication Service: 3004
- AI Brain: 3005
- Network Analyzer: 3006
- Keycloak: 8090
- Frontend: 3100
- Ollama: 11434
- ChromaDB: 8000
- Celery Flower: 5555

### Resource Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 20GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB storage
- **Production**: 16GB RAM, 8 CPU cores, 100GB storage

---

**This documentation provides comprehensive coverage of OpsConductor NG. Start with README.md for overview, then follow the appropriate guide based on your needs.**