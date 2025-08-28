# 🏗️ OpsConductor System Overview

## 📋 System Summary

OpsConductor is a **production-ready microservice architecture** built with Python FastAPI, React TypeScript, PostgreSQL, Docker, and Nginx. The system provides comprehensive Windows management, job scheduling, and automation capabilities through modern microservice patterns.

### 🎯 Key Features
- ✅ **Microservices Architecture** - 8 independent services with clear separation of concerns
- ✅ **Python FastAPI Backend** - High-performance async API services
- ✅ **React TypeScript Frontend** - Modern, responsive web interface
- ✅ **JWT Authentication** - Stateless security across services
- ✅ **SSL/HTTPS** - Secure communication with nginx reverse proxy
- ✅ **Windows Management** - Remote Windows server management via WinRM
- ✅ **Job Scheduling** - Advanced job scheduling and execution system
- ✅ **Email Notifications** - SMTP-based notification system
- ✅ **Containerized Deployment** - Full Docker containerization

---

## 🏛️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL ACCESS                             │
│  Browser/Client → https://localhost:8443 (SSL/TLS)             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NGINX GATEWAY                                │
│  • SSL Termination (HTTPS → HTTP)                              │
│  • Request Routing & Load Balancing                            │
│  • Security Headers & Rate Limiting                            │
│  Ports: 8080 (HTTP), 8443 (HTTPS)                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 MICROSERVICES LAYER                             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Frontend   │  │    Auth     │  │    User     │              │
│  │  (React)    │  │  Service    │  │  Service    │              │
│  │             │  │             │  │             │              │
│  │ • React UI  │  │ • Login     │  │ • User CRUD │              │
│  │ • TypeScript│  │ • JWT Auth  │  │ • Profile   │              │
│  │ • Routing   │  │ • Token Val │  │ • Search    │              │
│  │             │  │             │  │ • Roles     │              │
│  │ Port: 3000  │  │ Port: 3001  │  │ Port: 3002  │              │
│  │ React/TS    │  │ FastAPI     │  │ FastAPI     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │Credentials  │  │  Targets    │  │    Jobs     │              │
│  │  Service    │  │  Service    │  │  Service    │              │
│  │             │  │             │  │             │              │
│  │ • Cred CRUD │  │ • Target Mgmt│  │ • Job Defn  │              │
│  │ • Encryption│  │ • WinRM Cfg │  │ • Job Runs  │              │
│  │ • Security  │  │ • SSH Cfg   │  │ • History   │              │
│  │             │  │             │  │             │              │
│  │ Port: 3004  │  │ Port: 3005  │  │ Port: 3006  │              │
│  │ FastAPI     │  │ FastAPI     │  │ FastAPI     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Executor   │  │ Scheduler   │  │Notification │              │
│  │  Service    │  │  Service    │  │  Service    │              │
│  │             │  │             │  │             │              │
│  │ • Job Exec  │  │ • Cron Jobs │  │ • Email     │              │
│  │ • WinRM     │  │ • Triggers  │  │ • SMTP      │              │
│  │ • SSH       │  │ • Queue     │  │ • Templates │              │
│  │             │  │             │  │             │              │
│  │ Port: 3007  │  │ Port: 3008  │  │ Port: 3009  │              │
│  │ FastAPI     │  │ FastAPI     │  │ FastAPI     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                               │
│                                                                 │
│                    ┌─────────────────────────────┐              │
│                    │      PostgreSQL Database    │              │
│                    │                             │              │
│                    │ • Users & Authentication    │              │
│                    │ • Credentials (Encrypted)   │              │
│                    │ • Targets & Configuration   │              │
│                    │ • Jobs & Execution History  │              │
│                    │ • Schedules & Triggers      │              │
│                    │ • Notifications & Templates │              │
│                    │                             │              │
│                    │ Port: 5432                  │              │
│                    └─────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Services Detailed

### 1. 🌐 Frontend Service (Port 3000)
**Technology**: React 18 + TypeScript
- Modern React application with TypeScript
- Responsive design with component-based architecture
- JWT token management and authentication
- Complete UI for all system features

### 2. 🔐 Auth Service (Port 3001)
**Technology**: Python FastAPI
- JWT token generation and validation
- Password hashing with bcrypt
- Token refresh and revocation
- Role-based access control

### 3. 👥 User Service (Port 3002)
**Technology**: Python FastAPI
- Complete user CRUD operations
- Role management (admin, operator, viewer)
- User profile management
- Search and pagination

### 4. 🔑 Credentials Service (Port 3004)
**Technology**: Python FastAPI
- AES-GCM encryption for sensitive data
- Multiple credential types (WinRM, SSH, API keys)
- Secure credential storage and retrieval
- Credential rotation capabilities

