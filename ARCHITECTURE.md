# OpsConductor NG - System Architecture

This document describes the complete architecture of OpsConductor NG, including all components, data flows, and design decisions.

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [AI Pipeline](#ai-pipeline)
4. [Microservices](#microservices)
5. [Infrastructure Components](#infrastructure-components)
6. [Data Flow](#data-flow)
7. [Database Schema](#database-schema)
8. [Security Architecture](#security-architecture)
9. [Deployment Architecture](#deployment-architecture)

---

## Overview

OpsConductor NG is an AI-powered IT operations automation platform that translates natural language requests into executed IT operations. The system uses a 4-stage AI pipeline to understand intent, select tools, plan execution, and format responses.

### Design Principles

1. **Clean Architecture** - Clear separation of concerns with single responsibility per component
2. **Microservices** - Specialized services for specific domains (automation, assets, network, communication)
3. **AI-First** - LLM-powered decision making at every stage
4. **API-Driven** - All services expose REST APIs
5. **Containerized** - Docker-based deployment for consistency and portability

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (React Frontend - Port 3100)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Kong API Gateway                           │
│                         (Port 3000)                             │
│              Authentication, Routing, Rate Limiting             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI Pipeline (Port 3005)                    │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Stage A  │→ │ Stage B  │→ │ Stage C  │→ │ Stage D  │      │
│  │Classifier│  │ Selector │  │ Planner  │  │Answerer  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                             │                                   │
│                             ▼                                   │
│                      ┌──────────┐                              │
│                      │ Stage E  │                              │
│                      │ Executor │                              │
│                      └──────────┘                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Specialized Services                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Automation  │  │    Assets    │  │   Network    │        │
│  │   Service    │  │   Service    │  │   Analyzer   │        │
│  │  (Port 3003) │  │ (Port 3002)  │  │ (Port 3006)  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  ┌──────────────┐                                              │
│  │Communication │                                              │
│  │   Service    │                                              │
│  │ (Port 3004)  │                                              │
│  └──────────────┘                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  PostgreSQL  │  │    Redis     │  │     vLLM     │        │
│  │  (Port 5432) │  │ (Port 6379)  │  │ (Port 8000)  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  ┌──────────────┐                                              │
│  │  Keycloak    │                                              │
│  │ (Port 8090)  │                                              │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## AI Pipeline

The AI Pipeline is the brain of OpsConductor NG. It processes user requests through four sequential stages, with each stage powered by the vLLM inference engine.

### Stage A: Classifier (Intent Analysis)

**Purpose**: Understand what the user wants to do

**Input**: Raw user request + context
**Output**: Structured intent classification

**Responsibilities**:
- Parse natural language request
- Identify primary intent (query, action, analysis)
- Extract key entities (hostnames, IPs, services)
- Determine urgency and scope
- Classify request type (informational, operational, analytical)

**Example**:
```
Input: "Check the status of web servers in production"
Output: {
  "intent": "query",
  "category": "system_status",
  "entities": ["web servers", "production"],
  "urgency": "normal",
  "scope": "infrastructure"
}
```

### Stage B: Selector (Tool Selection)

**Purpose**: Choose the right tools and services to fulfill the request

**Input**: Intent classification from Stage A
**Output**: Selected tools and services with parameters

**Responsibilities**:
- Query tool catalog for available capabilities
- Match intent to appropriate tools
- Select specialized services (automation, assets, network, communication)
- Determine execution order
- Validate tool availability

**Example**:
```
Input: Intent to check web server status
Output: {
  "tools": [
    {
      "service": "asset-service",
      "action": "query_assets",
      "parameters": {"type": "web_server", "environment": "production"}
    },
    {
      "service": "automation-service",
      "action": "check_service_status",
      "parameters": {"service": "httpd"}
    }
  ]
}
```

### Stage C: Planner (Execution Planning)

**Purpose**: Create a detailed, step-by-step execution plan

**Input**: Selected tools from Stage B
**Output**: Ordered execution plan with dependencies

**Responsibilities**:
- Create execution steps with proper ordering
- Handle dependencies between steps
- Add error handling and rollback logic
- Estimate execution time
- Determine approval requirements
- Plan resource allocation

**Example**:
```
Output: {
  "steps": [
    {
      "step": 1,
      "action": "query_assets",
      "service": "asset-service",
      "parameters": {...},
      "timeout": 30
    },
    {
      "step": 2,
      "action": "check_status",
      "service": "automation-service",
      "depends_on": [1],
      "parameters": {...},
      "timeout": 60
    }
  ],
  "estimated_time": 90,
  "requires_approval": false
}
```

### Stage D: Answerer (Response Formatting)

**Purpose**: Format execution results into user-friendly responses

**Input**: Execution results from Stage E
**Output**: Formatted response for the user

**Responsibilities**:
- Aggregate results from multiple steps
- Format data for human readability
- Generate summaries and insights
- Handle errors gracefully
- Provide actionable recommendations

**Example**:
```
Output: {
  "summary": "Found 5 web servers in production. All are running normally.",
  "details": [
    {"server": "web-01", "status": "running", "uptime": "45 days"},
    {"server": "web-02", "status": "running", "uptime": "30 days"},
    ...
  ],
  "recommendations": ["Consider updating web-03 (outdated version)"]
}
```

### Stage E: Executor (Execution Integration)

**Purpose**: Execute the plan and coordinate service calls

**Input**: Execution plan from Stage C
**Output**: Execution results

**Responsibilities**:
- Execute steps in correct order
- Handle dependencies and parallelization
- Call specialized services via REST APIs
- Collect and aggregate results
- Handle errors and retries
- Track execution state

---

## Microservices

### Automation Service (Port 3003)

**Purpose**: Execute commands and manage workflows on target systems

**Capabilities**:
- SSH command execution
- PowerShell/WinRM for Windows
- Script execution (bash, Python, PowerShell)
- Service management (start, stop, restart)
- File operations (read, write, transfer)
- Process management

**Key Features**:
- Secure credential management
- Connection pooling
- Timeout handling
- Output streaming
- Error recovery

**API Endpoints**:
- `POST /execute` - Execute command on target
- `POST /script` - Run script on target
- `GET /health` - Health check

### Asset Service (Port 3002)

**Purpose**: Manage infrastructure assets and their metadata

**Capabilities**:
- Asset inventory management
- Query assets by type, location, tags
- Track asset relationships
- Store connection credentials (encrypted)
- Manage asset lifecycle

**Key Features**:
- Consolidated asset model
- Flexible tagging system
- Encrypted credential storage
- Asset relationship tracking
- Query optimization

**API Endpoints**:
- `GET /assets` - Query assets
- `POST /assets` - Create asset
- `PUT /assets/{id}` - Update asset
- `DELETE /assets/{id}` - Delete asset
- `GET /health` - Health check

### Network Analyzer Service (Port 3006)

**Purpose**: Monitor and analyze network connectivity and performance

**Capabilities**:
- Ping/ICMP testing
- Port scanning
- Traceroute analysis
- Bandwidth testing
- DNS resolution
- Network topology mapping

**Key Features**:
- Parallel network operations
- Result caching
- Historical data tracking
- Anomaly detection

**API Endpoints**:
- `POST /ping` - Ping host
- `POST /scan` - Port scan
- `POST /traceroute` - Trace route
- `GET /health` - Health check

### Communication Service (Port 3004)

**Purpose**: Send notifications and alerts

**Capabilities**:
- Email notifications
- Slack/Teams integration
- SMS alerts
- Webhook delivery
- Notification templates

**Key Features**:
- Multi-channel delivery
- Template management
- Delivery tracking
- Retry logic

**API Endpoints**:
- `POST /notify` - Send notification
- `GET /templates` - List templates
- `GET /health` - Health check

---

## Infrastructure Components

### PostgreSQL 17 (Port 5432)

**Purpose**: Primary data store

**Schemas**:
- `assets` - Asset inventory and metadata
- `automation` - Automation workflows and history
- `communication` - Notification templates and logs
- `network_analysis` - Network monitoring data
- `tool_catalog` - Available tools and capabilities
- `execution` - Execution plans and results

**Key Features**:
- JSONB for flexible data
- Full-text search
- Partitioning for large tables
- Connection pooling
- Automated backups

### Redis 7 (Port 6379)

**Purpose**: Caching and message queue

**Use Cases**:
- LLM response caching
- Session management
- Rate limiting
- Task queue
- Real-time data

**Configuration**:
- Max memory: 256MB
- Eviction policy: allkeys-lru
- Persistence: AOF enabled

### vLLM 0.11 (Port 8000)

**Purpose**: Local LLM inference with GPU acceleration

**Model**: Qwen/Qwen2.5-14B-Instruct-AWQ
- 14 billion parameters
- AWQ 4-bit quantization
- 8K-32K context window (GPU dependent)
- OpenAI-compatible API

**Configuration** (RTX 3090 Ti):
- KV Cache: auto (FP16 on Ampere)
- Max context: 8192 tokens
- Max sequences: 2
- GPU memory: 92%

**API Endpoints**:
- `POST /v1/completions` - Text completion
- `POST /v1/chat/completions` - Chat completion
- `GET /health` - Health check
- `GET /v1/models` - List models

### Kong 3.4 (Port 3000)

**Purpose**: API Gateway

**Features**:
- Request routing
- Authentication (JWT, OAuth2)
- Rate limiting
- Request/response transformation
- Logging and monitoring

**Configuration**: Declarative (kong/kong.yml)

### Keycloak 22 (Port 8090)

**Purpose**: Identity and access management

**Features**:
- User authentication
- Role-based access control (RBAC)
- Single sign-on (SSO)
- OAuth2/OIDC provider
- User federation

**Realm**: opsconductor

---

## Data Flow

### Request Flow

1. **User submits request** via Frontend (React)
2. **Frontend sends to Kong** API Gateway (port 3000)
3. **Kong authenticates** request via Keycloak
4. **Kong routes** to AI Pipeline (port 3005)
5. **AI Pipeline processes** through 4 stages:
   - Stage A: Classifies intent
   - Stage B: Selects tools
   - Stage C: Creates plan
   - Stage D: Formats response
6. **Stage E executes** plan by calling specialized services
7. **Services interact** with infrastructure (database, target systems)
8. **Results flow back** through pipeline
9. **Response returned** to user via Frontend

### Data Storage Flow

1. **User data** → Keycloak (authentication)
2. **Asset data** → PostgreSQL assets schema
3. **Execution history** → PostgreSQL execution schema
4. **Tool metadata** → PostgreSQL tool_catalog schema
5. **Cache data** → Redis
6. **LLM responses** → Redis (temporary cache)

---

## Database Schema

The complete database schema is defined in `database/init-schema.sql` (1439 lines).

### Key Schemas

#### assets schema
- `assets` - Consolidated asset inventory
- `asset_credentials` - Encrypted credentials
- `asset_relationships` - Asset dependencies

#### automation schema
- `workflows` - Automation workflows
- `workflow_executions` - Execution history
- `workflow_steps` - Step definitions

#### tool_catalog schema
- `tools` - Available tools and capabilities
- `tool_capabilities` - Tool capability mappings
- `tool_patterns` - Intent-to-tool patterns
- `tool_telemetry` - Usage metrics
- `tool_audit_log` - Audit trail

#### execution schema
- `executions` - Execution plans and results
- `execution_steps` - Individual step results
- `execution_queue` - Pending executions
- `execution_locks` - Concurrency control
- `approvals` - Approval workflows
- `timeout_policies` - Timeout configurations

#### network_analysis schema
- `network_scans` - Network scan results
- `connectivity_tests` - Ping/traceroute results
- `port_scans` - Port scan results

#### communication schema
- `notification_templates` - Message templates
- `notification_logs` - Delivery history

---

## Security Architecture

### Authentication & Authorization

1. **Keycloak** handles all user authentication
2. **JWT tokens** for API authentication
3. **Role-based access control** (RBAC)
4. **Service-to-service** authentication via shared secrets

### Data Security

1. **Credentials encrypted** at rest (AES-256)
2. **TLS/SSL** for all external connections
3. **Database encryption** for sensitive fields
4. **Secrets management** via environment variables

### Network Security

1. **Kong API Gateway** as single entry point
2. **Internal network** for service communication
3. **No direct external access** to services
4. **Rate limiting** to prevent abuse

---

## Deployment Architecture

### Container Architecture

All services run as Docker containers orchestrated by Docker Compose:

```yaml
networks:
  opsconductor:  # Internal bridge network

volumes:
  postgres_data:  # Persistent database storage
  redis_data:     # Persistent cache storage
  vllm_cache:     # Model cache storage

services:
  - postgres      # Database
  - redis         # Cache/Queue
  - vllm          # LLM inference (GPU)
  - kong          # API Gateway
  - keycloak      # Identity provider
  - ai-pipeline   # AI Pipeline
  - automation-service
  - asset-service
  - network-service
  - communication-service
  - frontend      # React UI
```

### Resource Requirements

**Minimum**:
- CPU: 4 cores
- RAM: 16 GB
- Storage: 100 GB
- GPU: 8 GB VRAM

**Recommended**:
- CPU: 8+ cores
- RAM: 32 GB
- Storage: 200 GB SSD
- GPU: 24 GB VRAM (RTX 3090 Ti or RTX 4090)

### Scaling Considerations

1. **Horizontal scaling**: Multiple instances of services behind load balancer
2. **Database scaling**: Read replicas for query-heavy workloads
3. **Cache scaling**: Redis cluster for high availability
4. **GPU scaling**: Multiple vLLM instances for high throughput

---

## Technology Stack

### Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI
- **Database**: PostgreSQL 17
- **Cache**: Redis 7
- **ORM**: SQLAlchemy
- **Async**: asyncio, aiohttp

### AI/ML
- **Inference**: vLLM 0.11
- **Model**: Qwen2.5-14B-Instruct-AWQ
- **GPU**: CUDA 12.1, NVIDIA Driver 535+

### Frontend
- **Language**: TypeScript 4.9
- **Framework**: React 18.2
- **UI**: Bootstrap 5.3
- **Build**: Webpack

### Infrastructure
- **Containers**: Docker 24.0+
- **Orchestration**: Docker Compose V2
- **API Gateway**: Kong 3.4
- **Identity**: Keycloak 22

### Testing
- **Backend**: pytest, pytest-asyncio
- **E2E**: Playwright
- **Load**: Locust

---

## Design Decisions

### Why 4-Stage Pipeline?

1. **Separation of concerns** - Each stage has a single responsibility
2. **Debuggability** - Easy to trace where issues occur
3. **Flexibility** - Can swap out individual stages
4. **Testability** - Each stage can be tested independently

### Why Microservices?

1. **Domain isolation** - Each service owns its domain
2. **Independent scaling** - Scale services based on load
3. **Technology flexibility** - Use best tool for each service
4. **Team autonomy** - Teams can work independently

### Why vLLM?

1. **Performance** - 10-20x faster than standard inference
2. **Local deployment** - No external API dependencies
3. **Cost** - No per-token pricing
4. **Privacy** - Data stays on-premises
5. **GPU optimization** - Efficient GPU memory usage

### Why PostgreSQL?

1. **JSONB support** - Flexible schema for dynamic data
2. **Full-text search** - Built-in search capabilities
3. **Reliability** - Battle-tested in production
4. **Performance** - Excellent query optimization
5. **Extensions** - Rich ecosystem (PostGIS, pg_trgm, etc.)

---

## Future Enhancements

1. **Multi-tenancy** - Support multiple organizations
2. **Advanced scheduling** - Cron-like job scheduling
3. **Workflow builder** - Visual workflow designer
4. **Advanced analytics** - ML-powered insights
5. **Mobile app** - iOS/Android clients
6. **Plugin system** - Third-party integrations
7. **High availability** - Active-active deployment
8. **Disaster recovery** - Automated backup/restore

---

**Last Updated**: 2024-10-08
**Version**: 1.0