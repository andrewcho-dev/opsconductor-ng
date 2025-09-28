# OpsConductor NG - AI-Powered Infrastructure Automation Platform

**Production-Ready IT Operations with Pure LLM-Driven Intelligence**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](https://github.com/opsconductor/opsconductor-ng)
[![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue.svg)](#architecture)
[![AI Powered](https://img.shields.io/badge/AI-Pure%20LLM-purple.svg)](#ai-capabilities)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Quick Start

### One-Command Deployment
```bash
git clone <repository-url>
cd opsconductor-ng
./deploy.sh
```

**Access the platform:**
- **Web Interface**: http://YOUR_HOST_IP:3100 (replace YOUR_HOST_IP with your actual server IP)
- **Default Login**: admin / admin123

> **Note**: Replace `localhost` with your actual server IP address in all URLs below. The deployment scripts will show you the correct IP address to use.

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM recommended
- **Optional**: NVIDIA GPU for enhanced AI performance

---

## 🎯 What is OpsConductor?

OpsConductor NG is a **production-ready, microservices-based IT operations automation platform** powered by pure LLM intelligence. It transforms complex infrastructure management into simple natural language conversations using advanced AI orchestration.

### Key Features

- 🧠 **Pure LLM Architecture** - No hardcoded logic, all decisions made by AI
- 🏗️ **Enterprise Microservices** - Kong Gateway, Keycloak identity, scalable design
- 🔧 **Multi-Protocol Automation** - SSH, RDP, SNMP, HTTP, PowerShell, and more
- 📊 **Real-Time Monitoring** - Comprehensive infrastructure visibility
- 🤖 **Intelligent Workflows** - AI-generated automation scripts
- 🛡️ **Enterprise Security** - RBAC, audit logging, encrypted credentials
- 📈 **Scalable Design** - Horizontal scaling with load balancing

---

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │◄──►│   Kong Gateway  │◄──►│ AI Brain        │
│   (React/TS)    │    │   (Port 3000)   │    │ (Pure LLM)      │
│   Port 3100     │    │                 │    │ Port 3005       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Keycloak       │    │  Asset Service  │    │  Automation     │
│  Identity       │    │  (Targets)      │    │  Service        │
│  Port 8090      │    │  Port 3002      │    │  Port 3003      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Communication   │    │ Network Analyzer│    │  Ollama LLM     │
│ Service         │    │ Service         │    │  Server         │
│ Port 3004       │    │ Port 3006       │    │  Port 11434     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Services

#### Infrastructure Services
- **PostgreSQL** (Port 5432) - Primary database with 5 schemas
- **Redis** (Port 6379) - Caching, sessions, and message streams
- **ChromaDB** (Port 8000) - Vector database for AI knowledge

#### Application Services
- **Kong Gateway** (Port 3000) - Enterprise API gateway with OAuth2
- **Keycloak** (Port 8090) - Enterprise identity and access management
- **Identity Service** (Port 3001) - User management with Keycloak integration
- **Asset Service** (Port 3002) - Infrastructure targets with embedded credentials
- **Automation Service** (Port 3003) - Job execution with Celery workers
- **Communication Service** (Port 3004) - Notifications and audit logging
- **Network Analyzer Service** (Port 3006) - Network monitoring and analysis

#### AI Services
- **AI Brain** (Port 3005) - Pure LLM-driven intelligence with Ollama integration
- **Ollama Server** (Port 11434) - Local LLM model serving (CodeLLama 7B)
- **ChromaDB** (Port 8000) - Vector database for knowledge storage

---

## 🧠 AI Capabilities

### Pure LLM Architecture
Transform complex operations into simple conversations with no hardcoded logic:

```bash
"Check CPU usage on all Linux servers"
"Restart apache service on web servers"
"Show disk space alerts from last 24 hours"
"Create a PowerShell script to restart IIS"
"Schedule weekly disk cleanup on Windows servers"
```

### Intelligent Features
- **Intent Brain** - Pure LLM-based intent understanding
- **Fulfillment Engine** - Direct execution of user requests
- **Direct Executor** - Ollama-driven service orchestration
- **Service Catalog** - Dynamic service discovery
- **Context Awareness** - Maintains conversation history
- **Learning System** - Continuously improves from interactions

---

## 🗄️ Database Architecture

### Five-Schema Design
- **identity** - Users, roles, permissions, sessions (integrated with Keycloak)
- **assets** - Consolidated targets with embedded credentials
- **automation** - Jobs, executions, schedules, workflows
- **communication** - Notifications, templates, audit logs
- **network_analysis** - Network monitoring and diagnostics

### Key Features
- **Enhanced Targets** - New architecture with embedded credentials
- **Hierarchical Groups** - 3-level target organization
- **Service Definitions** - 31+ predefined service types
- **Comprehensive RBAC** - Enterprise-grade role-based access control
- **Audit Logging** - Complete system operation tracking

---

## 🚀 Deployment

### Automated Deployment
```bash
# Complete system setup
./build.sh      # Build all services
./deploy.sh     # Deploy and initialize database
./verify-setup.sh  # Verify deployment

# GPU acceleration (optional)
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

### Alternative Deployments
```bash
# With Traefik reverse proxy
./deploy-traefik.sh

# With ELK logging stack
./deploy-elk.sh

# With Redis Streams messaging
./deploy-redis-streams.sh

# With monitoring stack
./start-monitoring.sh
```

### Health Monitoring
```bash
# Check all services
docker-compose ps

# Individual health checks
curl http://$(hostname -I | awk '{print $1}'):3000/health  # Kong Gateway
curl http://$(hostname -I | awk '{print $1}'):3005/health  # AI Brain
curl http://$(hostname -I | awk '{print $1}'):5555         # Celery Flower Dashboard
```

---

## 🔒 Security

### Enterprise Identity Management
- **Keycloak Integration** - Enterprise-grade identity and access management
- **OAuth2/OpenID Connect** - Secure token-based authentication
- **Role-based Access Control** - Fine-grained permissions
- **Multi-factor Authentication** - Enhanced security options

### Data Protection
- **Fernet Encryption** - Sensitive credential encryption
- **TLS/SSL Support** - Encrypted communication
- **Input Validation** - Comprehensive data sanitization
- **Audit Logging** - Complete operation tracking

### Default Credentials
- **Username**: admin
- **Password**: admin123
- **Change immediately** after first login

---

## 📊 API Reference

### AI Endpoints
```
POST /api/v1/ai/chat              - Natural language chat interface
POST /api/v1/ai/create-job        - Create automation jobs from text
POST /api/v1/ai/analyze           - Analyze text and generate insights
GET  /api/v1/ai/capabilities      - Get AI system capabilities
```

### Core Operations
```
GET  /api/v1/assets               - List infrastructure targets
POST /api/v1/assets               - Create new target
POST /api/v1/jobs                 - Create automation job
POST /api/v1/jobs/{id}/execute    - Execute job
GET  /api/v1/executions           - List job executions
```

### Interactive Documentation
- **Kong Gateway**: http://YOUR_HOST_IP:3000/docs
- **AI Brain**: http://YOUR_HOST_IP:3005/docs
- **All Services**: Available at `<service-url>/docs`

*Replace YOUR_HOST_IP with your actual host IP address*

---

## 🧪 Testing

### Automated Testing
```bash
# AI system tests
python test_ai_microservices.py

# Service-specific tests
pytest tests/

# Integration tests
python test_frontend_integration.py
```

### Manual Testing
```bash
# Test AI chat
curl -X POST http://$(hostname -I | awk '{print $1}'):3005/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "restart apache on web servers", "user_id": 1}'
```

---

## 🛠️ Development

### Development Setup
```bash
# Development environment with hot reload
docker-compose -f docker-compose.dev.yml up

# Install development dependencies
pip install -r requirements-dev.txt
```

### Code Structure
```
opsconductor-ng/
├── ai-brain/                # Pure LLM-driven AI service
├── kong/                    # Kong Gateway configuration
├── keycloak/                # Keycloak identity management
├── identity-service/        # User management
├── asset-service/           # Infrastructure targets
├── automation-service/      # Job execution
├── communication-service/   # Notifications
├── network-analyzer-service/# Network monitoring
├── frontend/                # React TypeScript web interface
├── database/                # Complete schema and migrations
├── shared/                  # Common utilities
└── scripts/                 # Deployment and utility scripts
```

---

## 📈 Performance & Monitoring

### Performance Metrics
- **Response Time**: < 3 seconds for AI queries
- **Throughput**: 100+ concurrent operations
- **Availability**: 99.9% uptime target
- **AI Accuracy**: 95%+ intent detection accuracy

### Resource Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 20GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB storage
- **Production**: 16GB RAM, 8 CPU cores, 100GB storage
- **GPU**: Optional NVIDIA GPU for enhanced AI performance

### Monitoring Tools
- **Celery Flower**: http://YOUR_HOST_IP:5555 (admin/admin123)
- **Health Checks**: All services provide `/health` endpoints
- **Audit Logs**: Complete operation tracking in database

---

## 🚨 Troubleshooting

### Common Issues

#### Service Startup
```bash
# Check service logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>

# Rebuild and restart
docker-compose up -d --build <service-name>
```

#### Database Issues
```bash
# Check database connection
docker-compose exec postgres psql -U postgres -d opsconductor -c "SELECT 1;"

# Reset database (WARNING: Data loss)
docker-compose down -v
docker-compose up -d postgres
```

#### AI Service Issues
```bash
# Test AI service health
curl http://$(hostname -I | awk '{print $1}'):3005/health

# Check Ollama models
curl http://$(hostname -I | awk '{print $1}'):11434/api/tags

# Verify ChromaDB
curl http://$(hostname -I | awk '{print $1}'):8000/api/v1/heartbeat
```

---

## 🎯 Use Cases

### IT Operations Teams
- **Infrastructure Monitoring** - Real-time system health
- **Automated Remediation** - Self-healing capabilities
- **Incident Response** - Rapid problem resolution
- **Capacity Planning** - Predictive resource management

### DevOps Engineers
- **CI/CD Integration** - Automated workflows
- **Configuration Management** - Consistent infrastructure
- **Security Compliance** - Automated scanning
- **Performance Optimization** - Continuous monitoring

### System Administrators
- **Daily Operations** - Streamlined maintenance
- **Emergency Response** - Quick system access
- **Documentation** - Automated procedure tracking
- **Training** - Interactive learning interface

---

## 📚 Additional Documentation

- **[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)** - Complete deployment instructions
- **[REPO.md](REPO.md)** - Repository structure and architecture
- **[docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md](docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md)** - Development standards

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**OpsConductor NG: Where Infrastructure Meets Intelligence**