### 5. 🎯 Targets Service (Port 3005)
**Technology**: Python FastAPI
- Windows and Linux target management
- WinRM and SSH configuration
- Target health monitoring
- OS type detection and management

### 6. 📋 Jobs Service (Port 3006)
**Technology**: Python FastAPI
- Job definition and management
- Job execution tracking
- Parameter validation
- Job run history and status

### 7. ⚡ Executor Service (Port 3007)
**Technology**: Python FastAPI
- Job execution engine
- WinRM and SSH execution
- Step-by-step execution tracking
- Integration with credentials and targets

### 8. ⏰ Scheduler Service (Port 3008)
**Technology**: Python FastAPI
- Cron-based job scheduling
- Schedule management and triggers
- Job queue management
- Recurring job execution

### 9. 📧 Notification Service (Port 3009)
**Technology**: Python FastAPI
- SMTP email notifications
- Notification templates
- Job status notifications
- SMTP configuration management

### 10. 🚪 Nginx Gateway (Ports 8080/8443)
**Technology**: Nginx
- SSL/TLS termination
- Reverse proxy and load balancing
- Request routing to services
- Security headers and rate limiting

---

## 🗄️ Database Architecture

### Unified PostgreSQL Database
All services share a single PostgreSQL database with separate schemas/tables:

#### Core Tables
- **users** - User accounts and profiles
- **credentials** - Encrypted credential storage
- **targets** - Target server configurations
- **jobs** - Job definitions and metadata
- **job_runs** - Job execution history
- **schedules** - Job scheduling configuration
- **notifications** - Notification history and templates

### Data Security
- **AES-GCM encryption** for sensitive credential data
- **bcrypt password hashing** for user passwords
- **JWT tokens** for stateless authentication
- **Input validation** and SQL injection prevention

---

## 🔐 Security Architecture

### Multi-Layer Security
1. **Network Security**
   - Docker network isolation
   - SSL/TLS encryption for all external communication
   - No direct database access from outside

2. **Authentication & Authorization**
   - JWT-based stateless authentication
   - Role-based access control (admin, operator, viewer)
   - Token expiration and refresh mechanisms

3. **Data Protection**
   - AES-GCM encryption for credentials
   - bcrypt password hashing
   - Secure key derivation with PBKDF2

4. **Input Validation**
   - Server-side validation on all endpoints
   - Parameterized queries to prevent SQL injection
   - XSS prevention in frontend

---

## 🚀 Deployment & Operations

### Container Orchestration
- **Docker Compose** manages all services
- **Persistent volumes** for database data
- **Custom network** for service communication
- **Environment variable** configuration

### Service Discovery
- **Docker DNS** for service-to-service communication
- **Health checks** on all services
- **Graceful shutdown** handling

### Monitoring
- **Health endpoints** on all services (`/health`)
- **System status** monitoring via web UI
- **Service logs** via Docker Compose

---

## 🧪 Testing

### Test Scripts
- `./test-sprint1.sh` - Complete system functionality test
- `./test-python-rebuild.sh` - Service rebuild verification
- `./test-user-management.sh` - User management CRUD tests
- `./system-status.sh` - System health check

### Test Coverage
- User authentication and authorization
- CRUD operations for all entities
- Job execution and scheduling
- Email notifications
- Service health and communication

---

## 📈 Scalability & Performance

### Performance Features
- **Async FastAPI** for high-performance APIs
- **Connection pooling** for database efficiency
- **Stateless services** for easy horizontal scaling
- **Caching strategies** for frequently accessed data

### Scaling Options
- **Horizontal scaling** - Multiple instances of services
- **Load balancing** - Nginx distributes requests
- **Database optimization** - Indexing and query optimization
- **Container orchestration** - Docker Compose or Kubernetes

---

## 🛠️ Development

### Technology Stack
- **Backend**: Python 3.11 + FastAPI + PostgreSQL
- **Frontend**: React 18 + TypeScript + Axios
- **Infrastructure**: Docker + Nginx + SSL
- **Database**: PostgreSQL 16

### Development Workflow
1. **Service Development** - Each service is independently developed
2. **API-First Design** - OpenAPI/Swagger documentation
3. **Container-Based** - All services run in Docker containers
4. **Environment Configuration** - `.env` file management

### Adding New Services
1. Use the service template in `service-template/`
2. Follow the [Add New Service Guide](ADD_NEW_SERVICE_GUIDE.md)
3. Update docker-compose configuration
4. Add nginx routing configuration

---

**OpsConductor** - Modern microservices architecture for Windows management and automation.