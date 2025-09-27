# OpsConductor NG - Repository Structure & Architecture

## 📁 Repository Overview

This document provides a comprehensive overview of the OpsConductor NG repository structure, components, and development guidelines based on the current production-ready implementation.

## 🏗️ Directory Structure

```
opsconductor-ng/
├── 🤖 AI Services
│   └── ai-brain/                # Unified AI service with modular engine architecture
│
├── 🌐 Core Services
│   ├── kong/                    # Kong Gateway - Enterprise API Gateway
│   ├── keycloak/                # Keycloak - Enterprise Identity Management
│   ├── identity-service/        # User management and RBAC
│   ├── asset-service/           # Infrastructure target management
│   ├── automation-service/      # Job execution with Celery workers
│   └── communication-service/   # Notifications and audit logging
│
├── 🎨 Frontend
│   └── frontend/                # React TypeScript web interface
│
├── 🔧 Infrastructure
│   ├── nginx/                   # Reverse proxy configuration
│   ├── database/                # Complete schema and migrations
│   └── shared/                  # Common utilities and libraries
│
├── 📜 Scripts & Tools
│   ├── scripts/                 # Deployment and utility scripts
│   ├── build.sh                 # Complete system build script
│   ├── deploy.sh                # Automated deployment script
│   └── verify-setup.sh          # Pre-deployment verification
│
├── 📚 Documentation
│   ├── README.md                # Main project documentation
│   ├── REPO.md                  # This file - repository structure
│   ├── VOLUME_MOUNT_SYSTEM.md   # Docker volume configuration
│   └── docs/                    # Additional documentation
│
└── 🐳 Deployment
    ├── docker-compose.yml       # Main deployment configuration
    ├── docker-compose.gpu.yml   # GPU acceleration configuration
    └── .env.example             # Environment variables template
```

## 🤖 AI Services

### AI Brain Service (`/ai-brain/`)
**Unified AI service with modular engine architecture**

```
ai-brain/
├── main.py                      # FastAPI service entry point
├── brain_engine.py              # Main AI orchestrator and coordinator
├── llm_conversation_handler.py  # LLM conversation management
├── intent_engine/               # Intent classification and processing
│   ├── intent_classifier.py     # ML-based intent classification
│   ├── entity_extractor.py      # Named entity recognition
│   └── context_manager.py       # Conversation context management
├── knowledge_engine/            # AI knowledge and learning systems
│   ├── it_knowledge_base.py     # IT operations knowledge
│   ├── error_resolution.py      # Error diagnosis and solutions
│   ├── learning_system.py       # Continuous learning engine
│   └── solution_patterns.py     # Common solution patterns
├── job_engine/                  # Intelligent job creation
│   ├── llm_job_creator.py       # LLM-powered job generation
│   ├── workflow_generator.py    # Workflow creation from NL
│   ├── job_validator.py         # Job validation and safety
│   ├── execution_planner.py     # Execution planning
│   ├── step_optimizer.py        # Step optimization
│   └── target_resolver.py       # Target resolution
├── system_model/                # System understanding and mapping
│   ├── asset_mapper.py          # Asset relationship mapping
│   ├── protocol_knowledge.py    # Protocol and service knowledge
│   ├── service_capabilities.py  # Service capability mapping
│   └── workflow_templates.py    # Workflow templates
├── integrations/                # External service integrations
│   ├── asset_client.py          # Asset service integration
│   ├── automation_client.py     # Automation service integration
│   ├── communication_client.py  # Communication service integration
│   ├── llm_client.py           # Ollama LLM integration
│   └── vector_client.py        # Vector database integration
├── legacy/                     # Legacy compatibility layer
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

**Key Responsibilities**:
- Unified AI orchestration and coordination
- Natural language intent classification and entity extraction
- Intelligent job creation and workflow generation
- IT knowledge base and error resolution
- Continuous learning and improvement
- Integration with all core services and external AI infrastructure



## 🌐 Core Services

### Kong Gateway (`/kong/`)
**Enterprise API Gateway**

```
kong/
├── kong.yml                     # Kong Gateway configuration
└── Dockerfile                   # Container configuration
```

**Key Features**:
- Enterprise-grade API routing and load balancing
- Advanced authentication and authorization
- Rate limiting, request/response transformation
- Plugin ecosystem for extensibility
- High performance and scalability

### Keycloak (`/keycloak/`)
**Enterprise Identity Management**

```
keycloak/
├── opsconductor-realm.json      # Keycloak realm configuration
├── init-keycloak.sh             # Initialization script
└── Dockerfile                   # Container configuration
```

**Key Features**:
- Single Sign-On (SSO) and Multi-Factor Authentication (MFA)
- Advanced Role-Based Access Control (RBAC)
- User federation and social login
- OAuth2/OpenID Connect compliance
- Enterprise identity standards

### Identity Service (`/identity-service/`)
**User management and RBAC**

```
identity-service/
├── main.py                      # FastAPI service entry point
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

