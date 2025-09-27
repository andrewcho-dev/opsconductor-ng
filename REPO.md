# OpsConductor NG - Repository Structure & Architecture

## 📁 Repository Overview

This document provides a comprehensive overview of the OpsConductor NG repository structure, components, and development guidelines based on the current production-ready implementation.

## 🏗️ Directory Structure

```
opsconductor-ng/
├── 🤖 AI Services
│   └── ai-brain/                # Pure LLM-driven AI service with Ollama integration
│
├── 🌐 Core Services
│   ├── kong/                    # Kong Gateway - Enterprise API Gateway
│   ├── keycloak/                # Keycloak - Enterprise Identity Management
│   ├── identity-service/        # User management with Keycloak integration
│   ├── asset-service/           # Infrastructure target management
│   ├── automation-service/      # Job execution with Celery workers
│   ├── communication-service/   # Notifications and audit logging
│   └── network-analyzer-service/# Network monitoring and analysis
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
│   ├── deploy-traefik.sh        # Traefik deployment option
│   ├── deploy-elk.sh            # ELK stack deployment
│   ├── deploy-redis-streams.sh  # Redis Streams deployment
│   ├── start-monitoring.sh      # Monitoring stack deployment
│   └── verify-setup.sh          # Pre-deployment verification
│
├── 📚 Documentation
│   ├── README.md                # Main project documentation
│   ├── DEPLOYMENT-GUIDE.md      # Complete deployment instructions
│   ├── REPO.md                  # This file - repository structure
│   └── docs/                    # Additional documentation
│
└── 🐳 Deployment
    ├── docker-compose.yml       # Main deployment configuration
    ├── docker-compose.gpu.yml   # GPU acceleration configuration
    ├── docker-compose.dev.yml   # Development environment
    └── .env.example             # Environment variables template
```

## 🤖 AI Services

### AI Brain Service (`/ai-brain/`)
**Pure LLM-driven service with no hardcoded logic**

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
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

**Key Responsibilities**:
- Pure LLM orchestration with no hardcoded logic
- Natural language intent classification and entity extraction
- Intelligent job creation and workflow generation
- IT knowledge base and error resolution
- Continuous learning and improvement
- Integration with all core services and Ollama LLM infrastructure

## 🌐 Core Services

### Kong Gateway (`/kong/`)
**Enterprise API Gateway with OAuth2 integration**

```
kong/
├── kong.yml                     # Declarative configuration
├── Dockerfile                   # Custom Kong image
└── plugins/                     # Custom Kong plugins
```

**Key Responsibilities**:
- Centralized API routing and load balancing
- OAuth2 authentication with Keycloak integration
- Rate limiting and security policies
- Request/response transformation
- API analytics and monitoring

### Keycloak (`/keycloak/`)
**Enterprise Identity and Access Management**

```
keycloak/
├── opsconductor-realm.json      # Realm configuration
├── Dockerfile                   # Custom Keycloak image
└── themes/                      # Custom UI themes
```

**Key Responsibilities**:
- User authentication and authorization
- OAuth2/OpenID Connect provider
- Role-based access control (RBAC)
- Multi-factor authentication (MFA)
- Single sign-on (SSO) capabilities

### Identity Service (`/identity-service/`)
**User management with Keycloak integration**

```
identity-service/
├── main.py                      # FastAPI service entry point
├── models/                      # Database models
├── routers/                     # API route handlers
├── services/                    # Business logic
├── keycloak_integration.py      # Keycloak client integration
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

### Asset Service (`/asset-service/`)
**Infrastructure target management with embedded credentials**

```
asset-service/
├── main.py                      # FastAPI service entry point
├── models/                      # Database models
├── routers/                     # API route handlers
├── services/                    # Business logic
├── encryption.py                # Credential encryption
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

### Automation Service (`/automation-service/`)
**Job execution with distributed Celery workers**

```
automation-service/
├── main.py                      # FastAPI service entry point
├── worker.py                    # Celery worker implementation
├── models/                      # Database models
├── routers/                     # API route handlers
├── services/                    # Business logic
├── tasks/                       # Celery task definitions
├── protocols/                   # Protocol implementations (SSH, RDP, etc.)
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

### Communication Service (`/communication-service/`)
**Notifications and audit logging**

```
communication-service/
├── main.py                      # FastAPI service entry point
├── models/                      # Database models
├── routers/                     # API route handlers
├── services/                    # Business logic
├── notification_handlers.py    # Notification delivery
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

### Network Analyzer Service (`/network-analyzer-service/`)
**Network monitoring and analysis**

```
network-analyzer-service/
├── main.py                      # FastAPI service entry point
├── models/                      # Database models
├── routers/                     # API route handlers
├── services/                    # Business logic
├── packet_analyzer.py           # Packet analysis engine
├── requirements.txt             # Python dependencies
└── Dockerfile                   # Container configuration
```

## 🎨 Frontend

### React TypeScript Application (`/frontend/`)
**Modern web interface with Bootstrap components**

