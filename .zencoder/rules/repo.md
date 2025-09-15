---
description: Repository Information Overview
alwaysApply: true
---

# Repository Information Overview

## Repository Summary
OpsConductor NG is a modern, microservices-based IT operations automation platform built with Python FastAPI, React TypeScript, and PostgreSQL. It provides a comprehensive solution for IT asset management, job automation, and workflow generation with AI capabilities.

## Repository Structure
The repository follows a microservices architecture with clear domain boundaries:
- **Backend Services**: Python FastAPI microservices in separate directories
- **Frontend**: React TypeScript application
- **Infrastructure**: Docker Compose for orchestration, Nginx for reverse proxy
- **Database**: PostgreSQL with schema-per-service design

### Main Repository Components
- **API Gateway**: Central routing and authentication service
- **Identity Service**: User authentication and RBAC
- **Asset Service**: IT asset and credential management
- **Automation Service**: Job execution and workflows
- **Communication Service**: Notifications and messaging
- **AI Service**: Natural language processing and workflow generation
- **Frontend**: Modern TypeScript web interface

## Projects

### Backend Services (Python FastAPI)
**Configuration Files**: `requirements.txt`, `Dockerfile` in each service directory

#### Language & Runtime
**Language**: Python 3.11+
**Framework**: FastAPI 0.104.1
**Database**: PostgreSQL 16 with schema-per-service
**Cache/Queue**: Redis 7, Celery 5.3.4

#### Dependencies
**Main Dependencies**:
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- asyncpg==0.29.0
- redis==5.0.1
- structlog==23.2.0
- pydantic==2.5.0
- httpx==0.25.2
- celery==5.3.4 (Automation Service)
- cryptography==41.0.7 (Encryption)

#### Build & Installation
```bash
# Build all services
docker compose build

# Start all services
docker compose up -d
```

#### Docker
**Dockerfile**: Present in each service directory
**Base Image**: python:3.11-slim
**Configuration**: Multi-container setup with Docker Compose

#### Testing
**Health Checks**: Each service has `/health` endpoint
**Run Command**:
```bash
curl http://localhost:3001/health
```

### Frontend (React TypeScript)
**Configuration File**: `frontend/package.json`

#### Language & Runtime
**Language**: TypeScript 4.9.5
**Framework**: React 18.2.0
**Build System**: React Scripts 5.0.1
**Package Manager**: npm

#### Dependencies
**Main Dependencies**:
- react==18.2.0
- react-dom==18.2.0
- react-router-dom==6.20.1
- axios==1.6.2
- bootstrap==5.3.8
- lucide-react==0.542.0
- react-beautiful-dnd==13.1.1

#### Build & Installation
```bash
cd frontend
npm install
npm run build
```

#### Docker
**Dockerfile**: `frontend/Dockerfile`
**Base Image**: node:18-alpine
**Build Command**: npm run build

### Infrastructure
**Configuration Files**: `docker-compose.yml`, `nginx/nginx.conf`

#### Components
**Reverse Proxy**: Nginx with SSL/TLS
**Container Orchestration**: Docker Compose
**Monitoring**: Celery Flower dashboard (Port 5555)
**Database**: PostgreSQL 16 with schema-per-service

#### Key Configuration
**Ports**:
- Frontend: 443 (HTTPS)
- API Gateway: 3001
- Asset Service: 3002
- Automation Service: 3003
- Communication Service: 3004
- AI Service: 3005
- Identity Service: 3006
- Celery Flower: 5555

#### Security
**Authentication**: JWT token-based with refresh tokens
**RBAC**: Role-based access control with permissions
**Encryption**: Fernet encryption for sensitive credentials