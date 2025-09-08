# OpsConductor - Enterprise Automation Platform

A comprehensive microservices-based automation platform for managing Windows and Linux environments, providing job scheduling, execution, and monitoring capabilities with enterprise-grade security and scalability.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/andrewcho-dev/opsconductor-ms.git
   cd opsconductor-ms
   ```

2. **Start the system**
   ```bash
   ./start-python-system.sh
   ```

3. **Access the application**
   - Web UI: https://localhost:8443
   - Default credentials: admin / admin123

### System Status
Check system health:
```bash
./system-status.sh
```

## 🎯 Key Features

### ✅ Production-Ready Capabilities
- **Multi-Protocol Support**: WinRM (Windows) and SSH (Linux/Unix)
- **Visual Job Builder**: Drag-and-drop interface for job creation
- **Automated Scheduling**: Cron-based scheduling with timezone support
- **Real-time Monitoring**: Live job execution tracking and status updates
- **Multi-Channel Notifications**: Email, Slack, Teams, webhook notifications
- **Target Groups**: Logical target organization with bulk operations
- **Network Discovery**: Automated network scanning with nmap integration
- **Connection Testing**: Real-time WinRM and SSH connectivity validation
- **File Operations**: SFTP upload/download with transfer tracking
- **Step Libraries**: Modular automation components

### 🔧 Technical Stack
- **Backend**: Python FastAPI microservices
- **Frontend**: React 18 + TypeScript
- **Database**: PostgreSQL 16 with optimized schemas
- **Security**: AES-GCM encryption, JWT authentication
- **Deployment**: Docker Compose with health checks
- **Networking**: NGINX reverse proxy with SSL/TLS

## 🏗️ System Architecture

### Microservices (10 Services)
- **auth-service** (3001) - JWT authentication and authorization
- **user-service** (3002) - User management and profiles
- **credentials-service** (3004) - Secure credential storage
- **targets-service** (3005) - Windows/Linux target management
- **jobs-service** (3006) - Job definition and management
- **executor-service** (3007) - Job execution via WinRM/SSH
- **scheduler-service** (3008) - Job scheduling system
- **notification-service** (3009) - Multi-channel notifications
- **discovery-service** (3010) - Target discovery service
- **step-libraries-service** (3011) - Reusable automation steps
- **frontend** (3000) - React TypeScript UI
- **nginx** (8080/8443) - Reverse proxy and SSL termination

### Database
- **PostgreSQL** (5432) - Unified data storage with optimized schemas

## 📱 Web Interface

### Main Features
- **Dashboard**: System overview and metrics
- **Users**: User management with role-based access control
- **Credentials**: Secure credential storage with encryption
- **Targets**: Windows/Linux server management with groups
- **Discovery**: Automated network scanning and target import
- **Jobs**: Visual job creation and management
- **Schedules**: Cron-based job scheduling
- **Job Runs**: Execution history and real-time monitoring
- **Notifications**: Multi-channel notification configuration
- **Settings**: SMTP email and system configuration

## 🔒 Security

- **JWT-based authentication** with refresh token rotation
- **Role-based access control** (admin, operator, viewer)
- **AES-GCM encryption** for sensitive credential data
- **HTTPS/SSL encryption** for all communications
- **Input validation** and SQL injection prevention
- **Audit logging** for security events

## 🧪 Testing

### System Tests
```bash
# Test all services
./test-sprint1.sh

# Test specific components
./test-python-rebuild.sh
./test-user-management.sh
```

### E2E Testing
```bash
cd tests
npm install
npx playwright test
```

## 🔧 Configuration

### Environment Variables
Key variables in `.env`:
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

### SMTP Email Setup
1. Navigate to Settings in the web UI
2. Configure your SMTP server settings
3. Test the configuration with a test email
4. Supported providers: Gmail, Outlook, custom SMTP

## 🐳 Docker Management

### Service Management
```bash
# View logs
docker-compose logs -f [service-name]

# Restart service
docker-compose restart [service-name]

# Build services
docker-compose build

# Scale service
docker-compose up -d --scale user-service=2
```

### System Updates
```bash
git pull origin main
docker-compose pull
docker-compose up -d
```

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

## 🎯 Current Status

### Phase 11 Complete - Target Groups & UI Improvements
- ✅ **10 Microservices**: All operational with health monitoring
- ✅ **Multi-Platform Support**: Windows and Linux automation
- ✅ **Enterprise Security**: AES-GCM encryption, JWT authentication
- ✅ **Production Deployment**: HTTPS, SSL, containerized services
- ✅ **Network Discovery**: Automated target discovery and onboarding
- ✅ **Target Groups**: Logical target organization with group-based operations
- ✅ **UI Consolidation**: Eliminated redundant components, improved UX

### Next Phases Planned
- **Phase 12**: File Operations Library (25+ file management operations)
- **Phase 13**: Flow Control & Logical Operations (visual workflow designer)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the development standards
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review system status and logs

---

**OpsConductor** - Enterprise automation platform for modern infrastructure management.