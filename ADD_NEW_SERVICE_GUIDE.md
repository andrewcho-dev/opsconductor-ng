# 🚀 Adding New Services Guide

## 📋 Quick Start Checklist

Follow this step-by-step guide to add a new service to the microservice system.

### ✅ Prerequisites
- [ ] Docker and Docker Compose installed
- [ ] Basic understanding of Node.js and Express
- [ ] PostgreSQL knowledge (if database needed)
- [ ] Understanding of JWT authentication

---

## 🛠️ Step-by-Step Implementation

### Step 1: Copy Service Template
```bash
# Navigate to the microservice system directory
cd /path/to/microservice-system

# Copy the service template
cp -r service-template your-new-service

# Navigate to your new service
cd your-new-service
```

### Step 2: Customize Service Files

#### 2.1 Update `package.json`
```json
{
  "name": "your-new-service",
  "description": "Description of your new service",
  "author": "Your Name"
}
```

#### 2.2 Update `server.js`
Replace all instances of:
- `new-service` → `your-new-service`
- `3003` → `your-port-number` (use next available port)
- Modify endpoints based on your business logic

#### 2.3 Update `init.sql`
- Modify database schema for your service needs
- Update table names and structure
- Add your specific indexes and constraints

#### 2.4 Update `Dockerfile`
- Change the EXPOSE port if needed
- Modify health check URL if needed

#### 2.5 Update `README.md`
- Replace service description
- Update API documentation
- Add your specific environment variables

### Step 3: Add to Docker Compose

Edit `docker-compose.yml` and add your service:

```yaml
# Add database (if needed)
your-new-service-db:
  image: postgres:15
  environment:
    POSTGRES_DB: yournewservicedb
    POSTGRES_USER: yournewservice
    POSTGRES_PASSWORD: yournewservicepass123
  volumes:
    - your_new_service_data:/var/lib/postgresql/data
    - ./your-new-service/init.sql:/docker-entrypoint-initdb.d/init.sql
  networks:
    - microservice-network

# Add service
your-new-service:
  build: ./your-new-service
  depends_on:
    - your-new-service-db  # if database needed
  environment:
    PORT: 3004  # use next available port
    DB_HOST: your-new-service-db
    DB_PORT: 5432
    DB_NAME: yournewservicedb
    DB_USER: yournewservice
    DB_PASS: yournewservicepass123
    AUTH_SERVICE_URL: http://auth-service:3002
    USER_SERVICE_URL: http://user-service:3001
  networks:
    - microservice-network

# Add volume (if database needed)
volumes:
  your_new_service_data:
```

### Step 4: Update Nginx Configuration

Edit `nginx/nginx.conf` and add:

```nginx
# Add upstream
upstream your-new-service {
    server your-new-service:3004;  # use your port
}

# Add location block in server section
location /api/your-new-service/ {
    proxy_pass http://your-new-service/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Step 5: Update Frontend Service (Optional)

If you need frontend integration, edit `frontend/server.js`:

```javascript
// Add service URL
const YOUR_NEW_SERVICE_URL = process.env.YOUR_NEW_SERVICE_URL || 'http://your-new-service:3004';

