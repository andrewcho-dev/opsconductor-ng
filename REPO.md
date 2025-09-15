# OpsConductor Repository Structure

## 📁 Repository Overview

This document provides a comprehensive overview of the OpsConductor repository structure, components, and development guidelines.

## 🏗️ Directory Structure

```
opsconductor-ng/
├── 🤖 AI Services
│   ├── ai-orchestrator/         # AI coordination and main interface
│   ├── nlp-service/             # Natural language processing
│   ├── vector-service/          # Knowledge storage and retrieval
│   └── llm-service/             # Large language model interface
│
├── 🌐 Core Services
│   ├── api-gateway/             # Central API routing and authentication
│   ├── identity-service/        # User management and authentication
│   ├── asset-service/           # Infrastructure target management
│   ├── automation-service/      # Job execution and scheduling
│   └── communication-service/   # Notifications and messaging
│
├── 🎨 Frontend
│   └── frontend/                # React TypeScript web interface
│
├── 🔧 Infrastructure
│   ├── nginx/                   # Reverse proxy configuration
│   ├── database/                # Database schemas and migrations
│   └── shared/                  # Common utilities and libraries
│
├── 📜 Scripts & Tools
│   ├── scripts/                 # Deployment and utility scripts
│   └── test_ai_microservices.py # AI system testing suite
│
├── 📚 Documentation
│   ├── docs/                    # Additional documentation
│   ├── AI_DOCUMENTATION.md     # Comprehensive AI system guide
│   ├── README.md                # Main project documentation
│   └── REPO.md                  # This file
│
└── 🐳 Deployment
    ├── docker-compose.yml       # Main deployment configuration
    ├── docker-compose.dev.yml   # Development environment
    └── .env.example             # Environment variables template
```

## 🤖 AI Services

### AI Orchestrator (`/ai-orchestrator/`)
**Main AI interface and coordination hub**

```
ai-orchestrator/
├── main.py                 # FastAPI service entry point
├── orchestrator.py         # Core orchestration logic
├── protocol_manager.py     # AI workflow protocols
├── workflow_generator.py   # Workflow generation from NLP
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Responsibilities**:
- Unified AI API interface
- Request routing between AI services
- Response aggregation and formatting
- Integration with asset and automation services
- Protocol management for different AI workflows

### NLP Service (`/nlp-service/`)
**Natural language processing and understanding**

```
nlp-service/
├── main.py                 # FastAPI service entry point
├── nlp_processor.py        # Advanced NLP processing engine
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Responsibilities**:
- Intent classification (restart, update, check, stop, start)
- Entity extraction (operations, targets, groups, OS types)
- Command parsing and normalization
- Confidence scoring and validation
- Multi-language support

### Vector Service (`/vector-service/`)
**Knowledge storage and retrieval using vector embeddings**

```
vector-service/
├── main.py                 # FastAPI service entry point
├── vector_store.py         # Enhanced ChromaDB integration
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Responsibilities**:
- ChromaDB integration for vector storage
- Knowledge storage (documentation, procedures, solutions)
- Semantic search and similarity matching
- Pattern storage and retrieval
- Learning from successful operations

### LLM Service (`/llm-service/`)
**Large language model interface and text generation**

```
llm-service/
├── main.py                 # FastAPI service entry point
├── llm_engine.py           # Ollama integration and text generation
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Responsibilities**:
- Ollama integration for local LLM serving
- Multiple model support (Llama2, CodeLlama, etc.)
- Context-aware text generation
- Summarization and analysis
- Code generation and explanation

## 🌐 Core Services

### API Gateway (`/api-gateway/`)
**Central API routing and authentication**

```
api-gateway/
├── main.py                 # FastAPI gateway service
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Features**:
- Request routing to appropriate services
- JWT authentication and authorization
- Rate limiting and request validation
- CORS handling and security headers
- Health check aggregation

### Identity Service (`/identity-service/`)
**User management and authentication**

```
identity-service/
├── main.py                 # FastAPI service entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Features**:
- User registration and authentication
- JWT token generation and validation
- Role-based access control (RBAC)
- Password hashing and security
- Session management

### Asset Service (`/asset-service/`)
**Infrastructure target management**

