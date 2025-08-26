# 🏗️ Microservice System Architecture Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Service Specifications](#service-specifications)
4. [Communication Patterns](#communication-patterns)
5. [Data Flow](#data-flow)
6. [Security Architecture](#security-architecture)
7. [Infrastructure Components](#infrastructure-components)
8. [API Documentation](#api-documentation)
9. [Database Schema](#database-schema)
10. [Deployment Architecture](#deployment-architecture)
11. [Service Template](#service-template)
12. [Adding New Services](#adding-new-services)

---

## 🎯 System Overview

### Architecture Type
**Microservices Architecture** with the following characteristics:
- **Service Independence**: Each service runs in its own container
- **Database Per Service**: Each service has its own dedicated database
- **API Gateway Pattern**: Nginx acts as reverse proxy and SSL termination
- **Frontend Proxy Pattern**: Frontend service acts as API aggregator
- **JWT Authentication**: Stateless authentication across services
- **Docker Containerization**: All services containerized for isolation

### Core Principles
1. **Single Responsibility**: Each service handles one business domain
2. **Decentralized Data**: No shared databases between services
3. **Fault Isolation**: Service failures don't cascade
4. **Independent Deployment**: Services can be deployed independently
5. **Technology Agnostic**: Services can use different technologies
6. **Stateless Communication**: Services communicate via HTTP/REST

---

## 🏛️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  Browser/Client (HTTPS)                                         │
│  └── https://localhost                                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GATEWAY LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 Nginx Reverse Proxy                     │    │
│  │  • SSL Termination (HTTPS → HTTP)                      │    │
│  │  • Load Balancing                                       │    │
│  │  • Request Routing                                      │    │
│  │  • Security Headers                                     │    │
│  │  Ports: 80 (HTTP), 443 (HTTPS)                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Frontend   │  │    Auth     │  │    User     │              │
│  │  Service    │  │  Service    │  │  Service    │              │
│  │             │  │             │  │             │              │
│  │ • UI Serve  │  │ • Login     │  │ • User CRUD │              │
│  │ • API Proxy │  │ • JWT Auth  │  │ • Profile   │              │
│  │ • Routing   │  │ • Token Val │  │ • Search    │              │
│  │             │  │             │  │             │              │
│  │ Port: 3000  │  │ Port: 3002  │  │ Port: 3001  │              │
│  │ Node.js     │  │ Node.js     │  │ Node.js     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
└─────────────────────────────────────────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│     (None)         ┌─────────────┐  ┌─────────────┐              │
│                    │   Auth DB   │  │   User DB   │              │
│                    │             │  │             │              │
│                    │ PostgreSQL  │  │ PostgreSQL  │              │
│                    │ Port: 5432  │  │ Port: 5432  │              │
│                    │             │  │             │              │
│                    │ • Sessions  │  │ • Users     │              │
│                    │ • Tokens    │  │ • Profiles  │              │
│                    └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Network Communication
```
Docker Network: microservice-system_default
├── nginx (Gateway)
├── frontend (Port 3000)
├── auth-service (Port 3002)
├── user-service (Port 3001)
├── auth-db (Port 5432)
└── user-db (Port 5432)
```

---

## 🔧 Service Specifications

### 1. Frontend Service
**Purpose**: UI serving and API aggregation
**Technology**: Node.js + Express
**Port**: 3000 (internal)
**Dependencies**: auth-service, user-service

**Responsibilities**:
- Serve static HTML/CSS/JS files
- Proxy API requests to backend services
- Handle client-side routing
- Aggregate responses from multiple services

**Key Files**:
```
frontend/
├── server.js           # Express server
├── package.json        # Dependencies
├── Dockerfile         # Container config
└── public/            # Static files
    ├── index.html     # Login page
    ├── main.html      # Dashboard
    └── users.html     # User management
```

### 2. Authentication Service
**Purpose**: User authentication and authorization
**Technology**: Node.js + Express + JWT
**Port**: 3002 (internal)
**Database**: auth-db (PostgreSQL)

**Responsibilities**:
- User login/logout
- JWT token generation and validation
- Session management
- Password verification

**Key Files**:
```
auth-service/
├── server.js          # Express server
├── package.json       # Dependencies
├── Dockerfile        # Container config
└── init.sql          # Database schema
```

### 3. User Service
**Purpose**: User data management
**Technology**: Node.js + Express
**Port**: 3001 (internal)
**Database**: user-db (PostgreSQL)

**Responsibilities**:
- User CRUD operations
- User profile management
- User search and pagination
- Data validation

**Key Files**:
```
user-service/
├── server.js          # Express server
├── package.json       # Dependencies
├── Dockerfile        # Container config
└── init.sql          # Database schema
```

### 4. Nginx Gateway
**Purpose**: Reverse proxy and SSL termination
**Technology**: Nginx
**Ports**: 80 (HTTP), 443 (HTTPS)

**Responsibilities**:
- SSL/TLS termination
- Request routing
- Load balancing
- Security headers
- Static file serving (if needed)

**Key Files**:
```
nginx/
├── nginx.conf         # Main configuration
├── Dockerfile        # Container config
└── ssl/              # SSL certificates
    ├── server.crt    # Self-signed certificate
    └── server.key    # Private key
```

---

## 🔄 Communication Patterns

### 1. Client-to-Gateway Communication
```
Protocol: HTTPS
Flow: Browser → Nginx (443) → Internal Services
Security: SSL/TLS encryption
```

### 2. Gateway-to-Service Communication
```
Protocol: HTTP (internal network)
Flow: Nginx → Frontend/Auth/User Services
Security: Docker network isolation
```

### 3. Service-to-Service Communication
```
Protocol: HTTP REST APIs
Authentication: JWT tokens
Pattern: Synchronous request/response
```

### 4. Service-to-Database Communication
```
Protocol: PostgreSQL wire protocol
Security: Internal Docker network
Pattern: Connection pooling
```

### Communication Matrix
| From → To | Protocol | Port | Authentication | Purpose |
|-----------|----------|------|----------------|---------|
| Browser → Nginx | HTTPS | 443 | None | External access |
| Nginx → Frontend | HTTP | 3000 | None | UI serving |
| Nginx → Auth | HTTP | 3002 | None | Direct API access |
| Nginx → User | HTTP | 3001 | None | Direct API access |
| Frontend → Auth | HTTP | 3002 | JWT | Authentication |
| Frontend → User | HTTP | 3001 | JWT | User operations |
| Auth → Auth-DB | PostgreSQL | 5432 | Credentials | Data persistence |
| User → User-DB | PostgreSQL | 5432 | Credentials | Data persistence |

---

## 📊 Data Flow

### 1. User Login Flow
```
1. Browser → Nginx → Frontend (GET /)
2. User submits login form
3. Browser → Nginx → Frontend → Auth Service (POST /login)
4. Auth Service validates credentials against Auth DB
5. Auth Service generates JWT token
6. Token returned to browser via Frontend
7. Browser stores token for subsequent requests
```

### 2. User Management Flow
```
1. Browser → Nginx → Frontend (GET /users)
2. Frontend serves user management UI
3. Browser requests user list with JWT token
4. Browser → Nginx → Frontend → User Service (GET /users)
5. User Service queries User DB
6. Data returned through chain: User Service → Frontend → Browser
7. Browser renders user list in UI
```

### 3. CRUD Operations Flow
```
CREATE: Browser → Frontend → User Service → User DB
READ:   Browser → Frontend → User Service → User DB
UPDATE: Browser → Frontend → User Service → User DB
DELETE: Browser → Frontend → User Service → User DB
```

### 4. Authentication Flow
```
1. Browser includes JWT token in Authorization header
2. Frontend validates token with Auth Service
3. Auth Service verifies token signature and expiration
4. If valid, request proceeds to target service
5. If invalid, 401 Unauthorized returned
```

---

## 🔐 Security Architecture

### 1. Network Security
- **Docker Network Isolation**: Services communicate on isolated network
- **No Direct Database Access**: Databases only accessible from their services
- **Internal HTTP**: Services use HTTP internally (encrypted at gateway)

### 2. Authentication & Authorization
- **JWT Tokens**: Stateless authentication
- **Token Expiration**: Configurable token lifetime
- **Bearer Token**: Standard Authorization header format
- **Password Hashing**: bcrypt for password storage

### 3. Input Validation
- **Server-side Validation**: All inputs validated at service level
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: HTML escaping in frontend
- **CSRF Protection**: Token-based authentication

### 4. SSL/TLS
- **HTTPS Only**: All external communication encrypted
- **Self-signed Certificate**: For development (replace in production)
- **HTTP Redirect**: Automatic redirect from HTTP to HTTPS

### Security Headers
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

---

## 🗄️ Database Schema

### Auth Database (auth-db)
```sql
-- Sessions/tokens table (if needed for session management)
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
```

### User Database (user-db)
```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    firstname VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 🚀 Deployment Architecture

### Docker Compose Structure
```yaml
version: '3.8'
services:
  # Databases
  user-db:
    image: postgres:15
    environment:
      POSTGRES_DB: userdb
      POSTGRES_USER: userservice
      POSTGRES_PASSWORD: userpass123
    volumes:
      - user_data:/var/lib/postgresql/data
      - ./user-service/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - microservice-network

  auth-db:
    image: postgres:15
    environment:
      POSTGRES_DB: authdb
      POSTGRES_USER: authservice
      POSTGRES_PASSWORD: authpass123
    volumes:
      - auth_data:/var/lib/postgresql/data
      - ./auth-service/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - microservice-network

  # Application Services
  user-service:
    build: ./user-service
    depends_on:
      - user-db
    environment:
      DB_HOST: user-db
      DB_PORT: 5432
      DB_NAME: userdb
      DB_USER: userservice
      DB_PASS: userpass123
    networks:
      - microservice-network

  auth-service:
    build: ./auth-service
    depends_on:
      - auth-db
    environment:
      DB_HOST: auth-db
      DB_PORT: 5432
      DB_NAME: authdb
      DB_USER: authservice
      DB_PASS: authpass123
      USER_SERVICE_URL: http://user-service:3001
      JWT_SECRET: your-super-secret-jwt-key-change-in-production
    networks:
      - microservice-network

  frontend:
    build: ./frontend
    depends_on:
      - auth-service
      - user-service
    environment:
      AUTH_SERVICE_URL: http://auth-service:3002
      USER_SERVICE_URL: http://user-service:3001
    networks:
      - microservice-network

  # Gateway
  nginx:
    build: ./nginx
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - auth-service
      - user-service
    networks:
      - microservice-network

networks:
  microservice-network:
    driver: bridge

volumes:
  user_data:
  auth_data:
```

### Container Dependencies
```
nginx → frontend, auth-service, user-service
frontend → auth-service, user-service
auth-service → auth-db, user-service
user-service → user-db
```

---

## 📚 API Documentation

### Authentication Service APIs

#### POST /login
```json
Request:
{
  "username": "string",
  "password": "string"
}

Response (200):
{
  "token": "jwt-token-string",
  "user": {
    "id": 1,
    "username": "testuser",
    "firstname": "Test",
    "lastname": "User"
  }
}

Response (401):
{
  "error": "Invalid credentials"
}
```

#### POST /verify
```json
Headers:
Authorization: Bearer <jwt-token>

Response (200):
{
  "valid": true,
  "user": {
    "id": 1,
    "username": "testuser",
    "firstname": "Test",
    "lastname": "User"
  }
}

Response (401):
{
  "error": "Invalid token"
}
```

### User Service APIs

#### GET /users
```json
Query Parameters:
- page: number (default: 1)
- limit: number (default: 10)
- search: string (optional)

Response (200):
{
  "users": [
    {
      "id": 1,
      "username": "testuser",
      "firstname": "Test",
      "lastname": "User",
      "created_at": "2025-08-25T08:11:17.803Z"
    }
  ],
  "pagination": {
    "currentPage": 1,
    "totalPages": 1,
    "totalUsers": 1,
    "hasNext": false,
    "hasPrev": false
  }
}
```

#### POST /register
```json
Request:
{
  "username": "string",
  "firstname": "string",
  "lastname": "string",
  "password": "string"
}

Response (201):
{
  "id": 2,
  "username": "newuser",
  "firstname": "New",
  "lastname": "User",
  "created_at": "2025-08-25T08:20:00.000Z"
}

Response (409):
{
  "error": "Username already exists"
}
```

#### GET /users/id/:id
```json
Response (200):
{
  "id": 1,
  "username": "testuser",
  "firstname": "Test",
  "lastname": "User",
  "created_at": "2025-08-25T08:11:17.803Z"
}

Response (404):
{
  "error": "User not found"
}
```

#### PUT /users/:id
```json
Request:
{
  "username": "string",
  "firstname": "string",
  "lastname": "string"
}

Response (200):
{
  "id": 1,
  "username": "updateduser",
  "firstname": "Updated",
  "lastname": "User",
  "created_at": "2025-08-25T08:11:17.803Z"
}
```

#### DELETE /users/:id
```json
Response (200):
{
  "message": "User deleted successfully",
  "user": {
    "id": 1,
    "username": "deleteduser",
    "firstname": "Deleted",
    "lastname": "User"
  }
}
```

### Frontend Proxy APIs

All frontend APIs are proxies to backend services:
- `/api/login` → `auth-service/login`
- `/api/verify` → `auth-service/verify`
- `/api/register` → `user-service/register`
- `/api/users` → `user-service/users`
- `/api/users/:id` → `user-service/users/:id`

---

## 🛠️ Service Template

This section provides a template for adding new services to the system.

### Directory Structure Template
```
new-service/
├── server.js              # Main application file
├── package.json           # Node.js dependencies
├── Dockerfile             # Container configuration
├── init.sql              # Database initialization (if needed)
├── .dockerignore         # Docker ignore file
└── README.md             # Service documentation
```

### server.js Template
```javascript
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 3003; // Use next available port

// Middleware
app.use(cors());
app.use(express.json());

// Database connection (if needed)
const pool = new Pool({
  host: process.env.DB_HOST || 'new-service-db',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'newservicedb',
  user: process.env.DB_USER || 'newservice',
  password: process.env.DB_PASS || 'newservicepass123',
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'new-service',
    timestamp: new Date().toISOString()
  });
});

// Your service endpoints here
app.get('/api/endpoint', async (req, res) => {
  try {
    // Your business logic here
    res.json({ message: 'New service endpoint' });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
app.listen(port, () => {
  console.log(`New service running on port ${port}`);
});
```

### package.json Template
```json
{
  "name": "new-service",
  "version": "1.0.0",
  "description": "New microservice",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "pg": "^8.11.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.22"
  }
}
```

### Dockerfile Template
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3003

CMD ["npm", "start"]
```

### init.sql Template (if database needed)
```sql
-- New Service Database Schema
CREATE TABLE IF NOT EXISTS new_service_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_new_service_data_name ON new_service_data(name);
CREATE INDEX IF NOT EXISTS idx_new_service_data_created_at ON new_service_data(created_at);

-- Sample data
INSERT INTO new_service_data (name, description) VALUES 
('Sample Item', 'This is a sample item for the new service');
```

---

## ➕ Adding New Services

### Step-by-Step Guide

#### 1. Create Service Directory
```bash
mkdir new-service
cd new-service
```

#### 2. Create Service Files
Use the templates above to create:
- `server.js`
- `package.json`
- `Dockerfile`
- `init.sql` (if database needed)

#### 3. Update Docker Compose
Add to `docker-compose.yml`:

```yaml
# Add database (if needed)
new-service-db:
  image: postgres:15
  environment:
    POSTGRES_DB: newservicedb
    POSTGRES_USER: newservice
    POSTGRES_PASSWORD: newservicepass123
  volumes:
    - new_service_data:/var/lib/postgresql/data
    - ./new-service/init.sql:/docker-entrypoint-initdb.d/init.sql
  networks:
    - microservice-network

# Add service
new-service:
  build: ./new-service
  depends_on:
    - new-service-db  # if database needed
  environment:
    DB_HOST: new-service-db
    DB_PORT: 5432
    DB_NAME: newservicedb
    DB_USER: newservice
    DB_PASS: newservicepass123
    # Add other environment variables as needed
  networks:
    - microservice-network

# Add volume (if database needed)
volumes:
  new_service_data:
```

#### 4. Update Nginx Configuration
Add to `nginx/nginx.conf`:

```nginx
# Add upstream
upstream new-service {
    server new-service:3003;
}

# Add location block in server section
location /api/new-service/ {
    proxy_pass http://new-service/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

#### 5. Update Frontend Service (if needed)
Add proxy endpoints to `frontend/server.js`:

```javascript
// New service proxy endpoints
app.get('/api/new-service/*', async (req, res) => {
  try {
    const path = req.path.replace('/api/new-service', '');
    const response = await axios.get(`${NEW_SERVICE_URL}${path}`, {
      params: req.query,
      headers: {
        'Authorization': req.headers.authorization
      }
    });
    res.json(response.data);
  } catch (error) {
    if (error.response) {
      res.status(error.response.status).json(error.response.data);
    } else {
      console.error('New service proxy error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});
```

#### 6. Add Environment Variables
Update frontend service environment in `docker-compose.yml`:

```yaml
frontend:
  environment:
    NEW_SERVICE_URL: http://new-service:3003
```

#### 7. Create Service Tests
Create `test-new-service.sh`:

```bash
#!/bin/bash
echo "🧪 Testing New Service"
echo "====================="

# Test health endpoint
curl -k -s https://localhost/api/new-service/health

# Add more tests as needed
```

#### 8. Update Documentation
- Add service to architecture diagrams
- Document new APIs
- Update communication matrix
- Add to service specifications

#### 9. Deploy and Test
```bash
# Build and start services
sudo docker compose up --build -d

# Test the new service
./test-new-service.sh

# Check logs
sudo docker compose logs new-service
```

### Service Integration Checklist

- [ ] Service directory created with all template files
- [ ] Database added to docker-compose.yml (if needed)
- [ ] Service added to docker-compose.yml
- [ ] Nginx configuration updated with routing
- [ ] Frontend proxy endpoints added (if needed)
- [ ] Environment variables configured
- [ ] Health check endpoint implemented
- [ ] Error handling implemented
- [ ] Authentication integration (if needed)
- [ ] Tests created and passing
- [ ] Documentation updated
- [ ] Service deployed and verified

### Communication Patterns for New Services

#### Service-to-Service Communication
```javascript
// Example: New service calling user service
const axios = require('axios');

async function getUserInfo(userId, authToken) {
  try {
    const response = await axios.get(`${USER_SERVICE_URL}/users/id/${userId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user info:', error);
    throw error;
  }
}
```

#### Authentication Integration
```javascript
// Middleware for JWT validation
async function validateToken(req, res, next) {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }

    // Verify token with auth service
    const response = await axios.post(`${AUTH_SERVICE_URL}/verify`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    req.user = response.data.user;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid token' });
  }
}

// Use middleware
app.get('/protected-endpoint', validateToken, (req, res) => {
  res.json({ message: 'Protected data', user: req.user });
});
```

---

## 📈 Monitoring and Observability

### Health Checks
Each service should implement:
```javascript
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'service-name',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: process.env.npm_package_version || '1.0.0'
  });
});
```

### Logging Standards
```javascript
// Structured logging
const log = {
  info: (message, data = {}) => {
    console.log(JSON.stringify({
      level: 'info',
      message,
      timestamp: new Date().toISOString(),
      service: 'service-name',
      ...data
    }));
  },
  error: (message, error = {}) => {
    console.error(JSON.stringify({
      level: 'error',
      message,
      timestamp: new Date().toISOString(),
      service: 'service-name',
      error: error.message || error,
      stack: error.stack
    }));
  }
};
```

### Metrics Collection
Consider adding:
- Request/response times
- Error rates
- Database connection pool status
- Memory and CPU usage
- Custom business metrics

---

## 🔧 Development Guidelines

### Code Standards
- Use consistent error handling patterns
- Implement proper input validation
- Follow RESTful API conventions
- Use environment variables for configuration
- Implement graceful shutdown handling

### Testing Strategy
- Unit tests for business logic
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Database migration tests
- Performance tests for critical paths

### Security Best Practices
- Never log sensitive data (passwords, tokens)
- Validate all inputs
- Use parameterized queries
- Implement rate limiting
- Keep dependencies updated

---

This documentation provides a complete blueprint for understanding and extending the microservice architecture. Use it as a reference when adding new services or modifying existing ones.