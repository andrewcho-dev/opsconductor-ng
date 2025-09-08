# OpsConductor - Windows Management System

A comprehensive microservices-based system for managing Windows environments, job scheduling, and automation tasks.

## 🚀 Features

- **Microservices Architecture**: 8 independent services with clear separation of concerns
- **Windows Management**: Remote Windows server management via WinRM
- **Job Scheduling**: Advanced job scheduling and execution system
- **User Management**: Complete user authentication and authorization
- **Credential Management**: Secure storage and management of credentials
- **Email Notifications**: SMTP-based notification system with web UI configuration
- **Modern Frontend**: React TypeScript UI with responsive design
- **Containerized**: Full Docker containerization with docker-compose

## 🏗️ Architecture

### Services

1. **auth-service** (Port 3001) - JWT authentication and authorization
2. **user-service** (Port 3002) - User management and profiles
3. **credentials-service** (Port 3004) - Secure credential storage
4. **targets-service** (Port 3005) - Windows target management
5. **jobs-service** (Port 3006) - Job definition and management
6. **executor-service** (Port 3007) - Job execution via WinRM
7. **scheduler-service** (Port 3008) - Job scheduling system
8. **notification-service** (Port 3009) - Email notifications
9. **frontend** (Port 3000) - React TypeScript UI
10. **nginx** (Ports 8080/8443) - Reverse proxy and SSL termination

### Database
- **PostgreSQL** (Port 5432) - Primary database for all services

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/andrewcho-dev/opsconductor-ms.git
   cd opsconductor-ms
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start the system**
   ```bash
   # Start all services
   ./start-python-system.sh
   
   # Or manually with docker-compose
   docker-compose -f docker-compose-python.yml up -d
   ```

4. **Access the application**
   - Web UI: https://localhost:8443
   - Default credentials: admin / admin123

### System Status
Check system health:
```bash
./system-status.sh
```

## 📱 Web Interface

### Login
- Navigate to https://localhost:8443
- Use default credentials: `admin` / `admin123`

### Main Features
- **Dashboard**: System overview and metrics
- **Users**: User management
- **Credentials**: Secure credential storage
- **Targets**: Windows server management
- **Jobs**: Job creation and management
- **Schedules**: Job scheduling
- **Job Runs**: Execution history and monitoring
- **Notifications**: System notifications
- **Settings**: SMTP email configuration

## 🔧 Configuration

### SMTP Email Setup
1. Navigate to Settings in the web UI
2. Configure your SMTP server settings
3. Test the configuration with a test email
4. Supported providers: Gmail, Outlook, custom SMTP

### Environment Variables
Key environment variables in `.env`:
```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=opsconductor
DB_USER=postgres
DB_PASSWORD=postgres123

# JWT
JWT_SECRET=your-secret-key

# Services
AUTH_SERVICE_URL=http://auth-service:3001
USER_SERVICE_URL=http://user-service:3002
# ... other service URLs
```

## 🧪 Testing

### Run System Tests
```bash
# Test all services
./test-sprint1.sh

# Test specific components
./test-python-rebuild.sh
./test-user-management.sh
```

### API Testing
All services expose REST APIs. Example:
```bash
# Get auth token
curl -X POST https://localhost:8443/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token for authenticated requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://localhost:8443/users
```

## 📚 Documentation

- [Developer Guide](DEVELOPER_GUIDE.md) - **Essential reading for developers**
- [System Overview](SYSTEM_OVERVIEW.md)
- [Add New Service Guide](ADD_NEW_SERVICE_GUIDE.md)


## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- Secure credential storage
- HTTPS/SSL encryption
- Input validation and sanitization

## 🐳 Docker Services

### Build Services
```bash
# Build all services
docker-compose -f docker-compose-python.yml build

# Build specific service
docker-compose -f docker-compose-python.yml build auth-service
```

