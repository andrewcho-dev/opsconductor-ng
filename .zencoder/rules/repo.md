---
description: Repository Information Overview
alwaysApply: true
---

# OpsConductor Microservice System Information

## Repository Summary
A comprehensive microservices-based automation platform for managing Windows and Linux environments, job scheduling, execution, and monitoring. The system follows a modern architecture with 10 independent microservices, each with specific responsibilities, supporting both Windows (via WinRM) and Linux (via SSH) target management with enterprise-grade security and scalability.

## Repository Structure
- **auth-service**: JWT authentication and authorization (Port 3001)
- **user-service**: User management and profiles (Port 3002)
- **credentials-service**: Secure credential storage with AES-GCM encryption (Port 3004)
- **targets-service**: Windows/Linux target management with groups (Port 3005)
- **jobs-service**: Job definition and management (Port 3006)
- **executor-service**: Job execution via WinRM/SSH with file operations (Port 3007)
- **scheduler-service**: Cron-based job scheduling with timezone support (Port 3008)
- **notification-service**: Multi-channel notifications (Email, Slack, Teams, Webhooks) (Port 3009)
- **discovery-service**: Network scanning and automated target discovery (Port 3010)
- **step-libraries-service**: Reusable automation step libraries (Port 3011)
- **frontend**: React TypeScript UI with responsive design (Port 3000)
- **nginx**: Reverse proxy and SSL termination (Ports 80/443)
- **database**: PostgreSQL 16 with comprehensive schema
- **rabbitmq**: Message queue for job execution (Ports 5672/15672)

## Projects

### Backend Services (Python FastAPI)

#### Language & Runtime
**Language**: Python
**Version**: 3.11
**Framework**: FastAPI 0.104.1
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- fastapi==0.104.1
- uvicorn==0.24.0
- psycopg2-binary==2.9.9
- python-jose[cryptography]==3.3.0 (auth-service)
- passlib[bcrypt]==1.7.4 (auth-service)
- pywinrm==0.4.3 (executor-service)
- paramiko==3.4.0 (executor-service, for SSH)
- jinja2==3.1.2 (executor-service, for templates)
- pydantic==2.5.0
- python-dotenv==1.0.0
- aiohttp==3.9.1 (executor-service, for async HTTP)

#### Build & Installation
```bash
pip install -r requirements.txt
python main.py
```

#### Docker
**Dockerfile**: Each service has its own Dockerfile
**Base Image**: python:3.11-slim
**Configuration**: Services are containerized and orchestrated with docker-compose
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
- typescript==4.9.5

#### Build & Installation
```bash
npm install
npm start  # Development
npm run build  # Production
```

#### Docker
**Dockerfile**: frontend/Dockerfile
**Base Image**: node:18-alpine
**Configuration**: Serves React application on port 3000

## Testing
**Framework**: Playwright (TypeScript)
**Test Location**: tests/e2e
**Test Files**: 12 test files covering all major functionality
**Configuration**: playwright.config.ts
**Run Command**:
```bash
cd tests
npm install
npx playwright test
```

## System Configuration

### Database
- **Engine**: PostgreSQL 16 (Alpine)
- **Configuration**: Initialized with schema from database/init-schema.sql
- **Migrations**: database/migrations folder contains schema updates
- **Connection**: Environment variables in docker-compose.yml

### Docker Compose
**Main File**: docker-compose.yml
**Network**: Bridge network (opsconductor-net)
**Volumes**: 
  - postgres_data: Persistent PostgreSQL data
  - nginx_ssl: SSL certificates
  - step_libraries_data: Automation libraries
  - step_libraries_cache: Library cache

### Environment Variables
Key variables defined in .env:
- Database connection (DB_HOST, DB_USER, etc.)
- JWT configuration (JWT_SECRET_KEY)
- Service URLs for inter-service communication
- SMTP settings for notification service
- Encryption keys for credential storage

### Startup
```bash
# Start all services
./start-python-system.sh

# Or manually
docker-compose up -d
```

### Monitoring
- Health check endpoints on all services
- System status script: ./system-status.sh
- Service dependency management in docker-compose
- RabbitMQ management UI at http://localhost:15672

## Current System Status
**Phase 11 Complete**: Target Groups & UI Improvements with Advanced Scheduler Removal
- ✅ 10 microservices operational with health monitoring
- ✅ Multi-platform support (Windows WinRM, Linux SSH)
- ✅ Target groups with logical organization
- ✅ Network discovery and automated target onboarding
- ✅ Multi-channel notification system
- ✅ Visual job builder with drag-and-drop interface
- ✅ Enterprise security (AES-GCM encryption, JWT authentication)
- ✅ Production deployment with HTTPS and SSL
- ✅ Comprehensive testing suite with Playwright