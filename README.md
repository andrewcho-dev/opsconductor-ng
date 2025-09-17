# 🤖 OpsConductor - Intelligent Infrastructure Automation Platform

**Next-Generation IT Operations with AI Microservices Architecture**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](https://github.com/opsconductor/opsconductor-ng)
[![AI Architecture](https://img.shields.io/badge/AI-Microservices-blue.svg)](AI_DOCUMENTATION.md)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 What is OpsConductor?

OpsConductor is an **intelligent infrastructure automation platform** that transforms complex IT operations into simple natural language conversations. Built with a modern **AI microservices architecture**, it provides powerful automation, monitoring, and predictive analytics capabilities.

### 🎯 Key Features

- 🧠 **AI-Powered Interface** - Natural language commands for all operations
- 🔧 **Multi-Protocol Automation** - SNMP, SSH, SMTP, VAPIX, and more
- 📊 **Real-Time Monitoring** - Comprehensive infrastructure visibility
- 🤖 **Intelligent Workflows** - AI-generated automation scripts
- 🔮 **Predictive Analytics** - Proactive issue detection and prevention
- 🛡️ **Security-First** - Enterprise-grade security and compliance

---

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM (for AI services)
- Git
- **Optional:** NVIDIA GPU + drivers for AI acceleration
  - [Standard GPU Setup Guide](GPU_SETUP.md)
  - [GPU in VMs with vfio-pci](docs/GPU_VFIO_PCI_VM_FIX.md) - For virtualized environments

### One-Command Deployment
```bash
# Clone and deploy
git clone <repository-url>
cd opsconductor-ng
docker-compose up -d

# For GPU acceleration (optional)
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# Access the platform
# Web Interface: http://localhost:3100
# API Gateway: http://localhost:3000
# AI Chat: http://localhost:3005/ai/chat
```

### GPU Acceleration (Optional)
For enhanced AI performance, see the [GPU Setup Guide](GPU_SETUP.md):
```bash
# Validate GPU setup
./scripts/validate_gpu_setup.sh

# Check AI services GPU status
python3 scripts/check_gpu_status.py
```

### Default Credentials
- **Username:** admin
- **Password:** admin123

---

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │◄──►│   API Gateway   │◄──►│ AI Orchestrator │
│   (React/TS)    │    │   (FastAPI)     │    │   (FastAPI)     │
│   Port 3100     │    │   Port 3000     │    │   Port 3005     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Identity       │    │  Asset Service  │    │  Automation     │
│  Service        │    │  (Targets)      │    │  Service        │
│  Port 3001      │    │  Port 3002      │    │  Port 3003      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### AI Microservices Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AI Orchestrator│◄──►│   NLP Service   │    │  Vector Service │    │   LLM Service   │
│   (Port 3005)   │    │   (Port 3006)   │    │   (Port 3007)   │    │   (Port 3008)   │
│                 │    │                 │    │                 │    │                 │
│ • Coordination  │    │ • Intent Class. │    │ • Knowledge     │    │ • Text Gen.     │
│ • Routing       │    │ • Entity Extract│    │ • Vector Search │    │ • Chat Interface│
│ • Integration   │    │ • NLP Processing│    │ • ChromaDB      │    │ • Ollama        │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 💬 Natural Language Interface

Transform complex operations into simple conversations:

### System Management
```bash
"Check CPU usage on all Linux servers"
"Restart nginx service on web servers"
"Update stationcontroller on CIS servers"
"Show disk space alerts from last 24 hours"
```

### Automation Creation
```bash
"Create a PowerShell script to restart IIS"
"Schedule weekly disk cleanup on Windows servers"
"Monitor network switches via SNMP every 5 minutes"
"Generate a backup script for database servers"
```

### Monitoring & Analytics
```bash
"What's the system health status?"
"Show me performance trends for the last week"
"Any anomalies detected recently?"
"Predict maintenance needs for next month"
```

---

## 🧠 AI Capabilities

### Natural Language Processing
- **Intent Classification** - Understands user intentions with 95%+ accuracy
- **Entity Extraction** - Identifies targets, operations, and parameters
- **Context Awareness** - Maintains conversation context and history
- **Multi-Language Support** - Supports technical and natural language

### Knowledge Management
- **Vector Database** - Semantic search through documentation and procedures
- **Learning System** - Continuously improves from user interactions
- **Pattern Recognition** - Identifies common operations and optimizations
- **Best Practices** - Suggests industry-standard approaches

### Intelligent Automation
- **Script Generation** - Creates production-ready PowerShell, Bash, Python scripts
- **Workflow Orchestration** - Manages complex multi-step operations
- **Error Handling** - Robust error detection and recovery mechanisms
- **Protocol Integration** - Seamless multi-protocol operations

---

## 🔧 Core Services

### Infrastructure Services
- **PostgreSQL** (Port 5432) - Primary database
- **Redis** (Port 6379) - Caching and session management
- **ChromaDB** (Port 8000) - Vector database for AI knowledge
- **Nginx** (Port 80/443) - Reverse proxy and load balancer

### Application Services
- **API Gateway** (Port 3000) - Central API routing and authentication
- **Identity Service** (Port 3001) - User management and authentication
- **Asset Service** (Port 3002) - Infrastructure target management
- **Automation Service** (Port 3003) - Job execution and scheduling
- **Communication Service** (Port 3004) - Notifications and messaging

### AI Services
- **AI Orchestrator** (Port 3005) - Main AI interface and coordination
- **NLP Service** (Port 3006) - Natural language processing
- **Vector Service** (Port 3007) - Knowledge storage and retrieval
- **LLM Service** (Port 3008) - Large language model interface
- **Ollama Server** (Port 11434) - Local LLM model serving

---

## 🚀 Deployment Options

### Docker Compose (Recommended)
```bash
# Full deployment
docker-compose up -d

# AI services only
docker-compose up -d ai-orchestrator vector-service llm-service

# Development mode with hot reload
docker-compose -f docker-compose.dev.yml up
```

### Individual Service Deployment
```bash
# Build specific services
docker-compose build ai-orchestrator

# Scale services
docker-compose up -d --scale automation-worker=3

# Update specific service
docker-compose up -d --no-deps ai-orchestrator
```

### Health Monitoring
```bash
# Check all services
docker-compose ps

# Test AI services
python test_ai_microservices.py

# Individual health checks
curl http://localhost:3005/health  # AI Orchestrator
curl http://localhost:3006/health  # NLP Service
curl http://localhost:3007/health  # Vector Service
curl http://localhost:3008/health  # LLM Service
```

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
GET  /api/v1/targets              - List infrastructure targets
POST /api/v1/targets              - Create new target
POST /api/v1/jobs                 - Create automation job
POST /api/v1/jobs/{id}/execute    - Execute job
GET  /api/v1/executions           - List job executions
```

### Authentication
```
POST /api/v1/auth/login           - User authentication
POST /api/v1/auth/refresh         - Refresh JWT token
GET  /api/v1/auth/profile         - Get user profile
```

### Interactive Documentation
- **API Gateway**: http://localhost:3000/docs
- **AI Orchestrator**: http://localhost:3005/docs
- **NLP Service**: http://localhost:3006/docs
- **Vector Service**: http://localhost:3007/docs
- **LLM Service**: http://localhost:3008/docs

---

## 🧪 Testing

### Automated Testing
```bash
# Comprehensive AI test suite
python test_ai_microservices.py

# Service-specific tests
pytest tests/test_ai_services.py
pytest tests/test_vector_service.py
pytest tests/test_llm_service.py

# Integration tests
pytest tests/integration/
```

### Manual Testing
```bash
# Test AI chat
curl -X POST http://localhost:3005/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "restart nginx on web servers", "user_id": 1}'

# Test NLP parsing
curl -X POST http://localhost:3006/nlp/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "update stationcontroller on CIS servers"}'

# Test vector search
curl -X POST http://localhost:3007/vector/search \
  -H "Content-Type: application/json" \
  -d '{"query": "nginx restart procedure", "limit": 3}'
```

---

## 🔒 Security

### Authentication & Authorization
- **JWT-based Authentication** - Secure token-based access
- **Role-based Access Control** - Granular permission system
- **Multi-factor Authentication** - Enhanced security options
- **API Key Management** - Service-to-service authentication

### Data Protection
- **Encryption at Rest** - Fernet encryption for sensitive data
- **TLS/SSL Support** - Encrypted communication
- **Input Validation** - Comprehensive data sanitization
- **Audit Logging** - Complete operation tracking

### Security Monitoring
- **Automated Threat Detection** - AI-powered security analysis
- **Failed Login Monitoring** - Brute force attack detection
- **Privilege Escalation Alerts** - Unauthorized access attempts
- **Security Event Correlation** - Pattern-based threat identification

---

## 📈 Performance & Monitoring

### Performance Metrics
- **Response Time** - < 3 seconds for AI queries
- **Throughput** - 100+ concurrent operations
- **Availability** - 99.9% uptime target
- **AI Accuracy** - 95%+ intent detection accuracy

### Monitoring & Observability
- **Health Checks** - Comprehensive service monitoring
- **Metrics Collection** - Prometheus-compatible metrics
- **Log Aggregation** - Centralized logging
- **Distributed Tracing** - Request flow tracking
- **Alerting** - Proactive issue notification

### Resource Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 20GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB storage
- **Production**: 16GB RAM, 8 CPU cores, 100GB storage
- **GPU**: Optional NVIDIA GPU for enhanced AI performance

---

## 🛠️ Development

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd opsconductor-ng

# Development environment
docker-compose -f docker-compose.dev.yml up

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Code Structure
```
opsconductor-ng/
├── ai-orchestrator/     # AI coordination service
├── ai-command/          # Main AI service with Ollama
├── vector-service/      # Knowledge storage and retrieval
├── llm-service/         # Large language model interface
├── api-gateway/         # Central API routing
├── identity-service/    # User management
├── asset-service/       # Infrastructure targets
├── automation-service/  # Job execution
├── communication-service/ # Notifications
├── frontend/            # React web interface
├── shared/              # Common utilities
├── database/            # Database schemas
└── docs/                # Documentation
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

---

## 📚 Documentation

### Available Documentation
- **[AI System Documentation](AI_DOCUMENTATION.md)** - Comprehensive AI architecture guide
- **[Repository Overview](REPO.md)** - Detailed repository structure and components
- **[Scripting Standards](docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md)** - Development standards
- **[Volume Mount System](VOLUME_MOUNT_SYSTEM.md)** - Docker volume configuration
- **[Communication Settings](COMMUNICATION_SETTINGS_IMPLEMENTATION.md)** - Notification setup

### API Documentation
Interactive API documentation is available for all services at their respective `/docs` endpoints.

---

## 🚨 Troubleshooting

### Common Issues

#### Service Startup Issues
```bash
# Check service logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>

# Rebuild and restart
docker-compose up -d --build <service-name>
```

#### AI Service Issues
```bash
# Test AI service health
curl http://localhost:3005/health

# Check AI service communication
python test_ai_microservices.py

# Verify model availability
curl http://localhost:11434/api/tags
```

#### Database Issues
```bash
# Check database connection
docker-compose exec postgres psql -U postgres -d opsconductor -c "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Performance Issues
1. **High Memory Usage**: Increase Docker memory limits
2. **Slow AI Responses**: Check Ollama model size and GPU availability
3. **Database Slow**: Optimize queries and add indexes
4. **Network Issues**: Verify service connectivity and DNS resolution

---

## 🎯 Use Cases

### IT Operations Teams
- **Infrastructure Monitoring** - Real-time system health and performance
- **Automated Remediation** - Self-healing infrastructure capabilities
- **Incident Response** - Rapid problem identification and resolution
- **Capacity Planning** - Predictive resource management

### DevOps Engineers
- **CI/CD Integration** - Automated deployment and testing workflows
- **Configuration Management** - Consistent infrastructure configuration
- **Security Compliance** - Automated security scanning and remediation
- **Performance Optimization** - Continuous performance monitoring and tuning

### System Administrators
- **Daily Operations** - Streamlined routine maintenance tasks
- **Emergency Response** - Quick access to critical system information
- **Documentation** - Automated procedure documentation and knowledge sharing
- **Training** - Interactive learning through natural language interface

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

## 📞 Support

### Community Support
- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - Comprehensive guides and API reference
- **Examples** - Sample configurations and use cases

### Enterprise Support
- **Professional Services** - Implementation and customization
- **Training** - Team training and certification
- **SLA Support** - 24/7 support with guaranteed response times

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - For advancing the field of AI and natural language processing
- **Ollama** - For providing local LLM serving capabilities
- **ChromaDB** - For vector database technology
- **FastAPI** - For modern Python web framework
- **React** - For powerful frontend development

---

**OpsConductor - Transforming IT Operations with Intelligent Automation**

*Built with ❤️ for the IT operations community*