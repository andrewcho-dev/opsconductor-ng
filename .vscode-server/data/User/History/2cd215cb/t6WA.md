# OpsConductor NG (Next Generation)

A modern, microservices-based IT operations automation platform built with Python FastAPI, React TypeScript, and PostgreSQL.

## 🚀 Quick Start

1. **Clone and start the platform**:
   ```bash
   git clone https://github.com/andrewcho-dev/opsconductor-ng.git
   cd opsconductor-ng
   chmod +x build.sh
   ./build.sh
   ```

2. **Access the application**:
   - Web Interface: `https://your-server-ip`
   - Default credentials: `admin` / `admin123`

## 🏗️ Architecture

### Core Services
- **API Gateway** (`api-gateway/`) - Central routing and authentication (Port 3000)
- **Identity Service** (`identity-service/`) - User authentication and RBAC (Port 3001)
- **Asset Service** (`asset-service/`) - IT asset and credential management (Port 3002)
- **Automation Service** (`automation-service/`) - Job execution and workflows (Port 3003)
- **Communication Service** (`communication-service/`) - Notifications and messaging (Port 3004)

### Frontend & Infrastructure
- **React Application** (`frontend/`) - Modern TypeScript web interface
- **Database** (`database/`) - PostgreSQL schemas with service separation
- **Nginx** (`nginx/`) - Reverse proxy with SSL/TLS
- **Shared** (`shared/`) - Common utilities and base service classes

## 📁 Project Structure

```
opsconductor-ng/
├── api-gateway/          # Central API routing service
├── identity-service/     # Authentication & user management
├── asset-service/        # IT asset & credential management
├── automation-service/   # Job execution & workflows
├── communication-service/# Notifications & messaging
├── frontend/            # React TypeScript application
├── database/            # PostgreSQL schemas & migrations
├── nginx/               # Reverse proxy configuration
├── shared/              # Shared utilities and base classes
├── ssl/                 # TLS certificates
├── docker-compose.yml   # Container orchestration
├── build.sh            # Build and deployment script
└── README.md           # This file
```

## 🔧 Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL 16 with schema-per-service
- **Cache/Queue**: Redis 7 for caching and messaging
- **Task Queue**: Celery with Redis backend
- **Container**: Docker + Docker Compose

### Frontend
- **Framework**: React 18.2.0 with TypeScript 4.9.5
- **UI Library**: Bootstrap 5.3.8 + Lucide React icons
- **HTTP Client**: Axios 1.6.2
- **Routing**: React Router DOM 6.20.1
- **Build System**: React Scripts 5.0.1

### Infrastructure
- **Reverse Proxy**: Nginx with SSL/TLS
- **Monitoring**: Celery Flower dashboard (Port 5555)
- **Logging**: Structured JSON logging with structlog
- **Health Checks**: Built-in health endpoints for all services

## 🛡️ Security & RBAC

### Authentication
- JWT token-based authentication with refresh tokens
- Secure password hashing and validation
- Session management and token rotation

### Role-Based Access Control (RBAC)
- **Admin** - Full system access with wildcard permission (`*`)
- **Operator** - Can execute jobs and view most resources
- **Viewer** - Read-only access to basic resources

### Permission Categories
- **User Management**: `users:read`, `users:create`, `users:update`, `users:delete`
- **Role Management**: `roles:read`, `roles:create`, `roles:update`, `roles:delete`
- **Job Management**: `jobs:read`, `jobs:create`, `jobs:update`, `jobs:delete`, `jobs:execute`
- **Target Management**: `targets:read`, `targets:create`, `targets:update`, `targets:delete`
- **System Administration**: `system:admin`, `settings:read`, `settings:update`

### Implementation
- **Frontend**: Permission-based UI rendering with `hasPermission()` checks
- **Backend**: API endpoint protection with `@require_permission()` decorators
- **API Gateway**: User context propagation via HTTP headers

## 🗄️ Database Architecture

### Schema-per-Service Design
- `identity` schema - User authentication and role data
- `assets` schema - Targets, credentials, and discovery data
- `automation` schema - Jobs, workflows, and execution data
- `communication` schema - Notifications, templates, and audit logs

### Benefits
- Clear data ownership boundaries
- Independent schema evolution
- Better security isolation
- Easier backup and recovery strategies

## 🔄 Service Communication

### Synchronous Communication
- REST APIs for direct service calls (FastAPI)
- API Gateway pattern for centralized routing
- JWT tokens for service-to-service authentication

### Asynchronous Communication
- Event-driven architecture with Redis
- Background task processing with Celery
- Inter-service messaging via Redis pub/sub

## 🚀 Development

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Running in Development Mode
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Restart a specific service
docker compose restart frontend

# Start specific service for development
docker compose up postgres redis identity-service
```

### Building for Production
```bash
./build.sh
```

### Testing API Endpoints
```bash
# Health check
curl http://localhost:3000/health

# Login
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## 🎯 Key Features

- ✅ **Modern UI/UX**: Responsive React interface with TypeScript
- ✅ **Microservices**: Scalable, domain-driven service architecture
- ✅ **RBAC Security**: Fine-grained role-based access control
- ✅ **Asset Management**: Comprehensive IT asset and credential tracking
- ✅ **Job Automation**: Visual workflow builder and execution engine
- ✅ **Real-time Updates**: WebSocket-based live updates
- ✅ **API Documentation**: Auto-generated OpenAPI/Swagger docs
- ✅ **Container Ready**: Full Docker containerization
- ✅ **Production Ready**: Nginx, SSL, and security hardening

## 📊 Architecture Benefits

### Reduced Complexity
- **Before**: 9 services with complex interdependencies
- **After**: 4 core services + 1 gateway (44% reduction)
- Clear domain boundaries and responsibilities

### Better Performance
- Fewer network hops with API Gateway pattern
- Optimized data access with schema-per-service
- Async/await throughout all services
- Connection pooling and caching strategies

### Improved Maintainability
- Domain-focused development (4 clear domains)
- Clear service ownership and responsibilities
- Reduced integration complexity
- Independent service scaling and deployment

## 🔍 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Main Application** | https://localhost:443 | Web Interface |
| **API Gateway** | http://localhost:3000 | Main API entry point |
| **Identity Service** | http://localhost:3001 | Auth & Users |
| **Asset Service** | http://localhost:3002 | Targets & Credentials |
| **Automation Service** | http://localhost:3003 | Jobs & Workflows |
| **Communication Service** | http://localhost:3004 | Notifications |
| **Celery Flower** | http://localhost:5555 | Task Monitoring |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For support and questions:
- Create an issue in this repository
- Contact the development team

---

**OpsConductor NG** - Next Generation IT Operations Automation Platform