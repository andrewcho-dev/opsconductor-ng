# OpsConductor - New Optimized Architecture

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd opsconductor-ng
   ```

2. **Build the system:**
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

3. **Deploy the system:**
   ```bash
   ./deploy.sh
   ```

4. **Access the system:**
   - Frontend: http://localhost:3100
   - API Gateway: http://localhost:3000
   - API Documentation: http://localhost:3000/docs

### Default Credentials
- **Username:** admin
- **Password:** admin123

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

## 📊 Database Schema

The system uses a comprehensive PostgreSQL schema with the following components:

### Identity Schema
- `users` - User accounts and profiles
- `roles` - Role-based access control
- `user_roles` - User-role assignments
- `user_sessions` - Session management
- `user_preferences` - User settings

### Assets Schema
- `enhanced_targets` - Target systems (new architecture)
- `target_services` - Services and embedded credentials
- `target_groups` - Hierarchical target organization
- `target_group_memberships` - Target-group relationships
- `service_definitions` - Service metadata for UI
- `targets` - Legacy target systems (backward compatibility)
- `target_credentials` - Legacy credentials (backward compatibility)

### Automation Schema
- `jobs` - Job definitions and workflows
- `job_executions` - Execution tracking
- `step_executions` - Detailed step tracking
- `job_schedules` - Scheduling configuration

### Communication Schema
- `notification_templates` - Message templates
- `notification_channels` - Delivery channels
- `notifications` - Notification queue
- `audit_logs` - System audit trail

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

#### Initialize Database
```bash
./database/init-db.sh
```

#### Reset Database
```bash
docker compose down -v
docker compose up -d postgres
./database/init-db.sh
```

#### Manual Schema Updates
```bash
docker exec -i opsconductor-postgres psql -U postgres -d opsconductor < database/complete-schema.sql
```

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

The frontend is a React application with:
- Modern React 18 with hooks
- Material-UI components
- Axios for API communication
- React Router for navigation
- Context API for state management

#### Development Mode
```bash
cd frontend
npm install
npm start
```

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

## 🚀 Deployment

### Production Deployment
1. Update environment variables in `docker-compose.yml`
2. Configure SSL certificates
3. Set up reverse proxy (nginx recommended)
4. Configure backup strategies
5. Set up monitoring and alerting

### Environment Variables
Key environment variables to configure:
- `POSTGRES_PASSWORD` - Database password
- `JWT_SECRET_KEY` - JWT signing key
- `ENCRYPTION_KEY` - Credential encryption key
- `REDIS_URL` - Redis connection string

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