**Key Features**:
- User registration and authentication
- JWT token generation and validation
- Role-based access control (5 roles)
- Password hashing and security
- Session management with refresh tokens

### Asset Service (`/asset-service/`)
**Infrastructure target management with embedded credentials**

```
asset-service/
├── main.py                      # FastAPI service entry point
├── main_with_groups.py          # Enhanced version with groups
├── data/                        # Data storage
│   └── encryption.key           # Fernet encryption key
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

**Key Features**:
- Consolidated asset management
- Embedded credential encryption (Fernet)
- Hierarchical target groups (3 levels)
- Service definitions (31+ types)
- Connection testing and validation

### Automation Service (`/automation-service/`)
**Job execution with Celery workers**

```
automation-service/
├── main.py                      # FastAPI service entry point
├── worker.py                    # Celery worker for job execution
├── celery_monitor.py            # Celery monitoring
├── websocket_manager.py         # Real-time job status updates
├── libraries/                   # Protocol-specific libraries
│   ├── connection_manager.py    # Connection management
│   ├── windows_powershell.py    # PowerShell execution
│   └── linux_ssh.py             # SSH execution
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

**Key Features**:
- Job creation and execution
- Multi-protocol support (SSH, PowerShell, SNMP, etc.)
- Celery-based distributed task processing
- Real-time job status updates via WebSocket
- Scheduled job execution
- Multiple worker instances for scaling

### Communication Service (`/communication-service/`)
**Notifications and audit logging**

```
communication-service/
├── main.py                      # FastAPI service entry point
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

**Key Features**:
- Email notifications (SMTP)
- Webhook integrations
- Comprehensive audit logging
- Template management
- Multi-channel communication

## 🎨 Frontend

### Web Interface (`/frontend/`)
**React TypeScript web application**

```
frontend/
├── src/
│   ├── components/              # React components
│   │   ├── AssetDataGrid.tsx    # Enhanced asset grid
│   │   └── ...                  # Other components
│   ├── pages/                   # Page components
│   │   ├── Assets.tsx           # Asset management page
│   │   └── ...                  # Other pages
│   ├── contexts/                # React contexts
│   ├── services/                # API service clients
│   ├── types/                   # TypeScript type definitions
│   ├── utils/                   # Utility functions
│   └── App.tsx                  # Main application component
├── public/                      # Static assets
├── package.json                 # Node.js dependencies
├── tsconfig.json                # TypeScript configuration
└── Dockerfile                   # Container configuration
```

**Key Features**:
- Modern React with TypeScript
- Material-UI component library
- Real-time updates via WebSocket
- Responsive design
- AI chat interface
- Enhanced asset management

## 🔧 Infrastructure

### Database (`/database/`)
**Complete database schema and initialization**

```
database/
├── complete-schema.sql          # Complete database schema
├── init-db.sh                   # Database initialization script
└── migrations/                  # Database migration scripts
```

**Database Schemas**:
- **identity** - Users, roles, permissions, sessions (5 tables)
- **assets** - Consolidated targets with embedded credentials (8 tables)
- **automation** - Jobs, executions, schedules, workflows (6 tables)
- **communication** - Notifications, templates, audit logs (4 tables)

### Shared (`/shared/`)
**Common utilities and libraries**

```
shared/
├── base_service.py              # Base FastAPI service class
├── ai_common.py                 # AI common utilities
├── ai_monitoring.py             # AI monitoring utilities
├── learning_engine.py           # Shared learning engine
├── rbac_middleware.py           # RBAC middleware
└── vector_client.py             # Vector service client
```

### Nginx (`/nginx/`)
**Reverse proxy and SSL termination**

```
nginx/
├── nginx.conf                   # Main Nginx configuration
├── Dockerfile                   # Container configuration
└── ssl/                         # SSL certificates
    ├── nginx.crt                # SSL certificate
    └── nginx.key                # SSL private key
```

## 📜 Scripts & Tools

### Deployment Scripts
```
├── build.sh                     # Complete system build
├── deploy.sh                    # Automated deployment
├── verify-setup.sh              # Pre-deployment verification
└── scripts/
    ├── check_gpu_status.py      # GPU status checking
    ├── validate_gpu_setup.sh    # GPU setup validation
    └── README.md                # Script documentation