// Add proxy endpoints
app.get('/api/your-new-service/*', async (req, res) => {
  try {
    const path = req.path.replace('/api/your-new-service', '');
    const response = await axios.get(`${YOUR_NEW_SERVICE_URL}${path}`, {
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
      console.error('Service proxy error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

// Add POST, PUT, DELETE proxies as needed
```

Update frontend environment in `docker-compose.yml`:
```yaml
frontend:
  environment:
    YOUR_NEW_SERVICE_URL: http://your-new-service:3004
```

### Step 6: Create Test Script

Copy and customize the test script:
```bash
cp service-template/test-service.sh test-your-new-service.sh
chmod +x test-your-new-service.sh

# Edit the script and update:
# - SERVICE_NAME="your-new-service"
# - Test endpoints specific to your service
```

### Step 7: Build and Deploy

```bash
# Build and start all services
sudo docker compose up --build -d

# Check if your service is running
sudo docker compose ps

# Check logs
sudo docker compose logs -f your-new-service

# Test your service
./test-your-new-service.sh
```

---

## 🎯 Service Development Patterns

### 1. Database Service Pattern
For services that need persistent data storage:

```javascript
// Database connection with connection pooling
const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASS,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// CRUD operations
app.get('/items', validateToken, async (req, res) => {
  const result = await pool.query('SELECT * FROM items WHERE user_id = $1', [req.user.id]);
  res.json(result.rows);
});
```

### 2. Stateless Service Pattern
For services that don't need a database:

```javascript
// Remove database-related code
// Focus on business logic and external API calls

app.get('/calculate', validateToken, (req, res) => {
  const { value1, value2 } = req.query;
  const result = performCalculation(value1, value2);
  res.json({ result });
});
```

### 3. Integration Service Pattern
For services that integrate with external APIs:

```javascript
const axios = require('axios');

app.get('/external-data', validateToken, async (req, res) => {
  try {
    const response = await axios.get('https://external-api.com/data', {
      headers: { 'API-Key': process.env.EXTERNAL_API_KEY }
    });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'External service unavailable' });
  }
});
```

---

## 🔧 Common Customizations

### Authentication Variations

#### Optional Authentication
```javascript
// Middleware that allows both authenticated and anonymous access
async function optionalAuth(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (token) {
    try {
      const response = await axios.post(`${AUTH_SERVICE_URL}/verify`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      req.user = response.data.user;
    } catch (error) {
      // Continue without user info
    }
  }
  next();
}
```

#### Role-Based Access
```javascript
function requireRole(role) {
  return async (req, res, next) => {
    await validateToken(req, res, () => {});
    if (!req.user.roles || !req.user.roles.includes(role)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
  };
}

app.get('/admin-only', requireRole('admin'), (req, res) => {
  res.json({ message: 'Admin access granted' });
});
```

### Database Patterns

#### Soft Delete
```sql
ALTER TABLE your_table ADD COLUMN deleted_at TIMESTAMP NULL;
CREATE INDEX idx_your_table_deleted_at ON your_table(deleted_at);
```

```javascript
// Soft delete implementation
app.delete('/items/:id', validateToken, async (req, res) => {
  await pool.query(
    'UPDATE items SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND user_id = $2',
    [req.params.id, req.user.id]
  );
  res.json({ message: 'Item deleted' });
});

// Filter out deleted items in queries
app.get('/items', validateToken, async (req, res) => {
  const result = await pool.query(
    'SELECT * FROM items WHERE user_id = $1 AND deleted_at IS NULL',
    [req.user.id]
  );
  res.json(result.rows);
});
```

#### Audit Trail
```javascript
async function logAudit(tableName, recordId, action, oldValues, newValues, userId) {
  await pool.query(
    'INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, user_id) VALUES ($1, $2, $3, $4, $5, $6)',
    [tableName, recordId, action, JSON.stringify(oldValues), JSON.stringify(newValues), userId]
  );
}
```

### Error Handling Patterns

#### Custom Error Classes
```javascript
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    this.statusCode = 400;
  }
}

class NotFoundError extends Error {
  constructor(resource) {
    super(`${resource} not found`);
    this.name = 'NotFoundError';
    this.statusCode = 404;
  }
}

// Error handling middleware
app.use((error, req, res, next) => {
  if (error.statusCode) {
    res.status(error.statusCode).json({ 
      error: error.message,
      field: error.field 
    });
  } else {
    log.error('Unhandled error', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

---

## 📊 Monitoring and Observability

### Health Check Enhancements
```javascript
app.get('/health', async (req, res) => {
  const health = {
    status: 'healthy',
    service: 'your-service',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: process.env.npm_package_version || '1.0.0'
  };

  // Check database connectivity
  if (pool) {
    try {
      await pool.query('SELECT 1');
      health.database = 'healthy';
    } catch (error) {
      health.database = 'unhealthy';
      health.status = 'degraded';
    }
  }

  // Check external dependencies
  try {
    await axios.get(`${AUTH_SERVICE_URL}/health`, { timeout: 5000 });
    health.authService = 'healthy';
  } catch (error) {
    health.authService = 'unhealthy';
    health.status = 'degraded';
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
});
```

### Metrics Collection
```javascript
let requestCount = 0;
let errorCount = 0;

// Metrics middleware
app.use((req, res, next) => {
  requestCount++;
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    if (res.statusCode >= 400) errorCount++;
    
    log.info('Request completed', {
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration,
      userAgent: req.get('User-Agent')
    });
  });
  
  next();
});

// Metrics endpoint
app.get('/metrics', (req, res) => {
  res.json({
    requests: requestCount,
    errors: errorCount,
    errorRate: requestCount > 0 ? (errorCount / requestCount) * 100 : 0,
    uptime: process.uptime(),
    memory: process.memoryUsage()
  });
});
```

---

## 🧪 Testing Strategies

### Unit Tests
```javascript
// tests/service.test.js
const request = require('supertest');
const app = require('../server');

describe('Service Endpoints', () => {
  test('GET /health should return 200', async () => {
    const response = await request(app).get('/health');
    expect(response.status).toBe(200);
    expect(response.body.status).toBe('healthy');
  });

  test('GET /info should return service information', async () => {
    const response = await request(app).get('/info');
    expect(response.status).toBe(200);
    expect(response.body.service).toBe('your-service');
  });
});
```

### Integration Tests
```javascript
describe('Integration Tests', () => {
  let authToken;

  beforeAll(async () => {
    // Get auth token for tests
    const loginResponse = await request(app)
      .post('/api/login')
      .send({ username: 'testuser', password: 'testpass123' });
    authToken = loginResponse.body.token;
  });

  test('Protected endpoint should require authentication', async () => {
    const response = await request(app).get('/data');
    expect(response.status).toBe(401);
  });

  test('Protected endpoint should work with valid token', async () => {
    const response = await request(app)
      .get('/data')
      .set('Authorization', `Bearer ${authToken}`);
    expect(response.status).toBe(200);
  });
});
```

---

## 🚀 Deployment Best Practices

### Environment Configuration
```bash
# .env.example
PORT=3004
DB_HOST=your-new-service-db
DB_PORT=5432
DB_NAME=yournewservicedb
DB_USER=yournewservice
DB_PASS=yournewservicepass123
AUTH_SERVICE_URL=http://auth-service:3002
USER_SERVICE_URL=http://user-service:3001
LOG_LEVEL=info
NODE_ENV=production
```

### Production Considerations
1. **Security**: Use strong passwords and secrets
2. **Logging**: Implement structured logging
3. **Monitoring**: Add health checks and metrics
4. **Scaling**: Design for horizontal scaling
5. **Backup**: Implement database backup strategies
6. **SSL**: Use proper SSL certificates in production

### Performance Optimization
```javascript
// Connection pooling
const pool = new Pool({
  max: 20,                    // Maximum connections
  idleTimeoutMillis: 30000,   // Close idle connections
  connectionTimeoutMillis: 2000, // Connection timeout
});

// Request caching (if applicable)
const cache = new Map();
app.get('/cached-data', (req, res) => {
  const cacheKey = `data-${req.user.id}`;
  if (cache.has(cacheKey)) {
    return res.json(cache.get(cacheKey));
  }
  
  // Fetch data and cache it
  const data = fetchData();
  cache.set(cacheKey, data);
  setTimeout(() => cache.delete(cacheKey), 300000); // 5 min cache
  res.json(data);
});
```

---

## 📚 Additional Resources

### Documentation Templates
- API documentation with OpenAPI/Swagger
- Database schema documentation
- Deployment guides
- Troubleshooting guides

### Useful Libraries
- **Validation**: `joi`, `express-validator`
- **Testing**: `jest`, `supertest`, `nock`
- **Monitoring**: `prom-client`, `winston`
- **Security**: `helmet`, `rate-limiter-flexible`
- **Caching**: `redis`, `node-cache`

### Common Patterns
- Repository pattern for data access
- Service layer for business logic
- Middleware for cross-cutting concerns
- Event-driven architecture with message queues

---

## 🎯 Success Criteria

Your new service is successfully integrated when:

- [ ] Service starts without errors
- [ ] Health check endpoint returns 200
- [ ] Database connections work (if applicable)
- [ ] Authentication integration works
- [ ] Service is accessible through nginx gateway
- [ ] All tests pass
- [ ] Service can communicate with other services
- [ ] Logging is working properly
- [ ] Documentation is updated

---

## 🆘 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
sudo docker compose logs your-new-service

# Common causes:
# - Port conflicts
# - Database connection issues
# - Missing environment variables
# - Syntax errors in code
```

#### Database Connection Issues
```bash
# Check if database is running
sudo docker compose ps

# Check database logs
sudo docker compose logs your-new-service-db

# Test connection manually
sudo docker compose exec your-new-service-db psql -U yournewservice -d yournewservicedb
```

#### Authentication Issues
```bash
# Verify auth service is running
curl -k https://localhost/api/auth/health

# Check token format
echo "YOUR_TOKEN" | base64 -d

# Verify service can reach auth service
sudo docker compose exec your-new-service curl http://auth-service:3002/health
```

#### Nginx Routing Issues
```bash
# Check nginx configuration
sudo docker compose exec nginx nginx -t

# Reload nginx configuration
sudo docker compose restart nginx

# Check nginx logs
sudo docker compose logs nginx
```

---

This guide provides everything you need to successfully add new services to the microservice system. Follow the steps carefully and refer to the troubleshooting section if you encounter issues.