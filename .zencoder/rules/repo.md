---
description: Repository Information Overview
alwaysApply: true
---

# Repository Information Overview

## Repository Summary
OpsConductor NG is an IT operations automation platform with a clean architecture approach. The system uses a 4-stage AI pipeline powered by Ollama LLM for decision making, with specialized microservices for execution. The architecture follows a clear separation of concerns with the AI Brain making decisions, while specialized services handle execution.

## Repository Structure
- **ai-pipeline**: Core AI decision-making system with 4-stage pipeline
- **automation-service**: Command execution service with clean architecture
- **asset-service**: Infrastructure asset management
- **network-analyzer-service**: Network monitoring and analysis
- **communication-service**: Notifications and alerts
- **identity-service**: User management with Keycloak integration
- **frontend**: React TypeScript web interface
- **shared**: Common utilities and base classes for services
- **kong**: API Gateway configuration
- **keycloak**: Identity provider configuration

### Main Repository Components
- **AI Pipeline** (Port 3005): 4-stage LLM-driven decision engine
- **Kong API Gateway** (Port 3000): Centralized routing and authentication
- **Keycloak** (Port 8090): Identity and access management
- **Automation Service** (Port 3003): Command execution
- **Asset Service** (Port 3002): Infrastructure management
- **Network Service** (Port 3006): Network analysis
- **Communication Service** (Port 3004): Notifications
- **Frontend** (Port 3100): Web interface

## Projects

### AI Pipeline (4-Stage Architecture)
**Configuration Files**: `main.py`, `requirements.txt`, `Dockerfile`

#### Language & Runtime
**Language**: Python 3.12+
**Framework**: FastAPI 0.104.1
**LLM Integration**: Ollama 0.11.11 with Qwen2.5 model
**Database**: PostgreSQL 17

#### Architecture
**Key Components**:
- **Stage A (Classifier)**: Intent classification
- **Stage B (Selector)**: Tool selection
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

### Backend Services (Python FastAPI)
**Configuration Files**: `requirements.txt`, `Dockerfile` in each service directory

#### Language & Runtime
**Language**: Python 3.12+
**Framework**: FastAPI
**Database**: PostgreSQL 17
**Cache/Queue**: Redis 7.4

#### Key Services
- **Automation Service**: Clean architecture execution service
- **Asset Service**: Infrastructure asset management
- **Network Analyzer**: Network monitoring and analysis
- **Communication Service**: Notifications and alerts

#### Dependencies
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- pydantic[email]==2.5.0
- asyncpg==0.29.0
- redis==5.0.1
- httpx==0.25.2
- paramiko==3.4.0 (SSH connections)
- pywinrm==0.4.3 (Windows PowerShell)

### Frontend (React TypeScript)
**Configuration File**: `frontend/package.json`

#### Language & Runtime
**Language**: TypeScript 4.9.5
**Framework**: React 18.2.0
**UI Components**: Bootstrap 5.3.8, Lucide React 0.542.0
**Data Grid**: AG Grid 32.3.9

#### Dependencies
- react==18.2.0
- typescript==4.9.5
- bootstrap==5.3.8
- ag-grid-react==32.3.9
- lucide-react==0.542.0
- axios==1.6.2

#### Build & Installation
```bash
cd frontend
npm install
npm start
```

### Infrastructure
**Configuration Files**: `docker-compose.yml`

#### Components
**Database**: PostgreSQL 17
**Message Queue**: Redis 7.4
**LLM Server**: Ollama 0.11.11
**API Gateway**: Kong 3.4
**Identity Provider**: Keycloak 22.0.1

#### Deployment
```bash
# Standard deployment
docker-compose up -d

# Development with live reload
./scripts/dev-mode.sh
```

## Testing Framework
**Framework**: pytest 7.4.3 with pytest-asyncio
**Test Location**: `tests/`
**Key Test Files**:
- `tests/test_phase_*`: Pipeline stage tests
- `tests/test_ai_functional_performance.py`: Performance tests

**Run Command**:
```bash
pytest tests/
```