```
asset-service/
├── main.py                 # FastAPI service entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Features**:
- Infrastructure target management
- Credential storage and encryption
- Service discovery and registration
- Target grouping and categorization
- Connection testing and validation

### Automation Service (`/automation-service/`)
**Job execution and scheduling**

```
automation-service/
├── main.py                 # FastAPI service entry point
├── worker.py               # Celery worker for job execution
├── celery_monitor.py       # Celery monitoring and management
├── websocket_manager.py    # Real-time job status updates
├── libraries/              # Protocol-specific libraries
│   ├── __init__.py
│   ├── connection_manager.py
│   ├── windows_powershell.py
│   ├── linux_ssh.py
│   ├── snmp_manager.py
│   ├── smtp_manager.py
│   └── vapix_manager.py
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Features**:
- Job creation and execution
- Multi-protocol support (SNMP, SSH, SMTP, VAPIX)
- Celery-based distributed task processing
- Real-time job status updates via WebSocket
- Scheduled job execution
- Error handling and retry logic

### Communication Service (`/communication-service/`)
**Notifications and messaging**

```
communication-service/
├── main.py                 # FastAPI service entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── shared/                # Shared utilities (symlinked)
```

**Key Features**:
- Email notifications (SMTP)
- Webhook integrations
- Audit logging and tracking
- Template management
- Multi-channel communication

## 🎨 Frontend

### Web Interface (`/frontend/`)
**React TypeScript web application**

```
frontend/
├── src/
│   ├── components/         # React components
│   ├── pages/             # Page components
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API service clients
│   ├── types/             # TypeScript type definitions
│   ├── utils/             # Utility functions
│   └── App.tsx            # Main application component
├── public/                # Static assets
├── package.json           # Node.js dependencies
├── tsconfig.json          # TypeScript configuration
├── Dockerfile             # Container configuration
└── .env                   # Environment variables
```

**Key Features**:
- Modern React with TypeScript
- Material-UI component library
- Real-time updates via WebSocket
- Responsive design
- AI chat interface
- Job management dashboard

## 🔧 Infrastructure

### Nginx (`/nginx/`)
**Reverse proxy and load balancer**

```
nginx/
├── nginx.conf             # Main Nginx configuration
├── Dockerfile             # Container configuration
└── ssl/                   # SSL certificates (if used)
```

### Database (`/database/`)
**Database schemas and migrations**

```
database/
├── complete-schema.sql    # Complete database schema
├── migrations/            # Database migration scripts
└── seed-data.sql         # Initial data (optional)
```

**Database Schemas**:
- **identity** - Users, roles, permissions, sessions
- **assets** - Targets, credentials, service definitions
- **automation** - Jobs, executions, schedules, workflows
- **communication** - Notifications, templates, audit logs

### Shared (`/shared/`)
**Common utilities and libraries**

```
shared/
├── __init__.py
├── base_service.py        # Base FastAPI service class
├── database.py            # Database connection utilities
├── auth.py                # Authentication utilities
├── logging_config.py      # Logging configuration
├── redis_client.py        # Redis client utilities
└── models.py              # Shared data models
```

## 📜 Scripts & Tools

### Scripts (`/scripts/`)
**Deployment and utility scripts**

```
scripts/
├── deploy.sh              # Main deployment script
├── backup.sh              # Database backup script
├── restore.sh             # Database restore script
├── health-check.sh        # System health check
└── README.md              # Script documentation
```

### Testing (`/test_ai_microservices.py`)
**Comprehensive AI system testing suite**

- Service health checks
- NLP processing validation
- Vector storage and search testing
- LLM generation testing
- End-to-end integration testing

## 🐳 Deployment Configuration

### Docker Compose (`/docker-compose.yml`)
**Main deployment configuration**

**Services Defined**:
- Infrastructure: PostgreSQL, Redis, ChromaDB, Nginx
- AI Services: AI Orchestrator, NLP, Vector, LLM, Ollama
- Core Services: API Gateway, Identity, Asset, Automation, Communication
- Frontend: React web application
- Monitoring: Celery Flower, health checks

