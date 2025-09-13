# 🏗️ OpsConductor - Architecture Design

## 📊 System Overview

OpsConductor is a modern, domain-driven microservices platform for IT operations automation. The architecture follows a consolidated approach with 4 core domain services and a central API gateway, providing a balance between service isolation and operational simplicity.

## 🎯 Design Principles

### 1. **Domain-Driven Design**
- Services organized by business domains
- Clear boundaries and responsibilities
- Minimal cross-service dependencies

### 2. **Modern Microservices Patterns**
- API Gateway pattern
- Service mesh ready
- Event-driven architecture
- CQRS where appropriate

### 3. **Operational Excellence**
- Health checks and observability
- Graceful degradation
- Circuit breakers
- Distributed tracing ready

## 🏛️ Service Architecture

### **Core Services (4 Services)**

#### 1. **Identity Service** (Port 3001)
**Domain**: Authentication, Authorization, User Management
- JWT token management with refresh tokens
- User profiles and preferences
- Role-based access control (RBAC)
- Session management
- Password management and validation
- **Consolidates**: auth-service + user-service

#### 2. **Asset Service** (Port 3002)
**Domain**: Infrastructure and Credential Management
- Target system inventory
- Encrypted credential storage
- Asset discovery and scanning
- Connection testing
- Asset relationship management
- **Consolidates**: credentials-service + targets-service + discovery-service

#### 3. **Automation Service** (Port 3003)
**Domain**: Job Management and Execution
- Visual workflow designer
- Job scheduling and execution (Celery)
- Step libraries and templates
- Execution history and monitoring
- Background worker processing
- **Consolidates**: jobs-service + executor-service + step-libraries-service

#### 4. **Communication Service** (Port 3004)
**Domain**: Notifications and External Integrations
- Email and webhook notifications
- Notification templates
- External API integrations
- Audit logging
- **Consolidates**: notification-service

### **Infrastructure Services**

#### 5. **API Gateway** (Port 3000)
- Request routing and load balancing
- Authentication middleware
- Rate limiting and throttling
- API versioning
- Request/response transformation

#### 6. **Event Bus** (Redis + Celery)
- Asynchronous event processing
- Service-to-service communication
- Message queuing with Redis
- Background task processing

## 🔄 Service Communication Patterns

### **Synchronous Communication**
- REST APIs for direct service calls (FastAPI)
- GraphQL for complex queries (future enhancement)
- gRPC for high-performance internal calls (future enhancement)

### **Asynchronous Communication**
- Event-driven architecture with Redis
- Background task processing with Celery
- Inter-service messaging via Redis pub/sub

## 📊 Data Architecture

### **Database Strategy**
- **PostgreSQL 16**: Primary database for all services
- **Redis 7**: Caching, sessions, and message queuing
- **Schema-per-service**: Logical separation implemented
  - `identity` schema - User and authentication data
  - `assets` schema - Targets, credentials, and discovery data
  - `automation` schema - Jobs, workflows, and execution data
  - `communication` schema - Notifications, templates, and audit logs

### **Data Consistency**
- Eventual consistency for cross-service operations
- Transaction management within service boundaries
- Audit trails and event logging

## 🛡️ Security Architecture

### **Authentication Flow**
1. Client → API Gateway → Identity Service
2. JWT tokens for service-to-service communication
3. Refresh token rotation implemented
4. Multi-factor authentication support (ready for implementation)

### **Authorization**
- RBAC with fine-grained permissions
- Resource-based access control
- Encrypted credential storage
- API key management for external integrations (ready)

## 🔧 Technology Stack

### **Core Technologies**
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 16 (Alpine)
- **Cache/Queue**: Redis 7 (Alpine)
- **Container**: Docker + Docker Compose
- **Task Queue**: Celery 5.3.4 with Redis backend

### **Observability**
- **Logging**: Structured JSON logging with structlog
- **Health Checks**: Built-in health endpoints for all services
- **Monitoring**: Celery Flower dashboard (Port 5555)
- **Metrics**: Prometheus-compatible metrics (ready)
- **Tracing**: OpenTelemetry ready

### **Development**
- **Documentation**: OpenAPI/Swagger auto-generated
- **Hot Reloading**: Development environment ready
- **Testing**: pytest with async support (ready)
- **Code Quality**: Black, isort, mypy (ready)
- **CI/CD**: GitHub Actions ready

### **Frontend**
- **Framework**: React 18.2.0 with TypeScript 4.9.5
- **UI Library**: Bootstrap 5.3.8 + Lucide React icons
- **HTTP Client**: Axios 1.6.2
- **Routing**: React Router DOM 6.20.1
- **Build System**: React Scripts 5.0.1

## 🚀 Deployment Strategy

### **Development**
- Docker Compose for local development
- Hot reloading for rapid development
- Integrated testing environment
- Volume mounts for live code updates

### **Production Ready**
- Kubernetes manifests (ready for implementation)
- Helm charts (ready for implementation)
- Health checks and readiness probes implemented
- Horizontal pod autoscaling (ready)

### **Current Deployment**
- **Nginx Reverse Proxy**: Ports 80, 443, 3100
- **SSL/TLS**: Self-signed certificates configured
- **Service Discovery**: Docker Compose networking
- **Persistent Storage**: PostgreSQL and Redis data volumes

## 📈 Scalability Considerations

### **Horizontal Scaling**
- Stateless service design
- Load balancer ready (Nginx)
- Database connection pooling (asyncpg)
- Caching strategies (Redis)

### **Performance Optimization**
- Async/await throughout all services
- Connection pooling (2-10 connections per service)
- Query optimization with prepared statements
- Response caching with Redis

### **Background Processing**
- **Celery Workers**: 4 concurrent workers
- **Celery Beat**: Scheduled task processing
- **Flower Monitoring**: Real-time task monitoring
- **Redis Backend**: Reliable message queuing

## 🎯 Benefits of Architecture

### **Reduced Complexity**
- 9 services → 4 core services + 1 gateway (44% reduction)
- Clear domain boundaries implemented
- Simplified deployment with single docker-compose.yml

### **Better Performance**
- Fewer network hops (API Gateway pattern)
- Optimized data access patterns (schema-per-service)
- Reduced latency with connection pooling

### **Improved Maintainability**
- Domain-focused development (4 clear domains)
- Clear service ownership and responsibilities
- Reduced integration complexity (shared base service)

### **Enhanced Scalability**
- Independent scaling per domain
- Better resource utilization (stateless services)
- Simplified monitoring (health checks + Flower)

## 🏁 Deployment URLs

| Service | URL | 
|---------|-----|
| **Main Application** | https://localhost:443 |
| **API Gateway** | http://localhost:3000 |
| **Identity Service** | http://localhost:3001 |
| **Asset Service** | http://localhost:3002 |
| **Automation Service** | http://localhost:3003 |
| **Communication Service** | http://localhost:3004 |
| **Celery Flower** | http://localhost:5555 |

This architecture provides a solid foundation for growth while maintaining operational simplicity and developer productivity. The system is designed for long-term scalability and maintainability.