```
frontend/
├── src/
│   ├── components/              # Reusable UI components
│   ├── pages/                   # Page components
│   ├── services/                # API service clients
│   ├── utils/                   # Utility functions
│   ├── types/                   # TypeScript type definitions
│   └── App.tsx                  # Main application component
├── public/                      # Static assets
├── package.json                 # Node.js dependencies
├── tsconfig.json                # TypeScript configuration
└── Dockerfile                   # Container configuration
```

**Key Technologies**:
- React 18.2.0 with TypeScript 4.9.5
- Bootstrap 5.3.8 for UI components
- AG Grid for advanced data display
- Lucide React for icons
- Axios for API communication

## 🔧 Infrastructure

### Database (`/database/`)
**PostgreSQL with comprehensive schema**

```
database/
├── complete-schema.sql          # Complete database schema
├── migrations/                  # Database migration scripts
└── seed-data.sql               # Initial data setup
```

**Schema Structure**:
- **identity** - User management (integrated with Keycloak)
- **assets** - Consolidated asset management
- **automation** - Job execution and scheduling
- **communication** - Notifications and audit logs
- **network_analysis** - Network monitoring and diagnostics

### Shared Libraries (`/shared/`)
**Common utilities and base classes**

```
shared/
├── base_service.py              # Base FastAPI service class
├── database.py                  # Database connection utilities
├── auth.py                      # Authentication utilities
├── logging.py                   # Logging configuration
└── models/                      # Shared database models
```

## 📜 Scripts & Tools

### Deployment Scripts
- **`build.sh`** - Complete system build script
- **`deploy.sh`** - Standard deployment with Nginx
- **`deploy-traefik.sh`** - Alternative deployment with Traefik
- **`deploy-elk.sh`** - Deployment with ELK logging stack
- **`deploy-redis-streams.sh`** - Deployment with Redis Streams messaging
- **`start-monitoring.sh`** - Deployment with Prometheus/Grafana monitoring
- **`verify-setup.sh`** - Pre-deployment verification and health checks

### Utility Scripts
```
scripts/
├── backup-database.sh           # Database backup utility
├── restore-database.sh          # Database restore utility
├── update-services.sh           # Service update utility
└── cleanup-docker.sh            # Docker cleanup utility
```

## 🐳 Deployment Configuration

### Docker Compose Files
- **`docker-compose.yml`** - Main deployment configuration
- **`docker-compose.gpu.yml`** - GPU acceleration overlay
- **`docker-compose.dev.yml`** - Development environment
- **`docker-compose.monitoring.yml`** - Monitoring stack overlay
- **`docker-compose.elk.yml`** - ELK logging stack overlay

### Environment Configuration
- **`.env.example`** - Environment variables template
- **`.env`** - Local environment configuration (created from template)

## 🔧 Development Guidelines

### Code Standards
- **Python**: PEP 8 compliance, type hints, async/await patterns
- **TypeScript**: Strict mode, proper typing, functional components
- **Docker**: Multi-stage builds, security best practices
- **API**: OpenAPI/Swagger documentation, RESTful design

### Testing Strategy
- **Unit Tests**: pytest for Python services
- **Integration Tests**: Service-to-service communication
- **End-to-End Tests**: Full workflow testing
- **AI Tests**: LLM response validation and accuracy

### Security Practices
- **Authentication**: OAuth2 with Keycloak integration
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: Fernet encryption for sensitive data
- **Input Validation**: Comprehensive data sanitization
- **Audit Logging**: Complete operation tracking

## 📊 Service Dependencies

### Dependency Graph
```
Frontend ──► Kong Gateway ──► Core Services ──► Database
    │              │                │              │
    │              │                │              │
    └──────────────┼────────────────┼──────────────┘
                   │                │
                   ▼                ▼
              Keycloak ────► AI Brain ────► Ollama
                   │           │              │
                   │           │              │
                   ▼           ▼              ▼
                Redis ────► ChromaDB ────► PostgreSQL
```

### Service Communication
- **API Gateway**: Kong handles all external API requests
- **Authentication**: Keycloak provides OAuth2 tokens
- **Service Mesh**: Internal service-to-service communication
- **Message Queue**: Redis for async task processing
- **Vector Database**: ChromaDB for AI knowledge storage
- **LLM Server**: Ollama for local model serving

## 🚀 Getting Started

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd opsconductor-ng

# Copy environment template
cp .env.example .env

# Build and deploy
./build.sh
./deploy.sh

# Verify deployment
./verify-setup.sh
```

### Adding New Services
1. Create service directory following naming convention
2. Implement FastAPI service with health endpoint
3. Add database models and migrations
4. Update docker-compose.yml
5. Add service to Kong Gateway configuration
6. Update documentation

### Contributing
1. Follow code standards and testing requirements
2. Update documentation for any changes
3. Ensure all health checks pass
4. Test with clean deployment

---

**For deployment instructions, see [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md). For project overview, see [README.md](README.md).**