---
description: Repository Information Overview
alwaysApply: true
---

# Repository Information Overview

## Repository Summary
OpsConductor NG is a production-ready, microservices-based IT operations automation platform built with Python FastAPI, React TypeScript, and PostgreSQL. It provides a comprehensive solution for IT asset management, job automation, workflow generation with AI capabilities, and complete enterprise-grade features including RBAC, audit logging, and hierarchical target management.

## Repository Structure
The repository follows a microservices architecture with clear domain boundaries and is designed for immediate deployment from a fresh git clone:
- **Backend Services**: Python FastAPI microservices with shared base classes
- **Frontend**: Modern React TypeScript application with Material-UI
- **Infrastructure**: Complete Docker Compose orchestration with health checks
- **Database**: PostgreSQL with comprehensive schema and automated initialization
- **Deployment**: Automated build, verification, and deployment scripts

### Main Repository Components
- **API Gateway** (Port 3000): Central routing, authentication, and rate limiting
- **Identity Service** (Port 3001): User authentication, RBAC with 5 roles, session management
- **Asset Service** (Port 3002): Enhanced targets with embedded credentials, hierarchical groups
- **Automation Service** (Port 3003): Job execution, Celery workers, step libraries
- **Communication Service** (Port 3004): Notifications, templates, audit logging
- **AI Service** (Port 3005): Natural language processing and workflow generation
- **Frontend** (Port 3100): Modern TypeScript web interface with enhanced UX

## Projects

### Backend Services (Python FastAPI)
**Configuration Files**: `requirements.txt`, `Dockerfile` in each service directory

#### Language & Runtime
**Language**: Python 3.11+
**Framework**: FastAPI 0.104.1
**Database**: PostgreSQL 16 with comprehensive schema (4 schemas: identity, assets, automation, communication)
**Cache/Queue**: Redis 7, Celery 5.3.4
**Authentication**: JWT with refresh tokens, bcrypt password hashing

#### Dependencies
**Main Dependencies**:
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- asyncpg==0.29.0
- redis==5.0.1
- structlog==23.2.0
- pydantic[email]==2.5.0
- PyJWT==2.8.0
- bcrypt==4.1.2
- httpx==0.25.2
- python-multipart==0.0.6
- cryptography==41.0.7 (Fernet encryption for credentials)
- celery==5.3.4 (Automation Service)
- aiohttp==3.9.1
- email-validator==2.3.0

#### Build & Installation
```bash
# Complete automated setup
./build.sh      # Sets up all services and dependencies
./deploy.sh     # Builds, deploys, and initializes database

# Or manual setup
docker compose build
docker compose up -d
./database/init-db.sh  # Initialize complete database schema
```

#### Docker
**Dockerfile**: Present in each service directory
**Base Image**: python:3.11-slim
**Configuration**: Multi-container setup with Docker Compose

#### Testing & Verification
**Health Checks**: Each service has `/health` endpoint with database connectivity checks
**Verification Script**: `./verify-setup.sh` - Comprehensive pre-deployment verification
**Run Commands**:
```bash
# Verify complete setup
./verify-setup.sh

# Check individual service health
curl http://localhost:3000/health  # API Gateway
curl http://localhost:3001/health  # Identity Service
curl http://localhost:3002/health  # Asset Service
```

### Frontend (React TypeScript)
**Configuration File**: `frontend/package.json`

#### Language & Runtime
**Language**: TypeScript 4.9.5
**Framework**: React 18.2.0 with hooks and context API
**Build System**: React Scripts 5.0.1
**Package Manager**: npm
**UI Framework**: Material-UI with custom theming

#### Dependencies
**Main Dependencies**:
- react==18.2.0
- react-dom==18.2.0
- react-router-dom==6.20.1
- axios==1.6.2
- @mui/material==5.15.0 (Material-UI)
- @mui/icons-material==5.15.0
- @emotion/react==11.11.1
- @emotion/styled==11.11.0
- lucide-react==0.542.0
- react-beautiful-dnd==13.1.1 (Drag & drop)
- react-hook-form==7.48.2 (Form management)

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

### Infrastructure & Database
**Configuration Files**: `docker-compose.yml`, `database/complete-schema.sql`, `database/init-db.sh`

#### Components
**Reverse Proxy**: Nginx with SSL/TLS support
**Container Orchestration**: Docker Compose with health checks
**Monitoring**: Celery Flower dashboard (Port 5555)
**Database**: PostgreSQL 16 with comprehensive schema
**Cache/Queue**: Redis 7 for sessions and Celery tasks

#### Database Schema (Complete)
**Identity Schema**: 
- users, roles, user_roles, user_sessions, user_preferences
- 5 predefined roles: admin, manager, operator, developer, viewer

**Assets Schema**:
- enhanced_targets (new architecture with embedded credentials)
- target_services (31+ predefined service types)
- target_groups (3-level hierarchy with materialized paths)
- target_group_memberships, service_definitions
- Legacy tables: targets, target_credentials (backward compatibility)

**Automation Schema**:
- jobs, job_executions, step_executions, job_schedules
- Complete workflow tracking and scheduling

**Communication Schema**:
- notification_templates, notification_channels, notifications
- audit_logs for comprehensive system auditing

#### Key Configuration
**Ports**:
- Frontend: 3100 (HTTP) / 443 (HTTPS with Nginx)
- API Gateway: 3000
- Identity Service: 3001
- Asset Service: 3002
- Automation Service: 3003
- Communication Service: 3004
- AI Service: 3005
- PostgreSQL: 5432
- Redis: 6379
- Celery Flower: 5555

#### Security & Features
**Authentication**: JWT token-based with refresh tokens, session management
**RBAC**: Complete role-based access control with granular permissions
**Encryption**: Fernet encryption for sensitive credentials and secrets
**Audit Logging**: Comprehensive audit trail for all system operations
**Data Integrity**: Database triggers, constraints, and validation
**Default Admin**: admin/admin123 for immediate access

## Latest Improvements & Deployment

### Production-Ready Features (Latest)
- **Complete Database Schema**: Single `complete-schema.sql` with all tables, triggers, and initial data
- **Automated Initialization**: `init-db.sh` script for database setup and verification
- **Enhanced Target Management**: New architecture with embedded credentials and hierarchical groups
- **Service Definitions**: 31+ predefined service types (SSH, RDP, HTTP, databases, etc.)
- **Comprehensive RBAC**: 5 roles with granular permissions for enterprise use
- **Audit Logging**: Complete system audit trail with user tracking
- **Session Management**: JWT with refresh tokens and session tracking
- **Verification System**: Pre-deployment verification with `verify-setup.sh`

### Deployment Scripts
- **`build.sh`**: Complete system build with dependency management
- **`deploy.sh`**: Automated deployment with health checks and database initialization
- **`verify-setup.sh`**: Pre-deployment verification of all components
- **`database/init-db.sh`**: Database initialization with integrity checks

### Fresh Installation Ready
The repository is designed for immediate deployment from a fresh git clone:
1. Clone repository
2. Run `./verify-setup.sh` (optional verification)
3. Run `./build.sh` (builds all components)
4. Run `./deploy.sh` (deploys and initializes)
5. Access http://localhost:3100 with admin/admin123

### Configuration Management
- **`.env.example`**: Complete environment configuration template
- **Environment Variables**: All services support environment-based configuration
- **Docker Compose**: Health checks, dependency management, and volume persistence
- **Nginx Configuration**: SSL/TLS ready with reverse proxy setup