---
description: Repository Information Overview
alwaysApply: true
---

# OpsConductor Rebuilt System Information

## Repository Summary
A modernized, domain-driven microservices platform for Windows and Linux automation, featuring a consolidated architecture that reduces complexity while maintaining all functionality. The rebuilt system transforms the original 10 microservices into 4 domain-focused services with a central API gateway, improving maintainability, scalability, and development velocity.

## Repository Structure
- **api-gateway**: Central entry point for all API requests (Port 3000)
- **identity-service**: Authentication, authorization, and user management (Port 3001)
- **asset-service**: Target systems, credentials, and network discovery (Port 3002)
- **automation-service**: Job management, execution, and step libraries (Port 3003)
- **communication-service**: Multi-channel notifications and integrations (Port 3004)
- **frontend**: React TypeScript UI with responsive design
- **nginx**: Reverse proxy and SSL termination (Ports 80/443)
- **database**: PostgreSQL 16 with schema-per-service design
- **shared**: Common service foundation and utilities

## Projects

### Backend Services (Python FastAPI)

#### Language & Runtime
**Language**: Python
**Version**: 3.11+
**Framework**: FastAPI 0.104.1
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- asyncpg==0.29.0
- redis==5.0.1
- structlog==23.2.0
- pydantic[email]==2.5.0
- PyJWT==2.8.0
- httpx==0.25.2
- celery==5.3.4 (automation-service)
- cryptography==41.0.7 (asset-service)
- aiosmtplib==3.0.1 (communication-service)

#### Build & Installation
```bash
cd /home/opsconductor/rebuild
./build.sh
./deploy.sh
```

#### Docker
**Dockerfile**: Each service has its own Dockerfile
**Base Image**: Python 3.11 with optimized dependencies
**Configuration**: Services are containerized with Docker Compose
**Health Checks**: All services implement /health endpoints

### Frontend (React TypeScript)

#### Language & Runtime
**Language**: TypeScript
**Version**: TypeScript 4.9.5
**Framework**: React 18.2.0
**Package Manager**: npm

#### Dependencies
**Main Dependencies**:
- react==18.2.0
- react-dom==18.2.0
- react-router-dom==6.20.1
- axios==1.6.2
- bootstrap==5.3.8
- lucide-react==0.542.0

#### Build & Installation
```bash
cd frontend
npm install
npm run build
```

## System Configuration

### Database
- **Engine**: PostgreSQL 16 (Alpine)
- **Design**: Schema-per-service architecture
  - `identity` schema - User and authentication data
  - `assets` schema - Targets, credentials, and discovery data
  - `automation` schema - Jobs, workflows, and execution data
  - `communication` schema - Notifications, templates, and audit logs
- **Configuration**: Initialized with schema from database/init-schema.sql

### Job Processing
- **Framework**: Celery 5.3.4 with Redis backend
- **Worker Configuration**: Concurrency of 4 workers
- **Monitoring**: Flower dashboard on port 5555
- **Beat Scheduler**: Handles all recurring jobs

### Docker Compose
**Main File**: docker-compose.yml
**Network**: Bridge network (opsconductor-net)
**Volumes**: 
  - postgres_data: Persistent PostgreSQL data
  - redis_data: Persistent Redis data
  - automation_libraries: Automation libraries
  - scheduler_data: Persistent scheduler data

### Security & Authentication
**API Gateway**: Central authentication and routing
**Authentication Flow**:
- JWT tokens with refresh token rotation
- Role-based access control (RBAC)
- Resource-based authorization
- Multi-factor authentication support

### Environment Variables
Key variables defined in docker-compose.yml:
- Database connection (DB_HOST, DB_USER, etc.)
- JWT configuration (JWT_SECRET_KEY)
- Service URLs for inter-service communication
- SMTP settings for notification service
- Encryption keys for credential storage
- Redis URL for caching and messaging

### Startup
```bash
cd /home/opsconductor/rebuild
./deploy.sh
```

### Monitoring
- Health check endpoints on all services
- Structured JSON logging with structlog
- Prometheus-compatible metrics (ready)
- Celery Flower dashboard at http://localhost:5555

## Architecture Improvements
- **Service Reduction**: 10 services → 4 core services + 1 gateway (44% reduction)
- **Domain-Driven Design**: Clear boundaries and responsibilities
- **Improved Scalability**: Independent scaling per domain
- **Enhanced Maintainability**: Domain-focused development
- **Better Performance**: Fewer network hops and optimized data access
- **Operational Simplicity**: Comprehensive health checks and monitoring