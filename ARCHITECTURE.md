# OpsConductor Architecture

## 🏗️ System Overview

OpsConductor is a production-ready microservices architecture built with Python FastAPI, React TypeScript, PostgreSQL, Docker, and NGINX. The system provides comprehensive automation capabilities through modern microservice patterns with enterprise-grade security and scalability.

## 📊 Architecture Diagram

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
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │ Discovery   │  │Step Libraries│                              │
│  │  Service    │  │  Service    │                               │
│  │             │  │             │                               │
│  │ • Network   │  │ • Libraries │                               │
│  │ • Scanning  │  │ • Modules   │                               │
│  │ • Import    │  │ • Catalog   │                               │
│  │             │  │             │                               │
│  │ Port: 3010  │  │ Port: 3011  │                               │
│  │ FastAPI     │  │ FastAPI     │                               │
│  └─────────────┘  └─────────────┘                               │
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
│                    │ • Discovery & Libraries     │              │
│                    │                             │              │
│                    │ Port: 5432                  │              │
│                    └─────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Microservices Architecture

### 1. Frontend Service (Port 3000)
**Technology**: React 18 + TypeScript
- Modern React application with responsive design
- JWT token management and authentication
- Component-based architecture with reusable components
- Real-time updates and WebSocket support
- Visual job builder with drag-and-drop interface

### 2. Auth Service (Port 3001)
**Technology**: Python FastAPI
- JWT token generation and validation
- Password hashing with bcrypt
- Token refresh and revocation mechanisms
- Role-based access control (admin, operator, viewer)
- Session management and security

### 3. User Service (Port 3002)
**Technology**: Python FastAPI
- Complete user CRUD operations
- Role management and permissions
- User profile management
- Search and pagination capabilities
- User preference management

### 4. Credentials Service (Port 3004)
**Technology**: Python FastAPI
- AES-GCM encryption for sensitive data
- Multiple credential types (WinRM, SSH, API keys)
- Secure credential storage and retrieval
- Credential rotation capabilities
- Access control and audit logging

### 5. Targets Service (Port 3005)
**Technology**: Python FastAPI
- Windows and Linux target management
- WinRM and SSH configuration
- Target health monitoring and connection testing
- Target groups with many-to-many relationships
- OS type detection and management

### 6. Jobs Service (Port 3006)
**Technology**: Python FastAPI
- Job definition and management
- Visual job builder integration
- Job execution tracking and history
- Parameter validation and templating
- Job templates and reusable components

### 7. Executor Service (Port 3007)
**Technology**: Python FastAPI
- Multi-protocol job execution (WinRM, SSH, HTTP, SFTP)
- Step-by-step execution tracking
- Real-time execution monitoring
- Integration with credentials and targets
- File transfer capabilities

### 8. Scheduler Service (Port 3008)
**Technology**: Python FastAPI
- Cron-based job scheduling
- Schedule management and triggers
- Job queue management
- Recurring job execution
- Timezone support and validation

### 9. Notification Service (Port 3009)
**Technology**: Python FastAPI
- Multi-channel notifications (Email, Slack, Teams, Webhooks)
- Template-based notification system
- Delivery tracking and retry logic
- SMTP configuration management
- Background worker for async delivery

### 10. Discovery Service (Port 3010)
**Technology**: Python FastAPI
- Automated network discovery with nmap
- Service detection (WinRM, SSH, RDP)
- Bulk target import capabilities
- Discovery job scheduling
- Target classification and validation

### 11. Step Libraries Service (Port 3011)
**Technology**: Python FastAPI
- Modular step library management
- Dynamic library installation and updates
- Version management and compatibility
- Step catalog and documentation
- Performance optimization and caching

## 🗄️ Database Architecture

### PostgreSQL Database Design
All services share a unified PostgreSQL database with optimized schemas:

#### Core Tables
- **users** - User accounts, profiles, and authentication
- **credentials** - Encrypted credential storage with access control
- **targets** - Target server configurations and groups
- **target_groups** - Logical target organization
- **target_group_memberships** - Many-to-many target-group relationships
- **jobs** - Job definitions and metadata
- **job_runs** - Job execution history and status
- **job_run_steps** - Individual step execution tracking
- **schedules** - Job scheduling configuration
- **notifications** - Notification history and templates
- **discovery_jobs** - Network discovery configurations
- **step_libraries** - Modular automation libraries

