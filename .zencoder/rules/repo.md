---
description: Repository Information Overview
alwaysApply: true
---

# Repository Information Overview

## Repository Summary
OpsConductor NG is a production-ready IT operations automation platform with advanced AI capabilities. The architecture uses Kong API Gateway, Keycloak for identity management, and a pure LLM-driven AI brain that eliminates hardcoded logic in favor of intelligent service orchestration.

## Repository Structure
The repository follows a microservices architecture with enhanced AI capabilities:
- **Backend Services**: Python FastAPI microservices with shared base classes
- **Frontend**: React TypeScript application with Bootstrap components
- **Infrastructure**: Docker Compose orchestration with GPU support
- **AI System**: Pure LLM-powered brain with Ollama integration
- **Identity**: Keycloak-based enterprise identity management
- **API Gateway**: Kong for centralized routing and authentication

### Main Repository Components
- **Kong API Gateway** (Port 3000): Centralized routing and authentication
- **Keycloak** (Port 8090): Enterprise identity and access management
- **Identity Service** (Port 3001): User management with Keycloak integration
- **Asset Service** (Port 3002): Infrastructure asset management with encryption
- **Automation Service** (Port 3003): Job execution and workflow management
- **Communication Service** (Port 3004): Notifications and audit logging
- **AI Brain** (Port 3005): Pure LLM-driven intelligence with Ollama integration
- **Network Analyzer** (Port 3006): Network monitoring and analysis
- **Frontend** (Port 3100): Modern web interface

## Projects

### AI Brain (Pure LLM Architecture)
**Configuration Files**: `ai-brain/main.py`, `ai-brain/requirements.txt`

#### Language & Runtime
**Language**: Python 3.12+
**Framework**: FastAPI 0.117.1
**LLM Integration**: Ollama 0.4.7 with CodeLLama 7B model
**Vector Database**: ChromaDB 0.6.1 for knowledge storage

#### Architecture
**Key Components**:
- **Intent Brain**: Pure LLM-based intent understanding
- **Fulfillment Engine**: Direct execution of user requests
- **Direct Executor**: Ollama-driven service orchestration
- **Service Catalog**: Dynamic service discovery
- **No Hardcoded Logic**: All decisions made by LLM

#### Dependencies
- fastapi==0.117.1
- uvicorn==0.24.0
- pydantic>=2.8.0
- chromadb==0.6.1
- ollama==0.4.7
- prefect>=3.0.0
- sentence-transformers>=3.3.1

### Backend Services (Python FastAPI)
**Configuration Files**: `requirements.txt`, `Dockerfile` in each service directory

#### Language & Runtime
**Language**: Python 3.12+
**Framework**: FastAPI
**Database**: PostgreSQL 17 with 5 schemas
**Cache/Queue**: Redis 7.4
**Authentication**: Keycloak integration with OAuth2

#### Key Services
- **Asset Service**: Asset management with embedded credentials
- **Automation Service**: Job execution with WebSocket updates
- **Network Analyzer**: Network monitoring with remote probes
- **Communication Service**: Notifications and audit logging

### Identity Management (Keycloak)
**Configuration Files**: `keycloak/Dockerfile`, `keycloak/opsconductor-realm.json`

#### Features
**Authentication**: OAuth2/OpenID Connect
**User Management**: Complete user lifecycle
**Role-Based Access**: Fine-grained permissions
**Integration**: Native integration with Kong API Gateway

### API Gateway (Kong)
**Configuration Files**: `kong/Dockerfile`, `kong/kong.yml`

#### Features
**Routing**: Centralized API routing
**Authentication**: OAuth2 with Keycloak
**Rate Limiting**: Request throttling
**Configuration**: Declarative YAML configuration

### Frontend (React TypeScript)
**Configuration File**: `frontend/package.json`

#### Language & Runtime
**Language**: TypeScript 4.9.5
**Framework**: React 18.2.0
**UI Components**: Bootstrap 5.3.8, Lucide React 0.542.0
**Data Grid**: AG Grid 32.3.9 for advanced data display

#### Key Pages
- **AIChat**: Natural language interface
- **Assets**: Infrastructure management
- **Jobs**: Automation workflow management
- **Dashboard**: System overview and metrics

### Infrastructure & Database
**Configuration Files**: `docker-compose.yml`, `database/complete-schema.sql`

#### Components
**Database**: PostgreSQL 17 with 5 schemas
**Message Queue**: Redis 7.4 for service communication
**LLM Server**: Ollama 0.11.11 for local model serving
**Vector Database**: ChromaDB 0.6.1 for AI knowledge storage
**Reverse Proxy**: Traefik for SSL termination and routing

#### Database Schema
**5 Schemas**:
- **identity**: User management (integrated with Keycloak)
- **assets**: Consolidated asset management
- **automation**: Job execution and scheduling
- **communication**: Notifications and audit logs
- **network_analysis**: Network monitoring and diagnostics

### Network Analysis System
**Configuration Files**: `network-analyzer-service/main.py`, `network-analytics-probe/main.py`

#### Features
**Remote Probes**: Distributed network monitoring
**Packet Analysis**: Deep packet inspection
**Protocol Analysis**: Application-layer visibility
**AI Analysis**: Intelligent anomaly detection

## Deployment & Operations

### Deployment Options
```bash
# Standard deployment
./deploy.sh

# With GPU acceleration for AI
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# With monitoring stack
./start-monitoring.sh
```

### Advanced Features
- **GPU Acceleration**: NVIDIA GPU support for LLM performance
- **Traefik Integration**: Primary reverse proxy solution (deploy-traefik.sh)
- **ELK Stack**: Optional logging infrastructure (deploy-elk.sh)
- **Redis Streams**: Advanced message processing (deploy-redis-streams.sh)
- **Remote Probes**: Distributed network monitoring agents

### Security Features
- **Keycloak Authentication**: Enterprise-grade identity
- **Credential Encryption**: Fernet encryption for sensitive data
- **RBAC**: Role-based access with fine-grained permissions
- **Audit Logging**: Comprehensive activity tracking
- **TLS/SSL**: Secure communication with certificate management

## Testing Framework

### E2E Testing (Python-based)
**Framework**: Python asyncio with httpx for HTTP testing
**Test Location**: `tests/e2e/`
**Target Framework**: Python-based integration tests for microservices
**Key Features**:
- Comprehensive AI Brain → Prefect → Automation Engine integration testing
- Incremental difficulty scaling (1-10 difficulty levels)
- Real-time monitoring of service interactions
- Detailed logging and reporting
- JSON-based test result storage