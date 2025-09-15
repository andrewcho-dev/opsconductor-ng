# OpsConductor - Production-Ready IT Operations Platform

## 🚀 Quick Start (Fresh Installation Ready)

### Prerequisites
- Docker and Docker Compose
- Git

### One-Command Installation

1. **Clone and verify:**
   ```bash
   git clone <repository-url>
   cd opsconductor-ng
   ./verify-setup.sh  # Optional: Verify all components
   ```

2. **Build and deploy:**
   ```bash
   ./build.sh   # Builds all services and dependencies
   ./deploy.sh  # Deploys with database initialization
   ```

3. **Access the system:**
   - **Frontend:** http://localhost:3100
   - **API Gateway:** http://localhost:3000
   - **API Documentation:** http://localhost:3000/docs
   - **Celery Monitor:** http://localhost:5555

### Default Credentials
- **Username:** admin
- **Password:** admin123

## ✨ Latest Features & Improvements

### 🗄️ Complete Database Schema
- **4 Service Schemas:** Identity, Assets, Automation, Communication
- **20+ Tables:** All tables, indexes, triggers, and functions included
- **Automated Setup:** Single `complete-schema.sql` with all components
- **Data Integrity:** Comprehensive constraints and validation
- **Initial Data:** Default admin user, roles, and service definitions

### 🎯 Enhanced Target Management
- **Embedded Credentials:** No separate credential management needed
- **31+ Service Types:** SSH, RDP, HTTP, databases, email, and more
- **Hierarchical Groups:** 3-level target organization with drag-and-drop
- **Service Definitions:** Predefined configurations for common services
- **Legacy Support:** Backward compatibility with existing systems

### 🔐 Enterprise Security
- **Complete RBAC:** 5 roles (admin, manager, operator, developer, viewer)
- **Granular Permissions:** Resource-level access control
- **JWT Authentication:** Access and refresh tokens with session management
- **Credential Encryption:** Fernet encryption for sensitive data
- **Audit Logging:** Comprehensive system audit trail

### 🚀 Production Deployment
- **Health Checks:** All services with database connectivity verification
- **Automated Scripts:** Build, deploy, and verification automation
- **Environment Config:** Complete `.env.example` with all options
- **Docker Optimization:** Multi-stage builds and health monitoring
- **Fresh Install Ready:** Works immediately from git clone

## 🏗️ Architecture Overview

### Services
- **API Gateway** (Port 3000) - Central routing and authentication
- **Identity Service** (Port 3001) - User management and authentication
- **Asset Service** (Port 3002) - Target systems and credentials
- **Automation Service** (Port 3003) - Jobs, workflows, and execution
- **Communication Service** (Port 3004) - Notifications and audit logs
- **Frontend** (Port 3100) - React-based user interface

### Infrastructure
- **PostgreSQL** (Port 5432) - Primary database
- **Redis** (Port 6379) - Caching and session storage
- **Flower** (Port 5555) - Celery monitoring

## 📊 Complete Database Schema

The system uses a comprehensive PostgreSQL schema with **4 service schemas** and **20+ tables**:

### 🔐 Identity Schema (User Management)
- **`users`** - User accounts with profiles and security settings
- **`roles`** - 5 predefined roles with granular permissions
- **`user_roles`** - User-role assignments with audit trail
- **`user_sessions`** - JWT session management and tracking
- **`user_preferences`** - User-specific settings and preferences

### 🎯 Assets Schema (Target & Credential Management)
- **`enhanced_targets`** - Modern target architecture with embedded credentials
- **`target_services`** - 31+ predefined service types (SSH, RDP, HTTP, databases)
- **`target_groups`** - 3-level hierarchical organization with materialized paths
- **`target_group_memberships`** - Many-to-many target-group relationships
- **`service_definitions`** - Service metadata and default configurations
- **Legacy tables:** `targets`, `target_credentials` (backward compatibility)

### ⚙️ Automation Schema (Job & Workflow Management)
- **`jobs`** - Job definitions with workflow specifications
- **`job_executions`** - Execution tracking with status and results
- **`step_executions`** - Detailed step-by-step execution tracking
- **`job_schedules`** - Cron-based scheduling configuration

### 📢 Communication Schema (Notifications & Audit)
- **`notification_templates`** - Customizable message templates
- **`notification_channels`** - Email, webhook, and Slack integrations
- **`notifications`** - Notification queue with retry logic
- **`audit_logs`** - Comprehensive system audit trail

### 🔧 Database Features
- **Triggers & Functions:** Automatic path management for hierarchical groups
- **Constraints:** Data integrity and circular reference prevention
- **Indexes:** Optimized for performance with 15+ strategic indexes
- **Initial Data:** Default admin user, roles, and 31+ service definitions
- **Automated Setup:** Single SQL file with complete schema and data

## 🔧 Development

### Service Structure
Each service follows a consistent structure:
```
service-name/
├── main.py              # Service entry point
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── shared/             # Shared utilities
    ├── base_service.py # Base service class
    ├── database.py     # Database utilities
    ├── auth.py         # Authentication utilities
    └── models.py       # Shared data models
```

### Database Management

#### Automated Database Setup
```bash
# Complete initialization (recommended)
./database/init-db.sh

# Verify database integrity
./verify-setup.sh
```