### Development Environment (`/docker-compose.dev.yml`)
**Development-specific configuration**

**Features**:
- Volume mounts for hot reload
- Development-specific environment variables
- Debug logging enabled
- Exposed ports for direct service access

## 🔧 Development Guidelines

### Code Standards

#### Python Services
- **Framework**: FastAPI for all services
- **Style**: PEP 8 compliance with Black formatting
- **Type Hints**: Full type annotations required
- **Documentation**: Docstrings for all functions and classes
- **Testing**: Pytest for unit and integration tests

#### Frontend
- **Framework**: React with TypeScript
- **Style**: ESLint and Prettier configuration
- **Components**: Functional components with hooks
- **State Management**: React Context and custom hooks
- **Testing**: Jest and React Testing Library

### Service Communication

#### Inter-Service Communication
- **Protocol**: HTTP/REST APIs
- **Authentication**: JWT tokens passed via headers
- **Error Handling**: Consistent error response format
- **Timeouts**: Configurable request timeouts
- **Retry Logic**: Exponential backoff for failed requests

#### Data Flow
```
User Request → API Gateway → Service Router → Target Service
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
# ... etc
```

#### Configuration Management
- **Development**: `.env` files for local development
- **Production**: Environment variables or secrets management
- **Docker**: Environment variables in docker-compose.yml
- **Kubernetes**: ConfigMaps and Secrets

### Testing Strategy

#### Unit Tests
- **Coverage**: Minimum 80% code coverage
- **Framework**: Pytest for Python, Jest for TypeScript
- **Mocking**: Mock external dependencies
- **Isolation**: Each test should be independent

#### Integration Tests
- **Service Integration**: Test service-to-service communication
- **Database Integration**: Test database operations
- **API Integration**: Test complete API workflows
- **AI Integration**: Test AI pipeline functionality

#### End-to-End Tests
- **User Workflows**: Test complete user journeys
- **AI Functionality**: Test natural language processing
- **Automation**: Test job creation and execution
- **Performance**: Load testing and stress testing

### Security Considerations

#### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access**: Granular permission system
- **Token Expiration**: Configurable token lifetimes
- **Refresh Tokens**: Secure token renewal

#### Data Protection
- **Encryption**: Fernet encryption for sensitive data
- **TLS/SSL**: Encrypted communication between services
- **Input Validation**: Comprehensive data sanitization
- **SQL Injection**: Parameterized queries and ORM usage

#### Security Monitoring
- **Audit Logging**: Complete operation tracking
- **Failed Attempts**: Monitor and alert on failed logins
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Security Headers**: Proper HTTP security headers

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

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Centralized**: All logs aggregated for analysis
- **Retention**: Configurable log retention policies

### Metrics
- **Performance**: Response times, throughput, error rates
- **Resource Usage**: CPU, memory, disk, network
- **Business Metrics**: User activity, job success rates
- **AI Metrics**: Model accuracy, processing times

## 🚀 Deployment Strategies

### Development Deployment
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Hot reload enabled for all services
# Debug logging enabled
# Direct port access for testing
```

### Production Deployment
```bash
# Full production deployment
docker-compose up -d

# Health checks enabled
# Resource limits configured
# Security hardening applied
```

### Scaling Strategies
```bash
# Scale specific services
docker-compose up -d --scale automation-worker=3
docker-compose up -d --scale ai-orchestrator=2

# Load balancing handled by Nginx
# Database connection pooling
# Redis clustering for high availability
```

## 🔮 Future Enhancements

### Planned Improvements
- **Kubernetes Support**: Native Kubernetes deployment manifests
- **Observability**: Prometheus metrics and Grafana dashboards
- **CI/CD Pipeline**: Automated testing and deployment
- **Multi-Tenancy**: Support for multiple organizations
- **Plugin Architecture**: Extensible plugin system

### Architecture Evolution
- **Event-Driven**: Transition to event-driven architecture
- **Microservices Mesh**: Service mesh for advanced networking
- **Edge Computing**: Support for edge deployment scenarios
- **Cloud Native**: Cloud provider integrations and managed services

---

**This repository structure provides a solid foundation for scalable, maintainable, and secure IT operations automation with advanced AI capabilities.**