```

### Testing Scripts
```
├── test_ai_microservices.py     # Comprehensive AI testing
├── test_frontend_integration.py # Frontend integration tests
├── test_ai_system_v2.py         # AI system v2 tests
└── various other test files...
```

## 🐳 Deployment Configuration

### Docker Compose (`/docker-compose.yml`)
**Main deployment configuration with 20+ services**

**Service Categories**:
- **Infrastructure**: PostgreSQL, Redis, ChromaDB, Nginx
- **Core Services**: API Gateway, Identity, Asset, Automation, Communication
- **AI Services**: AI Command, AI Orchestrator, Vector, LLM, Ollama
- **Workers**: 2 Automation workers, Scheduler, Celery Monitor
- **Frontend**: React web application

**Key Features**:
- Health checks for all services
- Selective volume mounts for development
- GPU support for AI services
- Service dependencies and startup order
- Resource limits and scaling configuration

### GPU Configuration (`/docker-compose.gpu.yml`)
**GPU acceleration for AI services**

**Features**:
- NVIDIA GPU support for AI services
- CUDA environment variables
- GPU resource reservations
- Optimized for AI workloads

## 🔧 Development Guidelines

### Code Standards

#### Python Services
- **Framework**: FastAPI for all services
- **Style**: PEP 8 compliance with Black formatting
- **Type Hints**: Full type annotations required
- **Documentation**: Comprehensive docstrings
- **Testing**: Pytest for unit and integration tests

#### Frontend
- **Framework**: React with TypeScript
- **Style**: ESLint and Prettier configuration
- **Components**: Functional components with hooks
- **State Management**: React Context and custom hooks
- **UI Library**: Material-UI with custom theming

### Service Communication

#### Inter-Service Communication
- **Protocol**: HTTP/REST APIs
- **Authentication**: JWT tokens via headers
- **Error Handling**: Consistent error response format
- **Timeouts**: Configurable request timeouts
- **Health Checks**: All services provide `/health` endpoints

#### Data Flow
```
User Request → Nginx → API Gateway → Service Router → Target Service
                           ↓
                   Authentication & Authorization
                           ↓
                   Request Validation & Rate Limiting
                           ↓
                   Response Aggregation & Formatting
```

### Environment Configuration

#### Environment Variables
Each service uses environment variables for configuration:

```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=opsconductor
DB_USER=postgres
DB_PASSWORD=postgres123

# Redis
REDIS_URL=redis://redis:6379/0

# Service URLs
IDENTITY_SERVICE_URL=http://identity-service:3001
ASSET_SERVICE_URL=http://asset-service:3002
AI_SERVICE_URL=http://ai-brain:3005
```

## 📊 Monitoring & Observability

### Health Checks
Each service provides a `/health` endpoint that returns:
```json
{
  "service": "service-name",
  "status": "healthy|unhealthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "dependencies": [
    {"name": "database", "status": "healthy"},
    {"name": "redis", "status": "healthy"}
  ]
}
```

### Monitoring Tools
- **Celery Flower**: http://localhost:5555 (admin/admin123)
- **Health Endpoints**: All services provide health checks
- **Audit Logs**: Complete operation tracking in database
- **Service Logs**: Structured logging with correlation IDs

## 🚀 Deployment Strategies

### Development Deployment
```bash
# Start development environment with hot reload
docker-compose -f docker-compose.dev.yml up

# Selective volume mounts for development
# Debug logging enabled
# Direct port access for testing
```

### Production Deployment
```bash
# Full production deployment
./deploy.sh

# Or manual deployment
docker-compose up -d

# Health checks enabled
# Resource limits configured
# Security hardening applied
```

### Scaling Strategies
```bash
# Scale specific services
docker-compose up -d --scale automation-worker-1=3
docker-compose up -d --scale automation-worker-2=2

# Load balancing handled by Nginx
# Database connection pooling
# Redis for session management
```

## 🔮 Architecture Evolution

### Current State (Production Ready)
- ✅ Microservices architecture with 11 core services
- ✅ AI-powered natural language interface
- ✅ Comprehensive database schema with 4 schemas
- ✅ Enhanced asset management with embedded credentials
- ✅ Scalable job execution with Celery workers
- ✅ Complete RBAC and audit logging
- ✅ GPU acceleration for AI services

### Planned Improvements
- **Kubernetes Support**: Native Kubernetes deployment manifests
- **Observability**: Prometheus metrics and Grafana dashboards
- **CI/CD Pipeline**: Automated testing and deployment
- **Multi-Tenancy**: Support for multiple organizations
- **Plugin Architecture**: Extensible plugin system

---

**This repository structure provides a solid foundation for scalable, maintainable, and secure IT operations automation with advanced AI capabilities.**