### Service Management
```bash
# View logs
docker-compose -f docker-compose-python.yml logs -f [service-name]

# Restart service
docker-compose -f docker-compose-python.yml restart [service-name]

# Scale service
docker-compose -f docker-compose-python.yml up -d --scale user-service=2
```

## 🔍 Monitoring

### Health Checks
- All services include health check endpoints
- System status monitoring via web UI
- Service dependency management

### Logs
```bash
# View all logs
docker-compose -f docker-compose-python.yml logs -f

# View specific service logs
docker-compose -f docker-compose-python.yml logs -f notification-service
```

## 🚀 Development

### Essential Developer Resources
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Complete development documentation
- **Utility Modules** - Always check for existing `utility_*.py` modules before writing new code
- **Error Handling** - Use custom error classes, not `HTTPException`

### Adding New Services
1. Follow the [Add New Service Guide](ADD_NEW_SERVICE_GUIDE.md)
2. Use the service template in `service-template/`
3. Update docker-compose configuration
4. Add routing in nginx configuration

### Utility Modules System
OpsConductor uses a comprehensive utility module system to avoid code duplication:

```python
# Always check for existing utilities first
import utility_email_sender as email_utility
import utility_webhook_sender as webhook_utility
import utility_notification_processor as notification_utility

# Initialize utilities
email_utility.set_smtp_config(SMTP_CONFIG)
notification_utility.set_db_cursor_func(get_db_cursor)

# Use in your endpoints
success = await email_utility.send_email_notification(id, dest, payload)
```

**Key Utility Modules:**
- `utility_email_sender.py` - Email notifications
- `utility_webhook_sender.py` - Slack, Teams, webhook notifications  
- `utility_template_renderer.py` - Jinja2 template rendering
- `utility_user_preferences.py` - User preference management
- `utility_notification_processor.py` - Notification processing

See [Developer Guide](DEVELOPER_GUIDE.md) for complete documentation.

### Frontend Development
```bash
cd frontend
npm install
npm start  # Development server
npm run build  # Production build
```

### Backend Development
Each service is a Python FastAPI application:
```bash
cd [service-name]
pip install -r requirements.txt
python main.py  # Development server
```

### Error Handling Standards
All services use standardized error handling with custom exception classes:

#### Available Error Classes
```python
from shared.errors import (
    DatabaseError,        # Database operation failures (500)
    ValidationError,      # Input validation failures (400)
    NotFoundError,        # Resource not found (404)
    AuthError,           # Authentication failures (401)
    PermissionError,     # Authorization failures (403)
    ServiceCommunicationError  # Inter-service communication (503)
)
```

#### Usage Examples
```python
# Input validation
if not user_data.email:
    raise ValidationError("Email is required", "email")

# Resource not found
if not user:
    raise NotFoundError("User not found")

# Database operations
try:
    cursor.execute(query, params)
except Exception as e:
    raise DatabaseError(f"Failed to create user: {str(e)}")

# Service communication
try:
    response = requests.get(f"{AUTH_SERVICE_URL}/verify")
except requests.RequestException:
    raise ServiceCommunicationError("auth-service", "Auth service unavailable")
```

#### Migration from HTTPException
- **DO NOT** use `HTTPException` directly in new code
- All 129 existing `HTTPException` instances have been standardized
- Use the appropriate custom error class for better error handling and consistency

## 📋 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh token

### Users
- `GET /users` - List users
- `POST /users` - Create user
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

### Jobs
- `GET /jobs` - List jobs
- `POST /jobs` - Create job
- `POST /jobs/{id}/run` - Execute job
- `GET /runs` - List job runs

### Notifications
- `GET /api/notification/smtp/settings` - Get SMTP settings
- `POST /api/notification/smtp/settings` - Update SMTP settings
- `POST /api/notification/smtp/test` - Test SMTP configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the system status and logs

## 🔄 Updates

To update the system:
```bash
git pull origin main
docker-compose -f docker-compose-python.yml pull
docker-compose -f docker-compose-python.yml up -d
```

---

**OpsConductor** - Streamlining Windows management and automation tasks through modern microservices architecture.