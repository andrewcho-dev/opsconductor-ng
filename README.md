# OpsConductor Microservice System

**WORKING SYSTEM** - User management, authentication, credential storage, and target management with web interface.

> **📋 See [CURRENT_STATUS.md](./CURRENT_STATUS.md) for accurate system status and capabilities**

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│     Browser     │────│      Nginx      │ (HTTPS/SSL)
└─────────────────┘    │  Reverse Proxy  │
                       └─────────────────┘
                              │ (HTTP)
                    ┌─────────┼─────────┐
                    │         │         │
            ┌───────▼───┐ ┌───▼───┐ ┌───▼───┐
            │ Frontend  │ │ Auth  │ │ User  │
            │ Service   │ │Service│ │Service│
            │  :3000    │ │ :3002 │ │ :3001 │
            └───────────┘ └───┬───┘ └───┬───┘
                              │         │
                        ┌─────▼───┐ ┌───▼─────┐
                        │ Auth DB │ │ User DB │
                        │(Postgres│ │(Postgres│
                        └─────────┘ └─────────┘
```

## Services

### 1. User Service (Port 3001)
- Manages user information (username, firstname, lastname, password)
- PostgreSQL database for user data
- RESTful API for user operations

### 2. Authentication Service (Port 3002)
- Handles login/logout operations
- JWT token management
- Session tracking in PostgreSQL database
- Communicates with User Service for credential verification

### 3. Frontend Service (Port 3000)
- Serves HTML/CSS/JavaScript
- Login and main dashboard pages
- Proxy for API calls to backend services

### 4. Nginx Reverse Proxy (Ports 80/443)
- SSL termination with self-signed certificate
- HTTP to HTTPS redirect
- Load balancing and routing
- Security headers

## Features

- **Complete isolation**: Each service has its own database
- **Docker containerization**: All services run in separate containers
- **SSL/HTTPS**: Self-signed certificate for secure communication
- **Service discovery**: Docker DNS for inter-service communication
- **Responsive UI**: Modern login and dashboard interface
- **JWT authentication**: Secure token-based authentication
- **Health checks**: Service monitoring endpoints

## Quick Start

1. **Start the system:**
   ```bash
   ./start.sh
   ```

2. **Access the application:**
   - Open https://localhost in your browser
   - Accept the self-signed certificate warning

3. **Register a new user:**
   - Click "Register here" on the login page
   - Fill in username, first name, last name, and password
   - Click "Register"

4. **Login:**
   - Use your registered credentials to login
   - You'll be redirected to the main dashboard

## Manual Commands

### Start services:
```bash
docker-compose up --build -d
```

### View logs:
```bash
docker-compose logs -f [service-name]
```

### Stop services:
```bash
docker-compose down
```

### Remove all data:
```bash
docker-compose down -v
```

## API Endpoints

### User Service (Internal: http://user-service:3001)
- `POST /users` - Create user
- `GET /users/:username` - Get user by username
- `GET /users/id/:id` - Get user by ID
- `PUT /users/:id` - Update user

### Auth Service (Internal: http://auth-service:3002)
- `POST /login` - User login
- `POST /verify` - Verify JWT token
- `POST /logout` - User logout

### Frontend Service (Internal: http://frontend:3000)
- `GET /` - Login page
- `GET /main` - Dashboard page
- `POST /api/login` - Login proxy
- `POST /api/register` - Register proxy
- `POST /api/verify` - Token verification proxy

### External Access (via Nginx HTTPS)
- `https://localhost/` - Main application
- `https://localhost/auth/` - Direct auth service access
- `https://localhost/users/` - Direct user service access

## Database Schema

### User Database (userdb)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    firstname VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Auth Database (authdb)
```sql
CREATE TABLE auth_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
```

## Security Features

- Password hashing with bcrypt
- JWT tokens with expiration
- HTTPS with SSL/TLS
- Security headers (HSTS, XSS protection, etc.)
- CORS configuration
- Input validation

## Development

Each service can be developed independently:

1. **User Service**: Node.js + Express + PostgreSQL
2. **Auth Service**: Node.js + Express + PostgreSQL + JWT
3. **Frontend**: Node.js + Express + Vanilla JavaScript
4. **Nginx**: Reverse proxy with SSL termination

## Troubleshooting

### Services not starting:
```bash
docker-compose logs [service-name]
```

### Database connection issues:
```bash
docker-compose restart [db-service-name]
```

### SSL certificate warnings:
- This is expected with self-signed certificates
- Click "Advanced" → "Proceed to localhost (unsafe)" in your browser

### Port conflicts:
- Make sure ports 80 and 443 are not in use by other applications
- Stop other web servers before starting this system

## Production Considerations

For production deployment:
1. Use proper SSL certificates (Let's Encrypt, etc.)
2. Use environment variables for secrets
3. Implement proper logging and monitoring
4. Add rate limiting and security middleware
5. Use production-grade databases with backups
6. Implement proper error handling and recovery
7. Add health checks and service discovery
8. Use container orchestration (Kubernetes, Docker Swarm)