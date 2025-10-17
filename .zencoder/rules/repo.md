---
description: Repository Information Overview
alwaysApply: true
---

# Repository Information Overview

## Repository Summary
OpsConductor NG is an AI-powered IT operations automation platform that uses a 4-stage AI pipeline to understand natural language requests and execute complex IT operations. The system follows a clean architecture approach with specialized microservices for execution, while the AI Brain makes decisions.

## Repository Structure
- **pipeline/**: Core AI decision-making system with 4-stage pipeline (merged A+B stages)
- **automation-service/**: Command execution service with clean architecture
- **asset-service/**: Infrastructure asset management
- **network-analyzer-service/**: Network monitoring and analysis
- **communication-service/**: Notifications and alerts
- **frontend/**: React TypeScript web interface
- **shared/**: Common utilities and base classes for services
- **kong/**: API Gateway configuration
- **keycloak/**: Identity provider configuration
- **tests/**: Comprehensive test suite for all components

### Main Repository Components
- **AI Pipeline** (Port 8006): 4-stage LLM-driven decision engine
- **Kong API Gateway** (Port 8008): Centralized routing and authentication
- **Keycloak** (Port 8080): Identity and access management
- **Automation Service** (Port 8005): Command execution
- **Asset Service** (Port 8002): Infrastructure management
- **Network Service** (Port 8003): Network analysis
- **Communication Service** (Port 8004): Notifications
- **Frontend** (Port 8000): Web interface

## Docker Configuration
**Main Dockerfile**: `Dockerfile` (Python 3.11 slim)
**Specialized Dockerfiles**:
- `Dockerfile.vllm.3090ti`: Optimized for NVIDIA RTX 3090 Ti GPU
- `automation-service/Dockerfile.clean`: Clean architecture automation service
- `asset-service/Dockerfile`: Asset management service
- `network-analyzer-service/Dockerfile`: Network analysis service
- `communication-service/Dockerfile`: Notification service
- `frontend/Dockerfile`: React frontend

**Docker Compose**: `docker-compose.yml` with override options:
- `override.clean.yml`: Simplified deployment configuration
- `override.pgvector.yml`: PostgreSQL with vector extensions

**Network Configuration**:
- Custom bridge network (172.28.0.0/16)
- Fixed IP addresses for service discovery
- Internal service communication

**Volumes**:
- `postgres_data`: Database persistence
- `redis_data`: Cache persistence
- `ollama_models`: LLM model storage

**GPU Configuration**:
- NVIDIA GPU with 8GB+ VRAM required
- Recommended: RTX 3090 Ti (24GB) or RTX 4090 (24GB)
- CUDA 12.1 runtime with nvidia-container-toolkit

## Projects

### AI Pipeline (4-Stage Architecture)
**Configuration Files**: `main.py`, `requirements.txt`, `Dockerfile`

#### Language & Runtime
**Language**: Python 3.11
**Framework**: FastAPI 0.104.1
**LLM Integration**: Ollama 0.11.11 with Qwen2.5 7B model
**Database**: PostgreSQL 17 with pgvector 0.4.1

#### Architecture
**Key Components**:
- **Stage AB (Combined)**: Intent classification and tool selection
- **Stage C (Planner)**: Execution planning
- **Stage D (Answerer)**: Response formatting
- **Stage E (Executor)**: Integrated execution

#### Dependencies
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- pydantic==2.5.0
- httpx==0.25.2
- asyncpg==0.29.0
- sqlalchemy[asyncio]==2.0.23
- redis[hiredis]==5.0.1
- sentence-transformers==5.1.0
- pgvector==0.4.1

### Backend Services (Python FastAPI)
**Configuration Files**: `requirements.txt`, `Dockerfile` in each service directory

#### Language & Runtime
**Language**: Python 3.11/3.12
**Framework**: FastAPI
**Database**: PostgreSQL 17
**Cache/Queue**: Redis 7

#### Key Services
- **Automation Service**: Clean architecture execution service
- **Asset Service**: Infrastructure asset management
- **Network Analyzer**: Network monitoring and analysis
- **Communication Service**: Notifications and alerts

#### Dependencies
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- pydantic==2.5.0
- asyncpg==0.29.0
- redis==5.0.1
- httpx==0.25.2
- paramiko==3.4.0 (SSH connections)
- pywinrm==0.4.3 (Windows PowerShell)

### Infrastructure
**Configuration Files**: `docker-compose.yml`

#### Components
**Database**: PostgreSQL 17 with pgvector
**Message Queue**: Redis 7
**LLM Server**: Ollama 0.11.11 with Qwen2.5-7B-Instruct model
**API Gateway**: Kong 3.4
**Identity Provider**: Keycloak 22.0.1

#### Deployment
```bash
# Standard deployment
docker compose up -d

# View logs
docker compose logs -f

# Service-by-service startup (for debugging)
docker compose up -d postgres redis kong keycloak
sleep 30
docker compose up -d ollama
sleep 120
docker compose up -d automation-service asset-service network-service communication-service
docker compose up -d ai-pipeline
docker compose up -d frontend
```

## Testing Framework
**Framework**: pytest 7.4.3 with pytest-asyncio 0.21.1
**Test Location**: `tests/`
**Key Test Files**:
- `tests/test_phase_*`: Pipeline stage tests
- `tests/test_ai_functional_performance.py`: Performance tests
- `tests/e2e/`: End-to-end tests with Playwright

**Run Command**:
```bash
pytest tests/
```