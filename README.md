# OpsConductor NG - Intelligent Infrastructure Automation Platform

**Production-Ready IT Operations with AI-Powered Microservices Architecture**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](https://github.com/opsconductor/opsconductor-ng)
[![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue.svg)](#architecture)
[![AI Powered](https://img.shields.io/badge/AI-Powered-purple.svg)](#ai-capabilities)
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
- **Web Interface**: http://localhost:3100
- **Default Login**: admin / admin123

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM recommended
- **Optional**: NVIDIA GPU for enhanced AI performance

---

## 🎯 What is OpsConductor?

OpsConductor NG is a **production-ready, microservices-based IT operations automation platform** that transforms complex infrastructure management into simple natural language conversations. Built with modern AI capabilities, it provides comprehensive automation, monitoring, and intelligent workflow generation.

### Key Features

- 🧠 **AI-Powered Interface** - Natural language commands for all operations
- 🏗️ **Microservices Architecture** - Scalable, maintainable service design
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
│   Web Frontend  │◄──►│   API Gateway   │◄──►│ AI Command      │
│   (React/TS)    │    │   (FastAPI)     │    │ Service         │
│   Port 3100     │    │   Port 3000     │    │ Port 3005       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Identity       │    │  Asset Service  │    │  Automation     │
│  Service        │    │  (Targets)      │    │  Service        │
│  Port 3001      │    │  Port 3002      │    │  Port 3003      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Communication   │    │  Vector Service │    │   LLM Service   │
│ Service         │    │  (ChromaDB)     │    │   (Ollama)      │
│ Port 3004       │    │  Port 3007      │    │  Port 3008      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Services

#### Infrastructure Services
- **PostgreSQL** (Port 5432) - Primary database with 4 schemas
- **Redis** (Port 6379) - Caching, sessions, and task queues
- **ChromaDB** (Port 8000) - Vector database for AI knowledge
- **Nginx** (Port 80/443) - Reverse proxy and SSL termination

#### Application Services
- **API Gateway** (Port 3000) - Central routing, authentication, rate limiting
- **Identity Service** (Port 3001) - User management, RBAC, JWT authentication
- **Asset Service** (Port 3002) - Infrastructure targets with embedded credentials
- **Automation Service** (Port 3003) - Job execution with Celery workers
- **Communication Service** (Port 3004) - Notifications, audit logging

#### AI Services
- **AI Command Service** (Port 3005) - Main AI interface with intent classification
- **Vector Service** (Port 3007) - Knowledge storage and semantic search
- **LLM Service** (Port 3008) - Large language model interface
- **AI Orchestrator** (Port 3010) - AI workflow coordination
- **Ollama Server** (Port 11434) - Local LLM model serving

---

## 🧠 AI Capabilities

### Natural Language Processing
Transform complex operations into simple conversations:

```bash
\"Check CPU usage on all Linux servers\"
\"Restart nginx service on web servers\"
\"Show disk space alerts from last 24 hours\"
\"Create a PowerShell script to restart IIS\"
\"Schedule weekly disk cleanup on Windows servers\"
```

### Intelligent Features
- **Intent Classification** - Understands user intentions with high accuracy
- **Entity Extraction** - Identifies targets, operations, and parameters
- **Context Awareness** - Maintains conversation history
- **Script Generation** - Creates production-ready automation scripts
- **Learning System** - Continuously improves from interactions
- **Predictive Analytics** - Proactive issue detection

---

## 🗄️ Database Architecture

### Four-Schema Design
- **identity** - Users, roles, permissions, sessions (5 tables)
- **assets** - Consolidated targets with embedded credentials (8 tables)
- **automation** - Jobs, executions, schedules, workflows (6 tables)
- **communication** - Notifications, templates, audit logs (4 tables)

### Key Features
- **Enhanced Targets** - New architecture with embedded credentials
- **Hierarchical Groups** - 3-level target organization
- **Service Definitions** - 31+ predefined service types
- **Comprehensive RBAC** - 5 roles with granular permissions
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

### Manual Deployment
```bash
# Standard deployment
docker-compose up -d

# Scale workers
docker-compose up -d --scale automation-worker-1=3

# Individual service updates
docker-compose up -d --no-deps <service-name>
```

### Health Monitoring
```bash
# Check all services
docker-compose ps

# Individual health checks
curl http://localhost:3000/health  # API Gateway
curl http://localhost:3005/health  # AI Command Service
curl http://localhost:5555         # Celery Flower Dashboard
```

---

## 🔒 Security

### Authentication & Authorization
- **JWT-based Authentication** - Secure token-based access
- **Role-based Access Control** - 5 predefined roles (admin, manager, operator, developer, viewer)
- **Session Management** - Refresh tokens and session tracking
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
- **API Gateway**: http://localhost:3000/docs
- **AI Command Service**: http://localhost:3005/docs
- **All Services**: Available at `<service-url>/docs`

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
curl -X POST http://localhost:3005/ai/chat \\
  -H \"Content-Type: application/json\" \\
  -d '{\"message\": \"restart nginx on web servers\", \"user_id\": 1}'
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
├── ai-brain/                # Unified AI service with modular engine architecture
├── api-gateway/             # Central API routing
├── identity-service/        # User management
├── asset-service/           # Infrastructure targets
├── automation-service/      # Job execution
├── communication-service/   # Notifications
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
- **Celery Flower**: http://localhost:5555 (admin/admin123)
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
docker-compose exec postgres psql -U postgres -d opsconductor -c \"SELECT 1;\"

# Reset database (WARNING: Data loss)
docker-compose down -v
docker-compose up -d postgres
```

#### AI Service Issues
```bash
# Test AI service health
curl http://localhost:3005/health

# Check Ollama models
curl http://localhost:11434/api/tags

# Verify ChromaDB
curl http://localhost:8000/api/v1/heartbeat
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

## 🔮 Roadmap

### Short Term (1-3 months)
- [ ] Enhanced multi-model LLM support
- [ ] Advanced caching and performance optimization
- [ ] Mobile-responsive web interface
- [ ] Extended protocol support (WMI, REST APIs)

### Medium Term (3-6 months)
- [ ] Kubernetes deployment manifests
- [ ] Advanced analytics dashboard
- [ ] Custom plugin architecture
- [ ] Multi-tenant support

### Long Term (6+ months)
- [ ] Edge computing support
- [ ] Advanced AI model training
- [ ] Marketplace for automation scripts
- [ ] Enterprise SSO integration

---

## 📚 Additional Documentation

- **[Volume Mount System](VOLUME_MOUNT_SYSTEM.md)** - Docker volume configuration
- **[GPU Setup Guide](GPU_SETUP.md)** - GPU acceleration setup
- **[Scripting Standards](docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md)** - Development standards

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - For advancing AI and natural language processing
- **Ollama** - For local LLM serving capabilities
- **ChromaDB** - For vector database technology
- **FastAPI** - For modern Python web framework
- **React** - For powerful frontend development

---

**OpsConductor NG - Transforming IT Operations with Intelligent Automation**

*Built with ❤️ for the IT operations community*