#### Manual Database Operations
```bash
# Reset database completely
docker compose down -v
docker compose up -d postgres
./database/init-db.sh

# Apply schema updates
docker exec -i opsconductor-postgres psql -U postgres -d opsconductor < database/complete-schema.sql

# Check database status
docker exec opsconductor-postgres psql -U postgres -d opsconductor -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog');"
```

#### Database Features
- **Complete Schema:** All 20+ tables with relationships and constraints
- **Automated Initialization:** Detects missing components and adds them
- **Data Integrity:** Triggers prevent circular references and maintain paths
- **Performance Optimized:** Strategic indexes for common queries
- **Audit Ready:** All operations logged with user tracking

### Service Development

#### Start Individual Service
```bash
docker compose up service-name
```

#### View Service Logs
```bash
docker compose logs -f service-name
```

#### Restart Service
```bash
docker compose restart service-name
```

### Frontend Development

The frontend is a modern React TypeScript application with:
- **React 18** with hooks and context API
- **Material-UI** with custom theming and responsive design
- **TypeScript** for type safety and better development experience
- **Axios** for API communication with interceptors
- **React Router** for client-side navigation
- **React Hook Form** for efficient form management
- **React Beautiful DnD** for drag-and-drop functionality

#### Development Mode
```bash
cd frontend
npm install
npm start  # Development server on port 3000
```

#### Frontend Features
- **Enhanced Target Management:** Drag-and-drop target groups
- **Real-time Updates:** WebSocket integration for live job monitoring
- **Responsive Design:** Mobile-friendly interface
- **Form Validation:** Client-side and server-side validation
- **Error Handling:** Comprehensive error boundaries and user feedback
- **Authentication:** JWT token management with automatic refresh

## 🔒 Security Features

### Authentication
- JWT-based authentication
- Refresh token rotation
- Session management
- Password hashing with bcrypt

### Authorization
- Role-based access control (RBAC)
- Granular permissions
- Resource-level access control

### Data Protection
- Encrypted credential storage
- Secure API communication
- Input validation and sanitization

## 📈 Monitoring and Logging

### Health Checks
- Service health endpoints: `/health`
- Database connectivity checks
- Redis connectivity checks

### Logging
- Structured logging with structlog
- Centralized log aggregation
- Request/response logging

### Monitoring
- Celery task monitoring with Flower
- Service metrics and status
- Database performance monitoring

## 🚀 Deployment & Scripts

### Automated Deployment Scripts

#### `verify-setup.sh` - Pre-deployment Verification
```bash
./verify-setup.sh
```
- Verifies all required files and directories
- Checks service structure and dependencies
- Validates Docker Compose configuration
- Ensures executable permissions
- Reports missing components

#### `build.sh` - Complete System Build
```bash
./build.sh
```
- Sets up directory structure for all services
- Copies shared modules to each service
- Creates Dockerfiles and requirements.txt if missing
- Prepares frontend with React and TypeScript
- Makes all scripts executable

#### `deploy.sh` - Production Deployment
```bash
./deploy.sh
```
- Stops existing containers
- Builds and starts all services
- Initializes database with complete schema
- Waits for services to be healthy
- Performs health checks on all components
- Reports service status and URLs

### Production Deployment
1. **Environment Setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your production values
   ```

2. **SSL/TLS Configuration:**
   - Update `nginx/nginx.conf` with your certificates
   - Configure domain names and SSL settings

3. **Database Security:**
   - Change default PostgreSQL password
   - Configure database backups
   - Set up monitoring and alerting

4. **Service Configuration:**
   - Update JWT secret keys
   - Configure SMTP settings for notifications
   - Set up external integrations

### Environment Variables
Key environment variables to configure in `.env`:
- `POSTGRES_PASSWORD` - Database password (change from default)
- `JWT_SECRET_KEY` - JWT signing key (generate secure key)
- `ENCRYPTION_KEY` - Credential encryption key (32 bytes)
- `REDIS_URL` - Redis connection string
- `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD` - Email configuration
- `CORS_ORIGINS` - Allowed frontend origins
- `DEBUG` - Enable/disable debug mode

## 🔄 Migration from Legacy System

The new architecture maintains backward compatibility:
- Legacy API endpoints are supported
- Existing data can be migrated
- Gradual migration path available

### Migration Steps
1. Export data from legacy system
2. Run migration scripts
3. Verify data integrity
4. Update client applications
5. Decommission legacy services

## 🛠️ Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Reinitialize database
./database/init-db.sh
```

#### Service Startup Issues
```bash
# Check service logs
docker compose logs service-name

# Rebuild service
docker compose up --build service-name
```

#### Frontend Issues
```bash
# Check frontend logs
docker compose logs frontend

# Rebuild frontend
cd frontend && npm run build
```

### Debug Mode
Enable debug logging by setting environment variables:
```bash
export LOG_LEVEL=DEBUG
docker compose up
```

## 📚 API Documentation

### Interactive Documentation
- Swagger UI: http://localhost:3000/docs
- ReDoc: http://localhost:3000/redoc

### Key Endpoints

#### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - User logout

#### Targets
- `GET /targets` - List targets
- `POST /targets` - Create target
- `PUT /targets/{id}` - Update target
- `DELETE /targets/{id}` - Delete target

#### Jobs
- `GET /jobs` - List jobs
- `POST /jobs` - Create job
- `POST /jobs/{id}/execute` - Execute job
- `GET /executions` - List executions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React code
- Add docstrings to all functions
- Include type hints where appropriate

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Check service logs for error details