### Data Security
- **AES-GCM encryption** for sensitive credential data
- **bcrypt password hashing** for user passwords
- **JWT tokens** for stateless authentication
- **Input validation** and SQL injection prevention
- **Audit logging** for security events

## 🔐 Security Architecture

### Multi-Layer Security
1. **Network Security**
   - Docker network isolation
   - SSL/TLS encryption for all external communication
   - No direct database access from outside
   - NGINX security headers and rate limiting

2. **Authentication & Authorization**
   - JWT-based stateless authentication
   - Role-based access control (admin, operator, viewer)
   - Token expiration and refresh mechanisms
   - Service-to-service authentication

3. **Data Protection**
   - AES-GCM encryption for credentials
   - bcrypt password hashing
   - Secure key derivation with PBKDF2
   - Encrypted communication between services

4. **Input Validation**
   - Server-side validation on all endpoints
   - Parameterized queries to prevent SQL injection
   - XSS prevention in frontend
   - CSRF protection

## 🚀 Deployment Architecture

### Container Orchestration
- **Docker Compose** manages all services
- **Multi-stage builds** for optimized container images
- **Persistent volumes** for database data and SSL certificates
- **Custom network** for service communication
- **Environment variable** configuration
- **Health checks** on all containers

### Service Discovery
- **Docker DNS** for service-to-service communication
- **Environment variables** for service URLs
- **Health endpoints** on all services (`/health`)
- **Graceful shutdown** handling
- **Circuit breakers** for resilient communication

### Load Balancing & Scaling
- **NGINX reverse proxy** with load balancing
- **Horizontal scaling** support for stateless services
- **Connection pooling** for database efficiency
- **Caching strategies** for performance optimization

## 📈 Performance & Scalability

### Performance Features
- **Async FastAPI** for high-performance APIs
- **Connection pooling** for database efficiency
- **Stateless services** for easy horizontal scaling
- **Caching strategies** for frequently accessed data
- **Background workers** for async processing

### Monitoring & Observability
- **Structured logging** with JSON format
- **Health check endpoints** on all services
- **Performance metrics** collection
- **Request tracing** across service boundaries
- **Error tracking** and alerting

### Scaling Options
- **Horizontal scaling** - Multiple instances of services
- **Load balancing** - NGINX distributes requests
- **Database optimization** - Indexing and query optimization
- **Container orchestration** - Docker Compose or Kubernetes

## 🔄 Service Communication

### Internal Communication
- **HTTP/REST APIs** for service-to-service communication
- **Standardized response formats** across all services
- **Service authentication** using shared tokens
- **Circuit breakers** for failure handling
- **Retry logic** with exponential backoff

### External APIs
- **OpenAPI/Swagger** documentation for all services
- **Consistent error responses** with proper HTTP status codes
- **API versioning** support for backward compatibility
- **Rate limiting** and throttling

## 🛠️ Development Architecture

### Shared Modules System
All services use shared modules from `/shared/` directory:

- **database.py** - Connection pooling and health monitoring
- **logging.py** - Structured logging with service context
- **middleware.py** - CORS, request logging, error handling
- **models.py** - Standardized Pydantic response models
- **errors.py** - Custom exception classes (replaces HTTPException)
- **auth.py** - JWT validation and role-based access control
- **utils.py** - Common utility functions and HTTP clients

### Service Architecture Pattern
Every service follows a consistent structure:
- Shared module imports
- Structured logging setup
- Standard middleware configuration
- Health check endpoints
- Standardized error handling
- Proper startup/shutdown lifecycle

### Code Quality Standards
- **Type hints** for all functions
- **Comprehensive documentation** with docstrings
- **Unit and integration tests** for all components
- **Error handling** with custom exception classes
- **Logging** for debugging and monitoring
- **Code consistency** across all services

---

**OpsConductor Architecture** - Modern, scalable, and secure microservices platform for enterprise automation.